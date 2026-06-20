""" AFP PTX Record (Presentation Text) -> model elements.

Walks the PTOCA control-sequence stream of a PTX record and emits TextElements (and
rule LineElements) into the current model page. Inline/baseline positions are tracked
in AFP L-units and converted to points using the page resolution captured from the
Page Descriptor (PGD); see units.afp_to_points.
"""

import logging

import fontmetrics
from afp.ptoca.afp_ptx_trn_seq import AFP_PTX_TRN
from afp.ptoca.afp_ptx_ami_seq import AFP_PTX_AMI
from afp.ptoca.afp_ptx_amb_seq import AFP_PTX_AMB
from afp.ptoca.afp_ptx_rmi_seq import AFP_PTX_RMI
from afp.ptoca.afp_ptx_rmb_seq import AFP_PTX_RMB
from stream_function_afp import StreamFunctionAFP
from model.element import LineElement, SourceRef, TextElement
from model.geometry import Color, Point, Rect
from units import POINTS_PER_INCH

logger = logging.getLogger(__name__)

# Nominal text height (points) used for bbox estimation until font metrics are wired.
_DEFAULT_TEXT_SIZE = 10.0


class AFP_PTX:
    """ Presentation Text record: a stream of PTOCA control sequences. """

    def __init__(self, segment):
        self.segment = segment
        self.document = self.segment.cur_document
        self.page = self.segment.cur_page
        # Position state, in AFP L-units relative to the page/text-object origin.
        self.cur_x = 0
        self.cur_y = 0
        self.active_font = None
        self.active_color = None
        self.active_orientation = 0

    # -- helpers ----------------------------------------------------------

    def _res(self):
        attrs = self.page.attributes if self.page else {}
        return attrs.get("res_x", 1440.0), attrs.get("res_y", 1440.0)

    def _pt(self, lunits, axis="x"):
        res_x, res_y = self._res()
        res = res_x if axis == "x" else res_y
        return lunits / res * POINTS_PER_INCH

    def _source_ref(self):
        return SourceRef(file_format="afp", record_type="PTX",
                         record_number=self.segment.cur_rec_number,
                         byte_offset=self.segment.cur_rec_offset,
                         length=self.segment.cur_rec_length)

    # -- parse ------------------------------------------------------------

    def parse(self, data):
        """ Parse PTOCA control sequences into model elements. """
        if self.page is None:
            return
        import stream_afp        # lazy: avoids a stream_afp <-> record-module import cycle
        start = 0
        length = len(data)
        while start < length:
            cur_function = StreamFunctionAFP()
            if data[start:start + 1] == b"\x2B":
                # PTOCA introducer escape (0x2B 0xD3) for the unchained form.
                cur_function.length = 2
                cur_function.type = "ESC"
                start += cur_function.length
                continue
            cur_function.length = data[start]
            func = stream_afp.afp_ptx_by_value.get(data[start + 1:start + 2])
            if func is None:
                start += max(cur_function.length, 1)
                continue
            cur_function.type = func["type"]
            seq_data = data[start + 2:start + cur_function.length]
            self._handle(cur_function.type, seq_data)
            start += max(cur_function.length, 1)

    def _handle(self, ftype, seq_data):
        base = ftype.split("-")[0]       # strip the "-C" chained suffix
        if base == "TRN":
            self._emit_text(seq_data)
        elif base == "AMI":
            seq = AFP_PTX_AMI(self.segment); seq.parse(seq_data)
            self.cur_x = seq.DSPLCMNT[0]
        elif base == "AMB":
            seq = AFP_PTX_AMB(self.segment); seq.parse(seq_data)
            self.cur_y = seq.DSPLCMNT[0]
        elif base == "RMI":
            seq = AFP_PTX_RMI(self.segment); seq.parse(seq_data)
            self.cur_x += seq.INCRMENT[0]
        elif base == "RMB":
            seq = AFP_PTX_RMB(self.segment); seq.parse(seq_data)
            self.cur_y += seq.INCRMENT[0]
        elif base == "SCF":
            # Set Coded Font Local: 1-byte local font id.
            if seq_data:
                self.active_font = f"F{seq_data[0]:02X}"
        elif base == "STO":
            # Set Text Orientation: inline rotation (2 bytes) as degrees*128.
            if len(seq_data) >= 2:
                self.active_orientation = int(round(
                    int.from_bytes(seq_data[0:2], "big") / 128.0)) % 360
        elif base == "STC":
            self.active_color = _stc_color(seq_data)
        elif base == "SEC":
            self.active_color = _sec_color(seq_data)
        elif base in ("DBR", "DIR"):
            self._emit_rule(base, seq_data)
        # Remaining sequences (SIM/SIA/SVI/BSU/ESU/...) adjust state we do not yet
        # render; they are intentionally skipped but never abort the stream.

    def _emit_text(self, seq_data):
        font = self.segment.objects.font(self.active_font) if self.active_font else None
        text = font.decode(seq_data) if font else seq_data.decode("latin-1", "replace")
        size = (font.size if font and font.size else None) or _DEFAULT_TEXT_SIZE
        # Precise run width from font metrics + the characters displayed (R11).
        width = fontmetrics.text_width(text, size, font)
        x_pt = self._pt(self.cur_x, "x")
        y_pt = self._pt(self.cur_y, "y")
        element = TextElement(
            text=text,
            position=Point(x_pt, y_pt),
            font_ref=self.active_font,
            font_size=size,
            color=self.active_color,
            orientation=self.active_orientation,
            raw_text_bytes=seq_data,
            bbox=Rect(x_pt, y_pt - size, width, size),
            source_ref=self._source_ref(),
        )
        # Per-character advances (points) for precise sub-run window extraction.
        element.attributes["char_advances"] = fontmetrics.char_advances(text, size, font)
        self.page.add_element(element)
        # Advance the inline cursor past the printed text using the true width.
        self.cur_x += int(width / POINTS_PER_INCH * self._res()[0])

    def _emit_rule(self, base, seq_data):
        # DBR/DIR: Rule Length (2, signed) [+ Rule Width (2)]. DBR draws along the
        # baseline (horizontal); DIR draws along the inline (vertical).
        if len(seq_data) < 2:
            return
        rule_len = int.from_bytes(seq_data[0:2], "big", signed=True)
        x_pt = self._pt(self.cur_x, "x")
        y_pt = self._pt(self.cur_y, "y")
        if base == "DBR":
            end = Point(x_pt + self._pt(rule_len, "x"), y_pt)
        else:
            end = Point(x_pt, y_pt + self._pt(rule_len, "y"))
        self.page.add_element(LineElement(
            start=Point(x_pt, y_pt), end=end, weight=1.0,
            bbox=Rect.from_corners(x_pt, y_pt, end.x, end.y),
            source_ref=self._source_ref(),
        ))


# PTOCA Set Text Color (STC) named-colour palette -> RGB.
_STC_COLORS = {
    0x0000: (0.0, 0.0, 0.0), 0x0001: (0.0, 0.0, 1.0), 0x0002: (1.0, 0.0, 0.0),
    0x0003: (1.0, 0.0, 1.0), 0x0004: (0.0, 1.0, 0.0), 0x0005: (0.0, 1.0, 1.0),
    0x0006: (1.0, 1.0, 0.0), 0x0007: (1.0, 1.0, 1.0), 0x0008: (0.0, 0.0, 0.0),
    0xFF05: (0.0, 0.0, 0.0), 0xFF06: (0.0, 0.0, 0.0), 0xFF07: (0.0, 0.0, 0.0),
    0xFF08: (0.0, 0.0, 0.0),
}


def _stc_color(seq_data):
    """ Set Text Color: a 2-byte (or 1-byte) named colour value. """
    if not seq_data:
        return None
    val = int.from_bytes(seq_data[0:2], "big") if len(seq_data) >= 2 else seq_data[0]
    rgb = _STC_COLORS.get(val)
    return Color.rgb(*rgb) if rgb else None


def _sec_color(seq_data):
    """ Set Extended Text Color: colour space (byte 1) + channel values. Handles RGB,
    CMYK and gray; falls back to None for unknown spaces. """
    if len(seq_data) < 8:
        return None
    space = seq_data[1]
    val = seq_data[8:]
    if space == 0x01 and len(val) >= 3:
        return Color.rgb(val[0] / 255.0, val[1] / 255.0, val[2] / 255.0)
    if space == 0x04 and len(val) >= 4:
        return Color.cmyk(val[0] / 255.0, val[1] / 255.0, val[2] / 255.0, val[3] / 255.0)
    if space == 0x08 and len(val) >= 1:
        return Color.gray(val[0] / 255.0)
    return None
