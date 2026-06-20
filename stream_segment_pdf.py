""" Parse a PDF printstream file segment into the generic model. """

import logging

import fitz  # PyMuPDF

from model.document import Document
from model.element import ImageElement, SourceRef, TextElement
from model.geometry import Color, Point, Rect

logger = logging.getLogger(__name__)


class StreamSegmentPDF:
    """ Parse a page range of a PDF file, building one document of model pages. """

    def __init__(self, file, key, start_page_offset=None, end_page_offset=None):
        self.file = file
        self.parser = self.file.parser
        self.name = self.file.name
        self.file_type = self.file.file_type
        self.type = self.file.type
        self.key = key
        self.start_page_offset = start_page_offset or 0
        self.end_page_offset = end_page_offset
        self.documents = 0
        self.pages = 0
        self.records = 0
        self.parsed_pages = 0
        self.options = self.parser.options
        self.document_set = self.parser.document_set
        self.cur_document = None
        self.cur_page = None

    def parse(self):
        """ Parse the PDF page range into the model. """
        doc = fitz.open(self.name)
        try:
            total = len(doc)
            end = self.end_page_offset if self.end_page_offset is not None else total
            self.cur_document = Document(
                name=self.name,
                source_ref=SourceRef(file_format="pdf", record_type="document",
                                     byte_offset=0),
            )
            self.document_set.add_document(self.cur_document)
            self.documents += 1
            sink = self.options.page_sink
            if sink:
                sink.on_document_start(self.cur_document)
            for page_index in range(self.start_page_offset, end):
                self._parse_page(doc, page_index)
                if self.options.past_end(self.pages):
                    break
            if sink:
                sink.on_document_end(self.cur_document)
                sink.on_end()
        finally:
            doc.close()
        self.file.documents += self.documents
        self.file.pages += self.pages
        self.file.records += self.records

    def _parse_page(self, doc, page_index):
        self.pages += 1
        in_scope = (self.options.in_page_range(self.pages)
                    and (self.options.max_pages is None
                         or self.parsed_pages < self.options.max_pages))
        pdf_page = doc.load_page(page_index)
        rect = pdf_page.rect
        page = self.cur_document.add_page(self._make_page(page_index, rect))
        self.cur_page = page
        if not in_scope:
            self.cur_document.pages.remove(page)   # drop out-of-scope shell
            return
        self.parsed_pages += 1
        if self.options.wants_record("span"):
            self._extract_text(pdf_page, page)
        if self.options.level >= 3 or self.options.wants_record("image"):
            self._extract_images(doc, pdf_page, page)
        if self.options.page_sink:
            self.options.page_sink.on_page(self.cur_document, page)
        if not self.options.retain_pages and page in self.cur_document.pages:
            self.cur_document.pages.remove(page)

    def _make_page(self, page_index, rect):
        from model.page import Page
        return Page(
            number=self.pages,
            size=Rect(0, 0, rect.width, rect.height),
            source_ref=SourceRef(file_format="pdf", record_type="page",
                                 record_number=page_index + 1),
        )

    def _extract_text(self, pdf_page, page):
        for block in pdf_page.get_text("dict")["blocks"]:
            if block.get("type") != 0:
                continue
            for line in block["lines"]:
                for span in line["spans"]:
                    x0, y0, x1, y1 = span["bbox"]
                    page.add_element(TextElement(
                        text=span["text"],
                        position=Point(x0, y0),
                        font_ref=span["font"],
                        font_size=span["size"],
                        color=Color.from_rgb_int(span["color"]),
                        bbox=Rect.from_corners(x0, y0, x1, y1),
                        source_ref=SourceRef(file_format="pdf", record_type="span"),
                    ))

    def _extract_images(self, doc, pdf_page, page):
        for img in pdf_page.get_images(full=True):
            xref = img[0]
            try:
                rects = pdf_page.get_image_rects(xref)
                extracted = doc.extract_image(xref)
            except Exception:
                continue
            for rect in rects or []:
                page.add_element(ImageElement(
                    data=extracted.get("image"),
                    encoding=extracted.get("ext"),
                    colorspace=extracted.get("colorspace"),
                    bbox=Rect.from_corners(rect.x0, rect.y0, rect.x1, rect.y1),
                    source_ref=SourceRef(file_format="pdf", record_type="image"),
                ))
