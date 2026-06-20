""" Shared resources for the generic model (fonts, images, overlays, etc.).

Resources are content referenced by elements/pages and shared across pages and
documents: fonts, embedded images, overlays, page segments, colour tables. The
``ResourceLibrary`` deduplicates them by name and tracks reference counts so writers
emit only what is actually used and merges can resolve name collisions.
"""

from __future__ import annotations

import enum
from collections import Counter
from dataclasses import dataclass, field


class ResourceKind(str, enum.Enum):
    FONT = "font"
    IMAGE = "image"
    OVERLAY = "overlay"
    PAGE_SEGMENT = "page_segment"
    COLOR_TABLE = "color_table"
    RAW = "raw"


@dataclass
class Resource:
    """ Base resource. ``name`` is the library key. """
    name: str
    kind: ResourceKind = ResourceKind.RAW
    attributes: dict = field(default_factory=dict)


@dataclass
class FontResource(Resource):
    """ A font. For AFP this ties together the coded font, code page, and char set,
    plus the codepage->Unicode mapping needed to decode/re-encode text correctly. """
    coded_font: str | None = None
    code_page: str | None = None
    char_set: str | None = None
    typeface: str | None = None
    size: float | None = None             # points, if fixed-size
    orientation: int = 0
    encoding_map: dict = field(default_factory=dict)   # codepoint(int) -> unicode str
    metrics: dict = field(default_factory=dict)        # codepoint -> advance width

    def __post_init__(self):
        self.kind = ResourceKind.FONT

    def decode(self, raw: bytes) -> str:
        """ Decode raw codepage bytes to a Unicode string using this font's map.
        Falls back to latin-1 for codepoints not present in the map. """
        if not self.encoding_map:
            return raw.decode("latin-1", "replace")
        return "".join(self.encoding_map.get(b, chr(b)) for b in raw)


@dataclass
class ImageResource(Resource):
    data: bytes | None = None
    image_format: str | None = None       # "jpeg", "tiff", "fs45", ...
    width: int | None = None
    height: int | None = None
    dpi: tuple | None = None
    colorspace: str | None = None

    def __post_init__(self):
        self.kind = ResourceKind.IMAGE


@dataclass
class OverlayResource(Resource):
    """ An overlay/form: its own mini page of elements, placed by reference. """
    page: object | None = None            # a model.page.Page
    raw: bytes | None = None

    def __post_init__(self):
        self.kind = ResourceKind.OVERLAY


@dataclass
class PageSegmentResource(Resource):
    page: object | None = None
    raw: bytes | None = None

    def __post_init__(self):
        self.kind = ResourceKind.PAGE_SEGMENT


@dataclass
class ColorTableResource(Resource):
    entries: dict = field(default_factory=dict)

    def __post_init__(self):
        self.kind = ResourceKind.COLOR_TABLE


@dataclass
class RawResource(Resource):
    """ A resource we preserve byte-for-byte without fully modeling it. """
    raw: bytes | None = None
    original_kind: str | None = None

    def __post_init__(self):
        self.kind = ResourceKind.RAW


class ResourceLibrary:
    """ A name-keyed collection of resources with reference counting. """

    def __init__(self):
        self._resources: dict[str, Resource] = {}
        self._refcounts: Counter[str] = Counter()

    def __contains__(self, name: str) -> bool:
        return name in self._resources

    def __iter__(self):
        return iter(self._resources.values())

    def add(self, resource: Resource) -> Resource:
        """ Add a resource (idempotent on name). Returns the stored resource. """
        self._resources.setdefault(resource.name, resource)
        return self._resources[resource.name]

    def get(self, name: str) -> Resource | None:
        return self._resources.get(name)

    def reference(self, name: str) -> None:
        if name:
            self._refcounts[name] += 1

    def dereference(self, name: str) -> None:
        if name and self._refcounts[name] > 0:
            self._refcounts[name] -= 1

    def refcount(self, name: str) -> int:
        return self._refcounts[name]

    def referenced(self) -> list[Resource]:
        return [r for n, r in self._resources.items() if self._refcounts[n] > 0]

    def prune_unreferenced(self) -> list[str]:
        """ Drop resources whose reference count is zero. Returns removed names. """
        removed = [n for n in list(self._resources)
                   if self._refcounts[n] <= 0]
        for n in removed:
            del self._resources[n]
            self._refcounts.pop(n, None)
        return removed

    def merge(self, other: "ResourceLibrary", rename_conflicts: bool = True) -> dict:
        """ Merge ``other`` into this library. Returns a name-remap dict for any
        resources that had to be renamed because of a content collision. """
        remap: dict[str, str] = {}
        for res in other:
            if res.name not in self._resources:
                self.add(res)
            elif self._resources[res.name] is res or not rename_conflicts:
                continue
            else:
                new_name = self._unique_name(res.name)
                res.name = new_name
                self.add(res)
                remap[res.name] = new_name
        return remap

    def _unique_name(self, base: str) -> str:
        i = 1
        while f"{base}_{i}" in self._resources:
            i += 1
        return f"{base}_{i}"
