""" Generic in-memory model shared by every print-stream format.

Parsers build a ``StreamDocumentSet``; writers consume it; the editing, indexing,
imposition, label, and markup layers all operate purely on this model. Adding a new
format means writing a parser + writer pair against these types — no feature code
needs to change.
"""

from model.document import Document, StreamDocumentSet
from model.element import (
    BarcodeElement,
    ContainerElement,
    DrawOp,
    Element,
    ElementKind,
    FormElement,
    GraphicElement,
    ImageElement,
    LineElement,
    OverlayElement,
    SourceRef,
    TextElement,
)
from model.geometry import Color, Matrix, Point, Rect
from model.page import IndexTag, Page
from model.resource import (
    ColorTableResource,
    FontResource,
    ImageResource,
    OverlayResource,
    PageSegmentResource,
    RawResource,
    Resource,
    ResourceKind,
    ResourceLibrary,
)

__all__ = [
    "StreamDocumentSet", "Document", "Page", "IndexTag",
    "Element", "ElementKind", "SourceRef",
    "TextElement", "LineElement", "ImageElement", "GraphicElement", "DrawOp",
    "BarcodeElement", "FormElement", "OverlayElement", "ContainerElement",
    "Point", "Rect", "Matrix", "Color",
    "Resource", "ResourceKind", "ResourceLibrary", "FontResource", "ImageResource",
    "OverlayResource", "PageSegmentResource", "ColorTableResource", "RawResource",
]
