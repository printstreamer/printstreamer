""" AFP object-area, image (IOCA), graphic (GOCA), barcode (BCOCA), and coded-font
(MCF) parsing, centralized so individual record classes stay thin delegates.

An ``AfpObjectContext`` lives on each AFP segment. Records call into it as they are
dispatched; it accumulates object state and emits model elements/resources with the
correct window (x,y origin + width/height) onto the current page.
"""

from __future__ import annotations

import logging
from struct import unpack

from model.element import (BarcodeElement, ContainerElement, DrawOp,
                           GraphicElement, ImageElement, OverlayElement, SourceRef)
from model.geometry import Point, Rect
from model.resource import FontResource, ImageResource
from units import POINTS_PER_INCH

logger = logging.getLogger(__name__)


def _sint(b):
    return int.from_bytes(b, "big", signed=True)


def _uint(b):
    return int.from_bytes(b, "big", signed=False)


class AfpObjectContext:
    """ Tracks the in-progress object (image/graphic/barcode) for one segment. """

    def __init__(self, segment):
        self.segment = segment
        self.obj = None                  # dict describing the current object
        self.fonts = {}                  # local font name -> FontResource

    # -- geometry helpers -------------------------------------------------

    def _res(self):
        attrs = self.segment.cur_page.attributes if self.segment.cur_page else {}
        return attrs.get("res_x", 1440.0), attrs.get("res_y", 1440.0)

    def _pt_x(self, lunits):
        return lunits / self._res()[0] * POINTS_PER_INCH

    def _pt_y(self, lunits):
        return lunits / self._res()[1] * POINTS_PER_INCH

    def _source_ref(self, record_type):
        return SourceRef(file_format="afp", record_type=record_type,
                         record_number=self.segment.cur_rec_number,
                         byte_offset=self.segment.cur_rec_offset,
                         length=self.segment.cur_rec_length)

    # -- object lifecycle -------------------------------------------------

    def begin_object(self, kind, name, record_type):
        self.obj = {
            "kind": kind,                # "image" | "graphic" | "barcode"
            "name": name,
            "origin": (0, 0),            # L-units (XoaOset, YoaOset)
            "extent": None,              # (w_pt, h_pt) if known
            "data": bytearray(),
            "encoding": None,
            "descriptor": {},
            "record_type": record_type,
            "offset": self.segment.cur_rec_offset,
        }

    def set_object_position(self, data):
        """ Object Area Position (OBP): capture the object-area origin. """
        if self.obj is None or len(data) < 8:
            return
        x = _sint(data[2:5])
        y = _sint(data[5:8])
        self.obj["origin"] = (x, y)

    def add_object_data(self, data):
        """ Append content bytes to the current object (e.g. GOCA drawing orders). """
        if self.obj is not None:
            self.obj["data"] += data

    def set_object_descriptor(self, data):
        """ Object Area Descriptor (OBD): capture extent from the size triplet. """
        if self.obj is None:
            return
        size = _find_triplet(data, 0x4C)     # Object Area Size triplet
        if size and len(size) >= 7:
            # size: UnitBase(1) Xext(3) Yext(3)
            x_ext = _uint(size[1:4])
            y_ext = _uint(size[4:7])
            self.obj["descriptor"]["area_extent"] = (x_ext, y_ext)

    def end_object(self):
        if self.obj is None:
            return
        page = self.segment.cur_page
        if page is None:
            self.obj = None
            return
        bbox = self._object_bbox()
        if self.obj["kind"] == "image":
            self._emit_image(page, bbox)
        elif self.obj["kind"] == "graphic":
            self._emit_graphic(page, bbox)
        elif self.obj["kind"] == "barcode":
            self._emit_barcode(page, bbox)
        self.obj = None

    def _object_bbox(self):
        ox, oy = self.obj["origin"]
        x_pt, y_pt = self._pt_x(ox), self._pt_y(oy)
        desc = self.obj["descriptor"]
        if desc.get("image_extent"):
            w_pt, h_pt = desc["image_extent"]
        elif desc.get("area_extent"):
            w_pt = self._pt_x(desc["area_extent"][0])
            h_pt = self._pt_y(desc["area_extent"][1])
        else:
            w_pt = h_pt = 0.0
        return Rect(x_pt, y_pt, w_pt, h_pt)

    # -- image (IOCA) -----------------------------------------------------

    def set_image_descriptor(self, data):
        """ IDD: image resolution and pixel size -> physical extent in points. """
        if self.obj is None or len(data) < 9:
            return
        unit_base = data[0]
        x_res = _uint(data[1:3]) or 1
        y_res = _uint(data[3:5]) or 1
        x_size = _uint(data[5:7])
        y_size = _uint(data[7:9])
        per_inch_x = x_res / 10.0 if unit_base == 0 else x_res
        per_inch_y = y_res / 10.0 if unit_base == 0 else y_res
        self.obj["descriptor"]["image_extent"] = (
            x_size / per_inch_x * POINTS_PER_INCH,
            y_size / per_inch_y * POINTS_PER_INCH,
        )
        self.obj["descriptor"].update(x_res=x_res, y_res=y_res,
                                      x_size=x_size, y_size=y_size)

    def add_image_data(self, payload, capture):
        """ IPD: accumulate IOCA image content (only when ``capture`` / FULL level). """
        if self.obj is None or not capture:
            return
        compression, content = _parse_ioca(payload)
        if compression is not None:
            self.obj["encoding"] = compression
        self.obj["data"] += content

    def _emit_image(self, page, bbox):
        desc = self.obj["descriptor"]
        resource = None
        if self.obj["data"]:
            resource = ImageResource(
                name=self.obj["name"] or f"IMG{self.obj['offset']}",
                data=bytes(self.obj["data"]),
                image_format=self.obj["encoding"],
                width=desc.get("x_size"), height=desc.get("y_size"),
                colorspace="bilevel",
            )
            self.segment.cur_document.resource_library.add(resource)
        element = ImageElement(
            resource_ref=resource.name if resource else None,
            data=resource.data if resource else None,
            encoding=self.obj["encoding"],
            bbox=bbox,
            source_ref=self._source_ref("BIM"),
        )
        element.attributes["px_width"] = desc.get("x_size")
        element.attributes["px_height"] = desc.get("y_size")
        page.add_element(element)

    def _emit_graphic(self, page, bbox):
        ops = self._parse_goca(bytes(self.obj["data"]), bbox)
        page.add_element(GraphicElement(
            ops=ops, bbox=bbox, raw=bytes(self.obj["data"]) or None,
            source_ref=self._source_ref("BGR"),
        ))

    def _parse_goca(self, data, bbox):
        """ Decode GOCA drawing orders into normalized DrawOps.

        GOCA long-format orders (code >= 0x80) carry a length byte, so unknown ones
        can be skipped without desync; short-format orders are stepped over. Position
        is in GOCA coordinates, scaled into the object area bbox. The common line/box
        primitives are recognized; this is a framework to extend per GOCA variant.
        """
        ops = []
        cur = Point(bbox.x if bbox else 0, bbox.y if bbox else 0)

        def pt(x, y):
            return Point((bbox.x if bbox else 0) + x, (bbox.y if bbox else 0) + y)

        i, n = 0, len(data)
        while i < n:
            code = data[i]; i += 1
            if code >= 0x80:                       # long format: [code][len][operands]
                if i >= n:
                    break
                length = data[i]; i += 1
                operands = data[i:i + length]; i += length
                base = code & 0x7F
                if base == 0x41:                   # GLINE: (x,y) pairs
                    pts = [cur]
                    for k in range(0, len(operands) - 3, 4):
                        x = int.from_bytes(operands[k:k + 2], "big", signed=True)
                        y = int.from_bytes(operands[k + 2:k + 4], "big", signed=True)
                        pts.append(pt(x, y))
                    if len(pts) > 1:
                        ops.append(DrawOp("polyline", pts))
                        cur = pts[-1]
                elif base == 0x40 and len(operands) >= 8:   # GBOX: two corners
                    x1 = int.from_bytes(operands[0:2], "big", signed=True)
                    y1 = int.from_bytes(operands[2:4], "big", signed=True)
                    x2 = int.from_bytes(operands[4:6], "big", signed=True)
                    y2 = int.from_bytes(operands[6:8], "big", signed=True)
                    ops.append(DrawOp("box", [pt(x1, y1), pt(x2, y2)]))
            else:                                  # short format: skip a fixed step
                i += 1
        return ops

    def _emit_barcode(self, page, bbox):
        page.add_element(BarcodeElement(
            symbology=self.obj["descriptor"].get("symbology"),
            data=self.obj["descriptor"].get("data", ""),
            bbox=bbox, raw=bytes(self.obj["data"]) or None,
            source_ref=self._source_ref("BBC"),
        ))

    # -- barcode (BCOCA) --------------------------------------------------

    def set_barcode_descriptor(self, data):
        if self.obj is None or len(data) < 3:
            return
        # BDD: ... Type(1) ... ; capture the symbology type byte for reference.
        self.obj["descriptor"]["symbology"] = f"bcoca-{data[2]:02x}"

    def add_barcode_data(self, data):
        if self.obj is None or len(data) < 3:
            return
        # BDA: flags(1) ... data; keep printable tail as the value.
        self.obj["descriptor"]["data"] = data[3:].decode("latin-1", "replace")

    # -- coded fonts (MCF) ------------------------------------------------

    def map_coded_fonts(self, data):
        """ Parse a Map Coded Font (format 2) record into FontResources. """
        import fontmetrics
        doc = self.segment.cur_document
        for local_id, char_set, code_page in _parse_mcf(data):
            name = f"F{local_id:02X}"
            font = FontResource(name=name, coded_font=char_set, code_page=code_page,
                                char_set=char_set, size=10.0)
            font.typeface = fontmetrics.base_font_for(char_set)
            if doc is not None:
                doc.resource_library.add(font)
            self.fonts[name] = font

    def font(self, name):
        return self.fonts.get(name)

    # -- includes (overlays / page segments / medium maps) ----------------

    def include_overlay(self, data):
        """ Include Page Overlay (IPO) -> OverlayElement placed on the page. """
        page = self.segment.cur_page
        if page is None or len(data) < 8:
            return
        name = data[0:8].decode("cp500", "replace").strip()
        x = _sint(data[8:11]) if len(data) >= 11 else 0
        y = _sint(data[11:14]) if len(data) >= 14 else 0
        page.add_element(OverlayElement(
            resource_ref=name, attributes={"x": self._pt_x(x), "y": self._pt_y(y)},
            bbox=Rect(self._pt_x(x), self._pt_y(y), 0, 0),
            source_ref=self._source_ref("IPO")))

    def include_page_segment(self, data):
        """ Include Page Segment (IPS) -> ContainerElement carrying its placement. """
        page = self.segment.cur_page
        if page is None or len(data) < 8:
            return
        name = data[0:8].decode("cp500", "replace").strip()
        x = _sint(data[8:11]) if len(data) >= 11 else 0
        y = _sint(data[11:14]) if len(data) >= 14 else 0
        page.add_element(ContainerElement(
            preserved_type="page-segment",
            attributes={"name": name, "x": self._pt_x(x), "y": self._pt_y(y)},
            bbox=Rect(self._pt_x(x), self._pt_y(y), 0, 0),
            source_ref=self._source_ref("IPS")))

    def invoke_medium_map(self, data):
        """ Invoke Medium Map (IMM) -> record the map name on the page. """
        page = self.segment.cur_page
        if page is not None and data:
            page.attributes["medium_map"] = data[0:8].decode("cp500", "replace").strip()


# -- structured-field / triplet helpers ------------------------------------

def _find_triplet(data, triplet_id):
    """ Return the data of the first triplet with the given id (or None). """
    i = 0
    while i + 1 < len(data):
        length = data[i]
        if length < 2 or i + length > len(data):
            break
        if data[i + 1] == triplet_id:
            return data[i + 2:i + length]
        i += length
    return None


def _parse_mcf(data):
    """ Yield (local_id, char_set, code_page) from an MCF (format 2) record.

    Each repeating group starts with a 2-byte length and contains triplets:
    Fully Qualified Name (X'02') entries for the character set (X'86') and code
    page (X'85'), and a Resource Local Identifier (X'24') giving the local id.
    """
    i = 0
    while i + 2 <= len(data):
        rg_len = _uint(data[i:i + 2])
        if rg_len < 2 or i + rg_len > len(data):
            break
        group = data[i + 2:i + rg_len]
        char_set = code_page = None
        local_id = None
        j = 0
        while j + 1 < len(group):
            tlen = group[j]
            if tlen < 2 or j + tlen > len(group):
                break
            tid = group[j + 1]
            tdata = group[j + 2:j + tlen]
            if tid == 0x02 and len(tdata) >= 2:        # Fully Qualified Name
                fqn_type = tdata[0]                     # tdata[1] = FQN format byte
                name = tdata[2:].decode("cp500", "replace").strip()
                if fqn_type == 0x86:
                    char_set = name
                elif fqn_type == 0x85:
                    code_page = name
            elif tid == 0x24 and len(tdata) >= 2:      # Resource Local Identifier
                local_id = tdata[1]
            j += tlen
        if local_id is not None:
            yield local_id, char_set, code_page
        i += rg_len


# IOCA self-defining field codes.
_IOCA_LONG = 0xFE
_IOCA_IMAGE_DATA = 0x92
_IOCA_ENCODING = 0x95


def _parse_ioca(payload):
    """ Walk IOCA self-defining fields, returning (compression, image_content). """
    compression = None
    content = bytearray()
    i = 0
    n = len(payload)
    while i < n:
        code = payload[i]
        if code == _IOCA_LONG:                       # long form: FE <code> <len2>
            if i + 4 > n:
                break
            real = payload[i + 1]
            length = _uint(payload[i + 2:i + 4])
            body = payload[i + 4:i + 4 + length]
            if real == _IOCA_IMAGE_DATA:
                content += body
            i += 4 + length
        else:                                        # short form: <code> <len1>
            if i + 2 > n:
                break
            length = payload[i + 1]
            body = payload[i + 2:i + 2 + length]
            if code == _IOCA_ENCODING and body:
                compression = f"ioca-{body[0]:02x}"
            i += 2 + length
    return compression, bytes(content)
