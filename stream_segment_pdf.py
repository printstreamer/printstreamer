""" Parse pdf printstream file segment. """

import fitz  # PyMuPDF
import os
import sys
import struct

import stream_page_pdf
import stream_pdf


class StreamSegmentPDF:
    """ Manage the detail parsing of a segment of a pdf printstream segment. """
    
    def __init__(self, file, key, start_offset=None, end_offset=None):
        self.file = file
        self.file_obj = None
        self.parser = self.file.parser
        self.name = self.file.name
        self.file_type = self.file.file_type
        self.key = key
        self.start_offset = start_offset
        self.end_offset = end_offset
        self.documents = 0
        self.pages = 0
        self.records = 0
        self.bytes = 0

    def parse(self):
        """ Parse a file segment. """
        # Open file.
        self.file_obj = fitz.open(self.name)
        self.pages = len(self.file_obj)
        if self.end_offset is None:
            self.end_offset = self.pages
        # Parse records until end of segment
        cur_offset = self.start_offset
        rec_count = 0
        while cur_offset < self.end_offset:
            # Parse pdf page.
            cur_page = stream_page_pdf.StreamPagePDF(segment=self, offset=cur_offset)
            cur_page.parse()
            print(cur_page.text)
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
