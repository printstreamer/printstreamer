""" Render the generic model to a Xerox Metacode order stream.

Emits the inverse of metacode.parser: one length-prefixed record per page containing
FONT / SET_X / SET_Y / TEXT orders for each text element, terminated by ENDPG. Uses
the same default order codes; calibrate to your variant if needed.
"""

import logging

from metacode.parser import ORDERS
from model.element import ElementKind

logger = logging.getLogger(__name__)

_DOTS_PER_POINT = 300.0 / 72.0
_FONT_SIZES = {0: 10.0, 1: 12.0, 2: 8.0, 3: 14.0}


def _dots(points):
    return max(0, min(0xFFFF, int(round(points * _DOTS_PER_POINT))))


def _font_index(size):
    best = min(_FONT_SIZES, key=lambda k: abs(_FONT_SIZES[k] - (size or 10.0)))
    return best


class MetacodeWriter:
    """ Write a StreamDocumentSet to a Metacode file. """

    def write(self, document_set, path):
        out = bytearray()
        for _document, page in document_set.iter_pages():
            out += self._pack(self._page_orders(page))
        with open(path, "wb") as fh:
            fh.write(out)
        logger.info("Wrote Metacode %s (%d pages)", path, document_set.page_count)

    def _page_orders(self, page):
        """ Return the page's orders as a list of byte chunks (one order each). """
        orders = []
        cur_font = None
        for el in page.ordered_elements():
            if el.kind != ElementKind.TEXT or not el.text:
                continue
            fi = _font_index(el.font_size)
            if fi != cur_font:
                orders.append(bytes([ORDERS["FONT"], fi]))
                cur_font = fi
            orders.append(bytes([ORDERS["SET_X"]]) + _dots(el.position.x).to_bytes(2, "big"))
            top = el.position.y - (el.font_size or 10.0)
            orders.append(bytes([ORDERS["SET_Y"]]) + _dots(top).to_bytes(2, "big"))
            text = el.text.encode("cp500", "replace")
            for i in range(0, max(len(text), 1), 253):     # TEXT order <= 255 bytes
                chunk = text[i:i + 253]
                orders.append(bytes([ORDERS["TEXT"], len(chunk)]) + chunk)
        orders.append(bytes([ORDERS["ENDPG"]]))
        return orders

    def _pack(self, orders):
        """ Pack whole orders into <=255-byte length-prefixed records. """
        out = bytearray()
        rec = bytearray()
        for order in orders:
            if len(rec) + len(order) > 255:
                out += bytes([len(rec)]) + rec
                rec = bytearray()
            rec += order
        if rec:
            out += bytes([len(rec)]) + rec
        return out
