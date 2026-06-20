""" Parse an AFP printstream file segment into the generic model. """

import logging
import struct

import stream_afp
from stream_record_afp import StreamRecordAFP
from afp.afp_objects import AfpObjectContext
from model.document import Document
from model.element import SourceRef
from model.page import Page
from model.geometry import Rect

logger = logging.getLogger(__name__)


class StreamSegmentAFP:
    """ Parse a byte range of an AFP file, building documents/pages/elements. """

    def __init__(self, file, key, start_byte_offset=None, end_byte_offset=None):
        self.file = file
        self.parser = self.file.parser
        self.name = self.file.name
        self.file_type = self.file.file_type
        self.type = self.file.type
        self.key = key
        self.start_byte_offset = start_byte_offset
        self.end_byte_offset = end_byte_offset
        self.documents = 0
        self.pages = 0
        self.records = 0
        self.bytes = self.end_byte_offset - self.start_byte_offset
        self.options = self.parser.options
        # Model context populated during parsing.
        self.document_set = self.parser.document_set
        self.cur_document = None
        self.cur_page = None
        self.cur_page_in_scope = False
        self.parsed_pages = 0             # pages whose content we actually parsed
        # Accumulates image/graphic/barcode objects and coded-font maps.
        self.objects = AfpObjectContext(self)
        # Current-record context (used to stamp element source references).
        self.cur_rec_number = 0
        self.cur_rec_offset = 0
        self.cur_rec_type = None
        self.cur_rec_length = 0

    # -- document / page lifecycle ----------------------------------------

    def begin_document(self, name=None, offset=None):
        self.cur_document = Document(
            name=name,
            source_ref=SourceRef(file_format="afp", record_type="BDT",
                                 record_number=self.cur_rec_number, byte_offset=offset),
        )
        self.document_set.add_document(self.cur_document)
        self.documents += 1
        sink = self.options.page_sink
        if sink:
            sink.on_document_start(self.cur_document)

    def end_document(self):
        if self.cur_document is not None and self.options.page_sink:
            self.options.page_sink.on_document_end(self.cur_document)
        self.cur_document = None

    def begin_page(self, name=None, offset=None):
        if self.cur_document is None:
            # Page outside an explicit document envelope: open an implicit one.
            self.begin_document(name=None, offset=offset)
        self.pages += 1
        in_range = self.options.in_page_range(self.pages)
        under_cap = (self.options.max_pages is None
                     or self.parsed_pages < self.options.max_pages)
        self.cur_page_in_scope = in_range and under_cap
        self.cur_page = Page(
            number=self.pages,
            size=Rect(0, 0, 612, 792),
            attributes={"name": name} if name else {},
            source_ref=SourceRef(file_format="afp", record_type="BPG",
                                 record_number=self.cur_rec_number, byte_offset=offset),
        )
        # Always attach so structural offsets are correct; may be released on end.
        self.cur_document.add_page(self.cur_page)

    def end_page(self):
        page = self.cur_page
        if page is not None:
            if self.cur_page_in_scope:
                self.parsed_pages += 1
                if self.options.page_sink:
                    self.options.page_sink.on_page(self.cur_document, page)
                drop = not self.options.retain_pages   # release for bounded memory
            else:
                drop = True                            # out-of-scope shell
            if drop and page in self.cur_document.pages:
                self.cur_document.pages.remove(page)
        self.cur_page = None
        self.cur_page_in_scope = False

    # -- parsing ----------------------------------------------------------

    def parse(self):
        """ Parse the segment's records into the model. """
        with open(self.name, "rb") as input_file:
            input_file.seek(self.start_byte_offset)
            cur_offset = self.start_byte_offset
            while cur_offset < self.end_byte_offset:
                rec_offset = cur_offset
                cc = input_file.read(1)
                work = input_file.read(2)
                if not work or len(work) < 2:
                    break
                rec_type = input_file.read(3)
                rec_len, = struct.unpack(">H", work)
                rec_len += 1                      # + carriage-control byte
                rec_data = cc + work + rec_type + input_file.read(rec_len - 6)
                cur_offset = input_file.tell()

                rec_type_cur = stream_afp.afp_rec_type.get(rec_type)
                if rec_type_cur is None:
                    logger.warning("Unknown AFP record id %s at offset %d; skipping",
                                   rec_type.hex(), rec_offset)
                    continue

                self.cur_rec_number += 1
                self.cur_rec_offset = rec_offset
                self.cur_rec_type = rec_type_cur["type"]
                self.cur_rec_length = rec_len
                self.records += 1

                self._dispatch(rec_type_cur["type"], rec_data, rec_len, rec_offset)

                # Cost control: stop once we are past the last page of interest.
                if self.cur_page is None and self.options.past_end(self.pages):
                    break

        if self.options.page_sink:
            self.options.page_sink.on_end()
        self.file.documents += self.documents
        self.file.pages += self.pages
        self.file.records += self.records

    def _dispatch(self, rec_type, rec_data, rec_len, rec_offset):
        """ Handle structural records inline; delegate content records to their class. """
        if rec_type == "BDT":
            self.begin_document(offset=rec_offset)
        elif rec_type == "EDT":
            self.end_document()
        elif rec_type == "BPG":
            self.begin_page(offset=rec_offset)
        elif rec_type == "EPG":
            self.end_page()
            return

        # Gate content parsing by parse level, record-type filter, and page scope.
        if not self.options.wants_record(rec_type):
            return
        if self.cur_page is not None and not self.cur_page_in_scope:
            return

        # Run the record's own parser (text, page geometry, objects, ...).
        cur_rec = StreamRecordAFP(self)
        cur_rec.data = rec_data
        cur_rec.length = rec_len
        cur_rec.type = rec_type
        try:
            cur_rec.parse()
        except Exception:                  # one bad record must not abort the stream
            logger.exception("Failed to parse record %s at offset %d", rec_type, rec_offset)
