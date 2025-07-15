""" Parse pdf printstream file segment. """

import os
import sys
import struct

import fitz  # PyMuPDF
from PIL import Image
from reportlab.lib.colors import Color
from reportlab.lib.pagesizes import A4, LETTER, LEGAL, ELEVENSEVENTEEN, letter
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from stream_page_pdf import StreamPagePDF


class StreamSegmentPDF:
    """ Manage the detail parsing of a segment of a pdf printstream segment. """
    
    def __init__(self, file, key, start_page_offset=None, end_page_offset=None):
        self.file = file
        self.file_obj = None
        self.parser = self.file.parser
        self.name = self.file.name
        self.file_type = self.file.file_type
        self.type = self.file.type
        self.key = key
        self.start_page_offset = start_page_offset
        self.end_page_offset = end_page_offset
        self.documents = 0
        self.pages = 0
        self.records = 0
        self.bytes = 0
        self.cur_page = None
        self.cur_document = None
        self.initialized = False
        self.canvas = None

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
            self.file.parser.output_page(self.cur_page)
            cur_offset += 1
        # Roll up counts to the file level.
        self.file.documents += self.documents
        self.file.pages += self.pages
        self.file.records += self.records
        # Close files.
        self.file_obj.close()
        # Report.
        print(f"\n{self.type.title()} file name:  {self.name}")
        print(f"  Type:             {self.file_type}")
        print(f"  Segment:          {self.key}")
        print(f"  Documents:        {self.documents}")
        print(f"  Pages:            {self.pages}")
        print(f"  Records:          {self.records}")
        print(f"  Bytes:            {self.bytes}")

    def output_start(self):
        """ Start an output file. """
        self.file_obj = canvas.Canvas(self.name)
        self.initialized = True

    def output_document(self, document):
        """ Output a document.

        :param document: Document to output
        """
        if not self.initialized:
            self.output_start()

    def output_page(self, page):
        """ Output a page.

        :param page: Page to output
        """
        if not self.initialized:
            self.output_start()
        self.file_obj.setPageSize((page.width, page.height))
        # Write text.
        for text in page.text:
            # try:
            #     self.file_obj.setFont(item["font"], item["size"])
            # except:
            #     self.file_obj.setFont("Helvetica", item["size"])  # fallback
            text_object = self.file_obj.drawString(text["x"], page.height - text["y"], text["text"])
        # # Write images.
        # for image in page.images:
        #     # Add images (resized if necessary)
        #     y_offset = 150
        #     for img_path in images:
        #         try:
        #             img = Image.open(img_path)
        #             img.thumbnail((400, 400), Image.ANTIALIAS)
        #             c.drawImage(ImageReader(img), 40, height - y_offset - img.height, width=img.width,
        #                         height=img.height)
        #             y_offset += img.height + 20
        #         except Exception as e:
        #             print(f"Failed to draw image {img_path}: {e}")
        # Write the page.
        self.file_obj.showPage()

    def output_end(self):
        """ End an output file. """
        self.file_obj.save()
