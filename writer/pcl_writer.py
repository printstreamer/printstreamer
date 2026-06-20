""" Render the generic model to PCL5.

Emits text with font selection and dot-precise cursor positioning, rules and filled
rectangles via the PCL rectangle-area commands, and a form feed between pages. PCL5 is
monochrome here; element colour is not emitted. Coordinates are PCL dots at 300 dpi.
"""

import logging

from model.element import ElementKind

logger = logging.getLogger(__name__)

ESC = b"\x1b"
_DOTS_PER_POINT = 300.0 / 72.0


def _dots(points):
    return int(round(points * _DOTS_PER_POINT))


class PclWriter:
    """ Write a StreamDocumentSet to a PCL file. """

    def write(self, document_set, path):
        out = bytearray()
        out += ESC + b"E"                       # printer reset
        first = True
        for _document, page in document_set.iter_pages():
            if not first:
                out += b"\x0c"                  # form feed between pages
            first = False
            for el in page.ordered_elements():
                self._emit(out, el, _document)
        out += ESC + b"E"
        with open(path, "wb") as fh:
            fh.write(out)
        logger.info("Wrote PCL %s (%d pages)", path, document_set.page_count)

    def _emit(self, out, el, document=None):
        if el.kind == ElementKind.TEXT and el.text:
            size = el.font_size or 10.0
            # Cursor Y is the line top; our reader adds the font size to reach baseline.
            top = (el.position.y - size)
            out += ESC + f"(s{size:.2f}V".encode("latin-1")
            if self._is_bold(document, el):
                out += ESC + b"(s3B"            # bold weight
            else:
                out += ESC + b"(s0B"            # normal weight
            out += ESC + f"*p{_dots(el.position.x)}x{_dots(top)}Y".encode("latin-1")
            out += el.text.encode("latin-1", "replace")
        elif el.kind == ElementKind.LINE:
            x = min(el.start.x, el.end.x)
            y = min(el.start.y, el.end.y)
            w = max(abs(el.end.x - el.start.x), el.weight or 1.0)
            h = max(abs(el.end.y - el.start.y), el.weight or 1.0)
            self._rect(out, x, y, w, h)
        elif el.kind == ElementKind.GRAPHIC and el.bbox is not None:
            self._rect(out, el.bbox.x, el.bbox.y, el.bbox.width, el.bbox.height)

    def _is_bold(self, document, el):
        """ Resolve weight from the AFP character-set name on the element's font. """
        res = None
        if document is not None and getattr(el, "font_ref", None):
            res = document.resource_library.get(el.font_ref)
        name = (getattr(res, "char_set", None) or getattr(res, "coded_font", None)
                or str(getattr(el, "font_ref", "") or "")).upper()
        return any(tok in name for tok in ("BOLD", "B0", "DB", "BD"))

    def _rect(self, out, x, y, w, h):
        out += ESC + f"*p{_dots(x)}x{_dots(y)}Y".encode("latin-1")
        out += ESC + f"*c{_dots(w)}a{_dots(h)}b0P".encode("latin-1")   # fill rectangle
