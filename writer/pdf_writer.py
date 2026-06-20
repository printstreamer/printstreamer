""" Render the generic model to a PDF using ReportLab. """

import io
import logging

from reportlab.lib.colors import Color as RLColor
from reportlab.pdfgen import canvas

from model.element import ElementKind

logger = logging.getLogger(__name__)

_DEFAULT_FONT = "Helvetica"


def _truthy(value):
    if value is None:
        return False
    s = str(value).strip().lower()
    return s in ("1", "true", "yes", "on") or (s.isdigit() and int(s) > 0)


class PdfWriter:
    """ Write a StreamDocumentSet to a PDF file. """

    def write(self, document_set, path):
        # Internal compression zlib-compresses PDF content streams (smaller files at a
        # little CPU cost). This is distinct from compressing the whole output file.
        # Tri-state: unset -> ReportLab default; explicit on -> 1; explicit off -> 0.
        opts = getattr(self, "options", None) or {}
        val = opts.get("internal_compress")
        page_compression = None if val is None else (1 if _truthy(val) else 0)
        c = canvas.Canvas(path, pageCompression=page_compression)
        bm = 0
        for document, page in document_set.iter_pages():
            c.setPageSize((page.width or 612, page.height or 792))
            for tag in self._bookmarks(document, page):
                key = f"bm{bm}"
                c.bookmarkPage(key)
                c.addOutlineEntry(tag.value or tag.name, key)
                bm += 1
            for element in page.ordered_elements():
                try:
                    self._render(c, page, element)
                except Exception:
                    logger.exception("Failed to render %s on page %d",
                                     element.kind, page.number)
            c.showPage()
        if bm:
            c.showOutline()
        c.save()
        logger.info("Wrote PDF %s (%d pages)", path, document_set.page_count)

    def _bookmarks(self, document, page):
        tags = [t for t in page.index_tags if t.name == "bookmark"]
        if page is document.pages[0]:        # surface document bookmarks on its first page
            tags = [t for t in document.index_tags if t.name == "bookmark"] + tags
        return tags

    # -- element rendering ------------------------------------------------

    def _flip_y(self, page, y):
        """ Convert a top-left model y to ReportLab's bottom-left origin. """
        return (page.height or 792) - y

    def _set_color(self, c, color, stroke=False):
        if color is None:
            return
        r, g, b = color.to_rgb()
        if stroke:
            c.setStrokeColor(RLColor(r, g, b))
        else:
            c.setFillColor(RLColor(r, g, b))

    def _render(self, c, page, element):
        if element.kind == ElementKind.TEXT:
            self._render_text(c, page, element)
        elif element.kind == ElementKind.LINE:
            self._render_line(c, page, element)
        elif element.kind == ElementKind.IMAGE:
            self._render_image(c, page, element)
        elif element.kind == ElementKind.BARCODE:
            self._render_barcode(c, page, element)
        elif element.kind == ElementKind.GRAPHIC:
            self._render_graphic(c, page, element)
        # FORM / OVERLAY / CONTAINER: emitted by the AFP writer; not drawn in PDF.

    def _render_graphic(self, c, page, element):
        stroked = element.stroke is not None
        filled = element.fill is not None
        if stroked:
            self._set_color(c, element.stroke, stroke=True)
        if filled:
            self._set_color(c, element.fill)
        for op in element.ops:
            pts = op.points
            if op.op == "box" and len(pts) >= 2:
                x0, y0, x1, y1 = pts[0].x, pts[0].y, pts[1].x, pts[1].y
                c.rect(x0, self._flip_y(page, max(y0, y1)), abs(x1 - x0), abs(y1 - y0),
                       stroke=stroked, fill=filled)
            elif op.op == "ellipse" and len(pts) >= 2:
                c.ellipse(pts[0].x, self._flip_y(page, pts[0].y),
                          pts[1].x, self._flip_y(page, pts[1].y),
                          stroke=stroked, fill=filled)
            elif op.op in ("polyline", "path") and len(pts) >= 2:
                p = c.beginPath()
                p.moveTo(pts[0].x, self._flip_y(page, pts[0].y))
                for pt in pts[1:]:
                    p.lineTo(pt.x, self._flip_y(page, pt.y))
                if op.op == "polyline":
                    p.close()
                c.drawPath(p, stroke=stroked, fill=filled)

    def _render_text(self, c, page, element):
        if not element.text:
            return
        size = element.font_size or 10.0
        c.setFont(_DEFAULT_FONT, size)
        self._set_color(c, element.color)
        x = element.position.x
        y = self._flip_y(page, element.position.y)
        orientation = getattr(element, "orientation", 0) % 360
        if orientation:
            # Rotate glyphs about the baseline origin (model is clockwise, top-left).
            c.saveState()
            c.translate(x, y)
            c.rotate(-orientation)
            c.drawString(0, 0, element.text)
            c.restoreState()
        else:
            c.drawString(x, y, element.text)

    def _render_line(self, c, page, element):
        self._set_color(c, element.color, stroke=True)
        c.setLineWidth(element.weight or 1.0)
        c.line(element.start.x, self._flip_y(page, element.start.y),
               element.end.x, self._flip_y(page, element.end.y))

    def _render_image(self, c, page, element):
        if element.bbox is None:
            return
        bbox = element.bbox
        data = self._decodable(element)
        if data:
            try:
                from reportlab.lib.utils import ImageReader
                c.drawImage(ImageReader(io.BytesIO(data)), bbox.x,
                            self._flip_y(page, bbox.y1), width=bbox.width,
                            height=bbox.height, mask="auto")
                return
            except Exception:
                # Data PIL/ReportLab cannot open directly: outline the region instead.
                logger.debug("Image not directly decodable (%s); outlining region",
                             element.encoding)
        c.saveState()
        c.setLineWidth(0.5)
        c.setStrokeColorRGB(0.7, 0.7, 0.7)
        c.rect(bbox.x, self._flip_y(page, bbox.y1), bbox.width, bbox.height)
        c.restoreState()

    def _decodable(self, element):
        """ Return renderable image bytes: decode IOCA bilevel to PNG, else raw. """
        data = element.data
        if data and element.encoding and element.encoding.startswith("ioca"):
            from afp.ioca_image import ioca_to_png
            png = ioca_to_png(data, element.attributes.get("px_width"),
                              element.attributes.get("px_height"), element.encoding)
            if png:
                return png
        return data

    def _render_barcode(self, c, page, element):
        if element.bbox is None:
            return
        from writer import barcodes
        bbox = element.bbox
        y = self._flip_y(page, bbox.y1)
        if element.color is not None:
            self._set_color(c, element.color)
        if barcodes.render(c, element.symbology, element.data, element.params,
                           bbox.x, y, bbox.width, bbox.height):
            return
        # Fallback: framed human-readable value for unsupported symbologies.
        c.setFont(_DEFAULT_FONT, 8)
        c.drawString(bbox.x, y + 2, f"[{element.symbology or 'barcode'}:{element.data}]")
        c.rect(bbox.x, y, bbox.width, bbox.height)
