""" Render the generic model back to an AFP (MO:DCA) print stream.

Emits the document/page envelope, text (PTOCA), and objects (IOCA images, BCOCA
barcodes), plus AFP-specific constructs declared in PSML: overlays (IPO), page
segments (IPS), medium maps (IMM), structured-field passthrough, and object
containers. Geometry converts from points to AFP L-units (1440/inch). The output is
structured so this project's AFP reader reconstructs an equivalent model.
"""

import logging

import stream_afp
from model.element import ElementKind
from units import POINTS_PER_INCH

logger = logging.getLogger(__name__)

_RES = 1440.0                     # L-units per inch used for output
_UNITS_PER_10IN = int(_RES * 10)  # PGD XpUnits/YpUnits (unit base 0x00 => per 10in)
_IMG_DPI = 300.0                  # resolution used when re-emitting IOCA images

# PTOCA control-sequence function codes (unchained forms).
_PTX = {"AMB": 0xD2, "AMI": 0xC6, "SCF": 0xF0, "TRN": 0xDA}


def _sf(rec_type, data):
    """ Wrap data as an AFP structured field: 0x5A + length(2) + id(3) + flags(1)
    + sequence(2) + data. The length counts everything after the 0x5A. """
    sfid = stream_afp.afp_rec_type_text[rec_type]["value"]
    length = 8 + len(data)
    return b"\x5a" + length.to_bytes(2, "big") + sfid + b"\x00" + b"\x00\x00" + data


def _pt_to_lunits(points):
    return int(round(points / POINTS_PER_INCH * _RES))


def _name8(value):
    return (value or "").encode("cp500", "replace")[:8].ljust(8, b"\x40")


def _ptx_seq(code, data):
    return bytes([2 + len(data), code]) + data


class AfpWriter:
    """ Write a StreamDocumentSet to an AFP file. """

    def write(self, document_set, path):
        out = bytearray()
        for di, document in enumerate(document_set.documents, start=1):
            name = (document.name or f"DOC{di:05d}").encode("latin-1", "replace")[:8].ljust(8)
            out += _sf("BDT", name)
            for page in document.pages:
                self._write_page(out, page)
            out += _sf("EDT", name)
        with open(path, "wb") as fh:
            fh.write(out)
        logger.info("Wrote AFP %s (%d documents, %d pages)",
                    path, document_set.document_count, document_set.page_count)

    def _write_page(self, out, page):
        pname = str(page.attributes.get("name", "")).encode("latin-1", "replace")[:8].ljust(8)
        out += _sf("BPG", pname)
        out += _sf("PGD", self._pgd_data(page))
        if page.attributes.get("medium_map"):
            out += _sf("IMM", _name8(page.attributes["medium_map"]))
        # Objects first (painted behind), then the text object on top.
        for element in page.ordered_elements():
            self._write_object(out, element)
        ptx = self._ptx_data(page)
        if ptx:
            out += _sf("BPT", b"\x00" * 8)
            out += _sf("PTX", ptx)
            out += _sf("EPT", b"\x00" * 8)
        out += _sf("EPG", b"")

    def _write_object(self, out, el):
        if el.kind == ElementKind.IMAGE:
            self._emit_image(out, el)
        elif el.kind == ElementKind.BARCODE:
            self._emit_barcode(out, el)
        elif el.kind == ElementKind.OVERLAY:
            self._emit_overlay(out, el)
        elif el.kind == ElementKind.CONTAINER:
            self._emit_container(out, el)

    # -- page geometry ----------------------------------------------------

    def _pgd_data(self, page):
        return (bytes([0x00, 0x00])
                + _UNITS_PER_10IN.to_bytes(2, "big")
                + _UNITS_PER_10IN.to_bytes(2, "big")
                + _pt_to_lunits(page.width or 612).to_bytes(3, "big")
                + _pt_to_lunits(page.height or 792).to_bytes(3, "big"))

    # -- text -------------------------------------------------------------

    def _ptx_data(self, page):
        body = bytearray(b"\x2b\xd3")
        active_font = object()
        for element in page.ordered_elements():
            if element.kind != ElementKind.TEXT or not element.text:
                continue
            body += _ptx_seq(_PTX["AMB"], _pt_to_lunits(element.position.y).to_bytes(2, "big", signed=True))
            body += _ptx_seq(_PTX["AMI"], _pt_to_lunits(element.position.x).to_bytes(2, "big", signed=True))
            if element.font_ref and element.font_ref != active_font:
                active_font = element.font_ref
                try:
                    fid = int(str(element.font_ref).lstrip("F"), 16) & 0xFF
                except ValueError:
                    fid = 1
                body += _ptx_seq(_PTX["SCF"], bytes([fid]))
            text_bytes = element.raw_text_bytes or element.text.encode("latin-1", "replace")
            for i in range(0, len(text_bytes), 253):
                body += _ptx_seq(_PTX["TRN"], text_bytes[i:i + 253])
        return bytes(body) if len(body) > 2 else b""

    # -- objects ----------------------------------------------------------

    def _obp(self, bbox):
        x = _pt_to_lunits(bbox.x if bbox else 0)
        y = _pt_to_lunits(bbox.y if bbox else 0)
        return (bytes([0x01, 0x17]) + x.to_bytes(3, "big", signed=True)
                + y.to_bytes(3, "big", signed=True) + b"\x00" * 15)

    # IOCA Image Data chunk size: keep each structured field within MO:DCA limits.
    _IOCA_CHUNK = 30000

    def _emit_image(self, out, el):
        bbox = el.bbox
        out += _sf("BIM", _name8(el.resource_ref))
        out += _sf("OBP", self._obp(bbox))
        x_size = max(1, round((bbox.width if bbox else 72) / POINTS_PER_INCH * _IMG_DPI))
        y_size = max(1, round((bbox.height if bbox else 72) / POINTS_PER_INCH * _IMG_DPI))
        res = int(_IMG_DPI * 10)
        out += _sf("IDD", bytes([0x00]) + res.to_bytes(2, "big") + res.to_bytes(2, "big")
                   + x_size.to_bytes(2, "big") + y_size.to_bytes(2, "big"))
        for ipd in self._ioca_records(el):
            out += _sf("IPD", ipd)
        out += _sf("EIM", _name8(el.resource_ref))

    def _ioca_records(self, el):
        """ Yield IPD payloads carrying the image's IOCA content, chunked to fit
        within structured-field size limits. The first record opens the segment and
        declares the encoding; each carries an Image Data (0xFE92) field. """
        content = el.data or b""
        comp = 0x00
        if el.encoding and el.encoding.startswith("ioca-"):
            try:
                comp = int(el.encoding.split("-")[1], 16)
            except ValueError:
                comp = 0x00
        chunks = [content[i:i + self._IOCA_CHUNK]
                  for i in range(0, max(len(content), 1), self._IOCA_CHUNK)] or [b""]
        for idx, chunk in enumerate(chunks):
            prefix = bytes([0x70, 0x00, 0x95, 0x02, comp, 0x01]) if idx == 0 else b""
            yield prefix + bytes([0xFE, 0x92]) + len(chunk).to_bytes(2, "big") + chunk

    def _emit_barcode(self, out, el):
        name = _name8(getattr(el, "resource_ref", None))
        out += _sf("BBC", name)
        if el.bbox:
            out += _sf("OBP", self._obp(el.bbox))
        sym = 0x00
        if el.symbology and el.symbology.startswith("bcoca-"):
            try:
                sym = int(el.symbology.split("-")[1], 16)
            except ValueError:
                sym = 0x00
        out += _sf("BDD", bytes([0x00, 0x00, sym]) + b"\x00" * 4)
        out += _sf("BDA", b"\x00\x00\x00" + (el.data or "").encode("latin-1", "replace"))
        out += _sf("EBC", name)

    def _emit_overlay(self, out, el):
        x = _pt_to_lunits(el.attributes.get("x", 0))
        y = _pt_to_lunits(el.attributes.get("y", 0))
        out += _sf("IPO", _name8(el.resource_ref) + x.to_bytes(3, "big", signed=True)
                   + y.to_bytes(3, "big", signed=True) + b"\x00\x00")

    def _emit_container(self, out, el):
        kind = (el.attributes or {}).get
        ptype = el.preserved_type
        if ptype == "structured-field" and el.raw:
            out += el.raw                       # verbatim passthrough
        elif ptype == "page-segment":
            x = _pt_to_lunits(kind("x", 0))
            y = _pt_to_lunits(kind("y", 0))
            out += _sf("IPS", _name8(kind("name")) + x.to_bytes(3, "big", signed=True)
                       + y.to_bytes(3, "big", signed=True))
        elif ptype == "object-container":
            out += _sf("BOC", _name8(kind("name")))
            if el.raw:
                out += _sf("OCD", el.raw)
            out += _sf("EOC", _name8(kind("name")))
