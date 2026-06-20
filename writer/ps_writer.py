""" Render the generic model to PostScript (level 2).

Emits one page per model page with text (moveto/show), rules (stroke), and filled
rectangles/paths. PostScript user space is points with a bottom-left origin, so model
y-coordinates are flipped against the page height.
"""

import logging

from model.element import ElementKind

logger = logging.getLogger(__name__)


def _esc(text):
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _font_name(document, element):
    """ Resolve a text element's font to a PostScript standard font name via the AFP
    character-set carried on its FontResource (base-14 names map 1:1 to PS fonts). """
    import fontmetrics
    res = None
    if document is not None and element.font_ref:
        res = document.resource_library.get(element.font_ref)
    charset = getattr(res, "char_set", None) or getattr(res, "coded_font", None)
    return fontmetrics.base_font_for(charset) if charset else "Helvetica"


class PsWriter:
    """ Write a StreamDocumentSet to a PostScript file. """

    def write(self, document_set, path):
        out = ["%!PS-Adobe-3.0", f"%%Pages: {document_set.page_count}"]
        pageno = 0
        for _document, page in document_set.iter_pages():
            pageno += 1
            h = page.height or 792
            out.append(f"%%Page: {pageno} {pageno}")
            out.append(f"<< /PageSize [{page.width or 612:.0f} {h:.0f}] >> setpagedevice")
            for el in page.ordered_elements():
                self._emit(out, el, h, _document)
            out.append("showpage")
        out.append("%%EOF")
        with open(path, "w", encoding="latin-1", errors="replace") as fh:
            fh.write("\n".join(out) + "\n")
        logger.info("Wrote PostScript %s (%d pages)", path, document_set.page_count)

    def _rgb(self, out, color):
        if color is not None:
            r, g, b = color.to_rgb()
            out.append(f"{r:.3f} {g:.3f} {b:.3f} setrgbcolor")

    def _emit(self, out, el, h, document=None):
        if el.kind == ElementKind.TEXT and el.text:
            self._rgb(out, el.color)
            out.append(f"/{_font_name(document, el)} findfont {el.font_size or 10:.2f} scalefont setfont")
            out.append(f"{el.position.x:.2f} {h - el.position.y:.2f} moveto ({_esc(el.text)}) show")
        elif el.kind == ElementKind.LINE:
            self._rgb(out, el.color)
            out.append(f"{el.weight or 1:.2f} setlinewidth")
            out.append(f"{el.start.x:.2f} {h - el.start.y:.2f} moveto "
                       f"{el.end.x:.2f} {h - el.end.y:.2f} lineto stroke")
        elif el.kind == ElementKind.GRAPHIC and el.bbox is not None:
            b = el.bbox
            self._rgb(out, el.fill or el.stroke)
            verb = "rectfill" if el.fill is not None else "rectstroke"
            out.append(f"{b.x:.2f} {h - b.y1:.2f} {b.width:.2f} {b.height:.2f} {verb}")
        elif el.kind == ElementKind.IMAGE and el.bbox is not None:
            b = el.bbox                       # placeholder outline for images
            out.append("0.7 0.7 0.7 setrgbcolor 0.5 setlinewidth")
            out.append(f"{b.x:.2f} {h - b.y1:.2f} {b.width:.2f} {b.height:.2f} rectstroke")
