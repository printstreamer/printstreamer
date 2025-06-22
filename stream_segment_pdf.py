""" Parse pdf printstream file segment. """

import fitz  # PyMuPDF
import os
import sys
import struct

from stream_page_pdf import StreamPagePDF
import stream_pdf


class StreamSegmentPDF:
    """ Manage the detail parsing of a segment of a pdf printstream segment. """
    
    def __init__(self, file, key, start_page_offset=None, end_page_offset=None):
        self.file = file
        self.file_obj = None
        self.parser = self.file.parser
        self.name = self.file.name
        self.file_type = self.file.file_type
        self.key = key
        self.start_page_offset = start_page_offset
        self.end_page_offset = end_page_offset
        self.documents = 0
        self.pages = 0
        self.records = 0
        self.bytes = 0
        self.cur_page = None
        self.cur_document = None

    def parse(self):
        """ Parse a file segment. """
        # Open file.
        self.file_obj = fitz.open(self.name)
        self.pages = len(self.file_obj)
        if self.end_page_offset is None:
            self.end_page_offset = self.pages
        # Parse records until end of segment
        cur_offset = self.start_page_offset
        rec_count = 0
        while cur_offset < self.end_page_offset:
            # Parse pdf page.
            self.cur_page = StreamPagePDF(segment=self, page_offset=cur_offset)
            self.cur_page.parse()
            print(self.cur_page.text)
            cur_offset += 1
        # Roll up counts to the file level.
        self.file.documents += self.documents
        self.file.pages += self.pages
        self.file.records += self.records
        # Close files.
        self.file_obj.close()
        # Report.
        print(f"\nInput file name:  {self.name}")
        print(f"  Type:             {self.file_type}")
        print(f"  Segment:          {self.key}")
        print(f"  Documents:        {self.documents}")
        print(f"  Pages:            {self.pages}")
        print(f"  Records:          {self.records}")
        print(f"  Bytes:            {self.bytes}")
