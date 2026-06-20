""" Page model: an ordered collection of elements plus geometry and index tags. """

from __future__ import annotations

from dataclasses import dataclass, field

from model.element import Element, ElementKind, SourceRef
from model.geometry import Rect


@dataclass
class IndexTag:
    """ A logical tag attached to a page or document (AFP TLE / index element, PDF
    bookmark, etc.). Used by document identification and the index file. """
    name: str
    value: str | None = None
    attributes: dict = field(default_factory=dict)


@dataclass
class Page:
    """ One page of a document. """
    number: int = 0                       # 1-based page number within the stream
    size: Rect = field(default_factory=lambda: Rect(0, 0, 612, 792))
    orientation: int = 0                  # degrees
    elements: list = field(default_factory=list)         # list[Element]
    resources_used: set = field(default_factory=set)     # resource names
    attributes: dict = field(default_factory=dict)
    index_tags: list = field(default_factory=list)       # list[IndexTag]
    source_ref: SourceRef | None = None

    @property
    def width(self) -> float:
        return self.size.width

    @property
    def height(self) -> float:
        return self.size.height

    def add_element(self, element: Element) -> Element:
        if element.z_order == 0:
            element.z_order = len(self.elements)
        self.elements.append(element)
        return element

    def iter_elements(self, kind: ElementKind | None = None):
        for el in self.elements:
            if kind is None or el.kind == kind:
                yield el

    def ordered_elements(self) -> list:
        """ Elements in z-order (paint order). """
        return sorted(self.elements, key=lambda e: e.z_order)
