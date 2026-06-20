""" Order-driven Metacode parser producing model pages.

The record/order layout assumed by the default ORDERS map:
  * the stream is a sequence of records, each prefixed by a 1-byte length;
  * a record body is a sequence of orders, each an order byte followed by its operands.

Default orders (override via ``order_map`` for a specific Metacode variant):
  SET_Y  (0xC0): 2-byte Y position, in dots
  SET_X  (0xC1): 2-byte X position, in dots
  FONT   (0xC2): 1-byte font index (mapped to a point size via ``font_sizes``)
  TEXT   (0xC3): 1-byte length N, then N text bytes (decoded with ``encoding``)
  ENDPG  (0xFF): end of page

Positions are in dots at ``dpi`` (default 300) and converted to points.
"""

from __future__ import annotations

import logging
import re

import fontmetrics
from model.element import ContainerElement, TextElement
from model.geometry import Color, Point, Rect

logger = logging.getLogger(__name__)

ORDERS = {"SET_Y": 0xC0, "SET_X": 0xC1, "FONT": 0xC2, "TEXT": 0xC3, "ENDPG": 0xFF}


class MetacodeParser:
    """ Parse a Metacode order stream, emitting pages via ``on_page``.

    Pass a :class:`metacode.jsl.JslConfig` (``jsl=``) to drive geometry, fonts,
    encoding, and DJDE recognition from a Job Source Library; without one the standard
    LPS defaults are used. DJDE records (data-stream descriptor entries flagged by the
    JSL's IDEN prefix) are recognized, applied, and preserved.
    """

    def __init__(self, on_page, *, jsl=None, order_map=None, dpi=None, encoding=None,
                 font_sizes=None, page_width=None, page_height=None):
        self.on_page = on_page
        self.jsl = jsl
        self.orders = {**ORDERS, **(order_map or {})}
        self.by_code = {v: k for k, v in self.orders.items()}
        # JSL supplies defaults; explicit kwargs still win.
        dpi = dpi or (jsl.dpi if jsl else 300)
        self.encoding = encoding or (jsl.encoding if jsl else "cp500")
        self.pt_per_dot = 72.0 / dpi
        self.font_sizes = font_sizes or (dict(jsl.font_sizes) if jsl else None) \
            or {0: 10.0, 1: 12.0, 2: 8.0, 3: 14.0}
        self.page_width = page_width or (jsl.page_width if jsl else 612.0)
        self.page_height = page_height or (jsl.page_height if jsl else 792.0)
        # DJDE recognition (from the JSL IDEN statement).
        self.djde_prefix = (jsl.djde_prefix if jsl else "$DJDE$")
        self.djde_skip = (jsl.djde_skip if jsl else 0)
        self.djde_prefix_bytes = self.djde_prefix.encode(self.encoding, "replace")
        self.reset()

    def reset(self):
        self.x = 0.0
        self.y = 0.0
        self.size = 10.0
        self.elements = []
        self._page_open = False

    def parse(self, data: bytes):
        i = 0
        n = len(data)
        while i < n:
            length = data[i]
            i += 1
            self._record(data[i:i + length])
            i += length
        if self._page_open:
            self._finish_page()

    def _is_djde(self, body):
        """ True when this record is a DJDE descriptor (carries the JSL's prefix). """
        window = body[:self.djde_skip + len(self.djde_prefix_bytes) + 8]
        return bool(self.djde_prefix_bytes) and self.djde_prefix_bytes in window

    def _handle_djde(self, body):
        """ Apply a DJDE record's settings and preserve it as a container element.

        DJDEs change formatting mid-stream (font selection, form/format, data span).
        We apply the ones that affect the model (FONTINDEX -> active font size) and keep
        the raw record so transforms/round-trips never drop it.
        """
        text = body.decode(self.encoding, "replace")
        ops = dict(re.findall(r"([A-Za-z][A-Za-z0-9]*)\s*=\s*(\([^)]*\)|[^,();]+)", text))
        fontindex = ops.get("FONTINDEX")
        if fontindex:
            m = re.search(r"-?\d+", fontindex)
            if m:
                self.size = self.font_sizes.get(int(m.group()), self.size)
        self._add(ContainerElement(preserved_type="DJDE", raw=bytes(body),
                                   attributes={"djde": text.strip()}))

    def _record(self, body):
        if self._is_djde(body):
            self._handle_djde(body)
            return
        i = 0
        n = len(body)
        while i < n:
            code = body[i]
            i += 1
            name = self.by_code.get(code)
            if name == "SET_Y":
                self.y = int.from_bytes(body[i:i + 2], "big") * self.pt_per_dot
                i += 2
            elif name == "SET_X":
                self.x = int.from_bytes(body[i:i + 2], "big") * self.pt_per_dot
                i += 2
            elif name == "FONT":
                self.size = self.font_sizes.get(body[i], 10.0)
                i += 1
            elif name == "TEXT":
                length = body[i]
                i += 1
                text = body[i:i + length].decode(self.encoding, "replace")
                i += length
                self._emit(text)
            elif name == "ENDPG":
                self._finish_page()
            else:
                break        # unknown order: stop this record (calibration needed)

    def _emit(self, text):
        if not text:
            return
        base = fontmetrics.base_font("sans")
        width = fontmetrics.width(text, base, self.size)
        self._add(TextElement(
            text=text, position=Point(self.x, self.y + self.size),
            font_size=self.size, color=Color.rgb(0, 0, 0), font_ref=base,
            bbox=Rect(self.x, self.y, width, self.size)))
        self.x += width

    def _add(self, element):
        if not self._page_open:
            self.elements = []
            self._page_open = True
        element.z_order = len(self.elements)
        self.elements.append(element)

    def _finish_page(self):
        self.on_page(self.page_width, self.page_height, self.elements)
        self.elements = []
        self._page_open = False
