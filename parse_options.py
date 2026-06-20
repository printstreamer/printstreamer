""" Parse scope/level options and the page-sink protocol.

``ParseOptions`` lets a caller bound the effort, space, and time of parsing: which
pages, which record types, which resource types, and how deeply to decode. A
``page_sink`` enables bounded memory: completed pages are handed to the sink and may
be dropped from the model instead of accumulating.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field


class ParseLevel(enum.IntEnum):
    """ How deeply to parse, from cheapest to most complete. """
    STRUCTURE = 1     # documents/pages/offsets only (no element content)
    ELEMENTS = 2      # element geometry + text (default)
    FULL = 3          # decode object content and resources (images, graphics, fonts)


class PageSink:
    """ Receives completed documents/pages as they are parsed. Override what you need.

    Returning is enough; the parser decides whether to also retain the page in the
    model (see ``ParseOptions.retain_pages``).
    """

    def on_document_start(self, document):
        pass

    def on_page(self, document, page):
        pass

    def on_document_end(self, document):
        pass

    def on_end(self):
        pass


@dataclass
class ParseOptions:
    """ Controls the scope and depth of a parse. """
    start_page: int = 1                       # 1-based, inclusive
    end_page: int | None = None               # inclusive; None = to end
    max_pages: int | None = None              # cap on pages parsed
    record_types: set | None = None           # allow-list of record types (None = all)
    skip_record_types: set | None = None      # deny-list of record types
    resource_types: set | None = None         # allow-list of resource kinds (None = all)
    skip_triplets: set | None = None           # triplet ids to skip decoding (None = all)
    object_kinds: set | None = None            # allow-list of object kinds (image/graphic/barcode)
    level: ParseLevel = ParseLevel.ELEMENTS
    page_sink: PageSink | None = None
    retain_pages: bool = True                 # keep pages in the model after the sink
    threads: int = 1                          # parse worker threads (1 = serial)
    font_path: str | None = None              # external AFP font-resource library dir

    def is_full_scope(self) -> bool:
        """ True when nothing limits the parse (so threading is safe to use). """
        return (self.start_page == 1 and self.end_page is None and self.max_pages is None
                and self.page_sink is None and self.retain_pages)

    def in_page_range(self, page_number: int) -> bool:
        if page_number < self.start_page:
            return False
        if self.end_page is not None and page_number > self.end_page:
            return False
        return True

    def past_end(self, page_number: int) -> bool:
        """ True once we are beyond the last page of interest (lets parsing stop). """
        return self.end_page is not None and page_number > self.end_page

    def wants_record(self, record_type: str) -> bool:
        if self.level <= ParseLevel.STRUCTURE:
            return False
        if self.skip_record_types and record_type in self.skip_record_types:
            return False
        if self.record_types is not None and record_type not in self.record_types:
            return False
        return True

    def wants_resource(self, resource_kind: str) -> bool:
        return self.resource_types is None or resource_kind in self.resource_types

    def wants_triplet(self, tid: int) -> bool:
        """ Whether to decode a triplet id. A process can skip triplets it doesn't need
        (e.g. colour/finishing triplets when only text is required) to save time on
        very large streams. Bytes are always consumed; only decoding is skipped. """
        return not (self.skip_triplets and tid in self.skip_triplets)

    def wants_object(self, kind: str) -> bool:
        """ Whether to decode an object kind (image/graphic/barcode). """
        return self.object_kinds is None or kind in self.object_kinds


# Default options used when a caller does not supply any.
DEFAULT_OPTIONS = ParseOptions()
