""" Parse afp printstream file segment. """

import os
import sys
import struct

from stream_page_afp import StreamPageAFP
from stream_record_afp import StreamRecordAFP
import stream_afp


class StreamSegmentAFP:
    """ Manage the detail parsing of a segment of an afp printstream segment. """
    
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
        self.cur_page = None
        self.cur_document = None
        self.initialized = False

    def parse(self):
        """ Parse a file segment. """
        # Open file.
        input_file = open(self.name, "rb")
        # Position to segment start in input file.
        input_file.seek(self.start_byte_offset, 1)
        # Parse records until end of segment
        cur_offset = self.start_byte_offset
        rec_count = 0
        while cur_offset < self.end_byte_offset:
            cc = input_file.read(1)
            work = input_file.read(2)
            rec_type = input_file.read(3)
            if work:
                rec_count += 1
                rec_len, = struct.unpack(">h", work)
                rec_len += 1
                rec_len_read = rec_len - 6
                rec_data = cc + work + rec_type + input_file.read(rec_len_read)
                rec_type_cur = stream_afp.afp_rec_type[rec_type]
                if not rec_type_cur:
                    print(f"Error:  missing afp record type ({rec_type})")
                    sys.exit(12)
                # s.decode("EBCDIC-CP-BE").encode("ascii")
                print("record #%d (%s->%s):  %i bytes" % (rec_count, rec_type_cur["type"], rec_type_cur["code"], rec_len))
                cur_offset = input_file.tell()
                cur_rec = StreamRecordAFP(self)
                cur_rec.data = rec_data
                cur_rec.length = rec_len
                cur_rec.type = rec_type_cur["type"]
                if cur_rec.type == "BPG":
                    self.pages += 1
                    self.cur_page = StreamPageAFP(segment=self, byte_offset=cur_offset)
                elif cur_rec.type == "EPG":
                    pause = True
                    print(self.cur_page.text)
                    self.file.parser.output_page(self.cur_page)
                cur_rec.parse()
                self.records += 1
            else:
                break
        # Roll up counts to the file level.
        self.file.documents += self.documents
        self.file.pages += self.pages
        self.file.records += self.records
        # Close files.
        input_file.close()
        # # Report.
        # print(f"\n{self.type.title()} file name:  {self.name}")
        # print(f"  Type:             {self.file_type}")
        # print(f"  Segment:          {self.key}")
        # print(f"  Documents:        {self.documents}")
        # print(f"  Pages:            {self.pages}")
        # print(f"  Records:          {self.records}")
        # print(f"  Bytes:            {self.bytes}")

    def output_start(self):
        """ Start an output file. """
        pass

    def output_document(self, document):
        """ Output a document.

        :param document: Document to output
        """
        pass

    def output_page(self, page):
        """ Output a page.

        :param page: Page to output
        """
        pass

    def output_end(self):
        """ End an output file. """
        pass
