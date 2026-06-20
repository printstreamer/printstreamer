""" Document and document-set model.

A ``Document`` is an ordered set of pages with its own resource library and index
tags. A ``StreamDocumentSet`` is the top of the model: the whole parsed stream, an
ordered list of documents sharing a global resource library. Parsers populate it,
writers consume it, and every processing layer operates on it.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from model.element import SourceRef
from model.page import Page
from model.resource import ResourceLibrary


@dataclass
class Document:
    """ One logical document within a stream. """
    name: str | None = None
    pages: list = field(default_factory=list)            # list[Page]
    resource_library: ResourceLibrary = field(default_factory=ResourceLibrary)
    index_tags: list = field(default_factory=list)       # list[IndexTag]
    attributes: dict = field(default_factory=dict)
    source_ref: SourceRef | None = None

    @property
    def page_count(self) -> int:
        return len(self.pages)

    def add_page(self, page: Page) -> Page:
        self.pages.append(page)
        return page


class StreamDocumentSet:
    """ The root model object: all documents parsed from a stream. """

    def __init__(self):
        self.documents: list[Document] = []
        self.resource_library = ResourceLibrary()   # global/shared resources
        self.attributes: dict = {}

    def add_document(self, document: Document) -> Document:
        self.documents.append(document)
        return document

    @property
    def document_count(self) -> int:
        return len(self.documents)

    @property
    def page_count(self) -> int:
        return sum(d.page_count for d in self.documents)

    def iter_pages(self):
        """ Yield (document, page) pairs across the whole set in order. """
        for doc in self.documents:
            for page in doc.pages:
                yield doc, page

    def all_pages(self) -> list:
        return [page for _, page in self.iter_pages()]
