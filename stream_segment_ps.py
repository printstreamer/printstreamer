""" Parse a PostScript/EPS printstream file segment into the generic model. """

import logging

from postscript.interpreter import PSInterpreter
from model.document import Document
from model.element import SourceRef
from model.page import Page
from model.geometry import Rect

logger = logging.getLogger(__name__)


class StreamSegmentPS:
    """ Interpret a PostScript file into one document of model pages. """

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

    def parse(self):
        with open(self.name, "r", encoding="latin-1", errors="replace") as fh:
            text = fh.read()
        self.cur_document = Document(
            name=self.name, source_ref=SourceRef(file_format="ps", record_type="document"))
        self.document_set.add_document(self.cur_document)
        self.documents += 1
        if self.options.page_sink:
            self.options.page_sink.on_document_start(self.cur_document)
        PSInterpreter(self._on_page).run(text)
        if self.options.page_sink:
            self.options.page_sink.on_document_end(self.cur_document)
            self.options.page_sink.on_end()
        self.file.documents += self.documents
        self.file.pages += self.pages
        self.file.records += self.records

    def _on_page(self, width, height, elements):
        self.pages += 1
        if self.options.past_end(self.pages):
            return
        in_scope = (self.options.in_page_range(self.pages)
                    and (self.options.max_pages is None
                         or self.parsed_pages < self.options.max_pages))
        if not in_scope:
            return
        self.parsed_pages += 1
        page = Page(number=self.pages, size=Rect(0, 0, width, height),
                    source_ref=SourceRef(file_format="ps", record_type="page",
                                         record_number=self.pages))
        for z, element in enumerate(elements):
            element.z_order = z
            page.elements.append(element)
        self.cur_document.add_page(page)
        if self.options.page_sink:
            self.options.page_sink.on_page(self.cur_document, page)
        if not self.options.retain_pages and page in self.cur_document.pages:
            self.cur_document.pages.remove(page)
