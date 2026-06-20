""" Typed document elements for the generic model.

Every visible thing on a page is an ``Element`` subclass. Elements are format
agnostic: parsers create them from AFP/PDF/etc., writers render them to any target,
and the editing/imposition layers manipulate them without knowing the source format.

Each element keeps a ``source_ref`` back-pointer (originating record type + byte
offset) so we can round-trip faithfully and report accurate offsets in the index.
Anything we cannot fully model is preserved as a ``ContainerElement`` carrying raw
bytes rather than being dropped.
"""

from __future__ import annotations

import enum
import itertools
from dataclasses import dataclass, field

from model.geometry import Color, Matrix, Point, Rect


class ElementKind(str, enum.Enum):
    TEXT = "text"
    LINE = "line"
    IMAGE = "image"
    GRAPHIC = "graphic"
    BARCODE = "barcode"
    FORM = "form"
    OVERLAY = "overlay"
    CONTAINER = "container"


@dataclass
class SourceRef:
    """ Where an element came from in the originating print stream. """
    file_format: str | None = None      # "afp", "pdf", ...
    record_type: str | None = None      # e.g. "PTX", "BPG", or a PTOCA function
    record_number: int | None = None    # ordinal record index within the stream
    byte_offset: int | None = None       # absolute byte offset of the source record
    length: int | None = None            # source record length in bytes


_id_counter = itertools.count(1)


def _next_id() -> int:
    return next(_id_counter)


@dataclass
class Element:
    """ Base class for all page elements. """
    kind: ElementKind = ElementKind.CONTAINER
    bbox: Rect | None = None
    transform: Matrix = field(default_factory=Matrix.identity)
    z_order: int = 0
    attributes: dict = field(default_factory=dict)
    source_ref: SourceRef | None = None
    raw: bytes | None = None             # original bytes, for fidelity / hex selection
    id: int = field(default_factory=_next_id)

    def source_bytes(self) -> bytes:
        """ Bytes used for hex-based selection: the preserved raw record if any. """
        return self.raw or b""


@dataclass
class TextElement(Element):
    """ A positioned run of text. ``position`` is the run's start baseline point. """
    text: str = ""
    position: Point = field(default_factory=Point)
    font_ref: str | None = None          # name into the ResourceLibrary
    font_size: float | None = None        # points
    color: Color | None = None
    orientation: int = 0                  # degrees: 0/90/180/270
    char_spacing: float = 0.0
    raw_text_bytes: bytes | None = None   # undecoded source bytes (codepage), for hex match

    def __post_init__(self):
        self.kind = ElementKind.TEXT

    def source_bytes(self) -> bytes:
        if self.raw_text_bytes:
            return self.raw_text_bytes
        if self.raw:
            return self.raw
        return self.text.encode("utf-8", "replace")


@dataclass
class LineElement(Element):
    """ A straight rule (baseline/inline rule in AFP, vector line elsewhere). """
    start: Point = field(default_factory=Point)
    end: Point = field(default_factory=Point)
    weight: float = 1.0                   # stroke width in points
    color: Color | None = None

    def __post_init__(self):
        self.kind = ElementKind.LINE


@dataclass
class ImageElement(Element):
    """ A placed image. Either references an ImageResource by name or carries its
    own inline bytes. ``bbox`` gives placement/size on the page. """
    resource_ref: str | None = None
    data: bytes | None = None
    encoding: str | None = None           # "jpeg", "fs10", "fs45", ...
    dpi: tuple | None = None
    colorspace: str | None = None

    def __post_init__(self):
        self.kind = ElementKind.IMAGE


@dataclass
class DrawOp:
    """ One normalized vector drawing operation within a GraphicElement. """
    op: str                               # "moveto", "lineto", "curveto", "box",
                                          # "fillet", "arc", "fill", "stroke", ...
    points: list = field(default_factory=list)   # list[Point]
    params: dict = field(default_factory=dict)


@dataclass
class GraphicElement(Element):
    """ A vector graphic as an ordered list of normalized drawing operations
    (GOCA drawing orders, PDF content path ops, HP-GL/2, etc.). """
    ops: list = field(default_factory=list)        # list[DrawOp]
    stroke: Color | None = None
    fill: Color | None = None

    def __post_init__(self):
        self.kind = ElementKind.GRAPHIC


@dataclass
class BarcodeElement(Element):
    """ A barcode. ``symbology`` names the type (e.g. "code39", "code128", "pdf417",
    "qr", or an AFP BCOCA type code); ``data`` is the encoded value. """
    symbology: str | None = None
    data: str = ""
    params: dict = field(default_factory=dict)     # module width, height, HRI, etc.
    color: Color | None = None

    def __post_init__(self):
        self.kind = ElementKind.BARCODE


@dataclass
class FormElement(Element):
    """ A form/overlay placed on the page by reference to a resource. """
    resource_ref: str | None = None

    def __post_init__(self):
        if self.kind not in (ElementKind.FORM, ElementKind.OVERLAY):
            self.kind = ElementKind.FORM


@dataclass
class OverlayElement(FormElement):
    def __post_init__(self):
        self.kind = ElementKind.OVERLAY


@dataclass
class ContainerElement(Element):
    """ A group of child elements, or a preserved-but-unmodeled construct.

    When a parser meets something it cannot fully decompose, it wraps the raw bytes
    here so transforms/merges never silently drop data. ``children`` lets it also act
    as a grouping node (e.g. an AFP object container).
    """
    children: list = field(default_factory=list)   # list[Element]
    preserved_type: str | None = None              # original record/object type

    def __post_init__(self):
        self.kind = ElementKind.CONTAINER
