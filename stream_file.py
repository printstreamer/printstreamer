""" Parse one-to-many segments of a printstream file into the model. """

import logging
import os

from stream_segment_afp import StreamSegmentAFP
from stream_segment_pdf import StreamSegmentPDF
from stream_segment_ps import StreamSegmentPS
from stream_segment_pcl import StreamSegmentPCL
from stream_segment_metacode import StreamSegmentMetacode

logger = logging.getLogger(__name__)

# Map a printstream type to its segment (reader) class. Output files are handled by
# writers (see writer.registry), so only readers are registered here. AFP parses by
# byte range; all others parse by page offset.
SEGMENT_CLASSES = {
    "afp": StreamSegmentAFP,
    "pdf": StreamSegmentPDF,
    "ps": StreamSegmentPS,
    "postscript": StreamSegmentPS,
    "pcl": StreamSegmentPCL,
    "metacode": StreamSegmentMetacode,
}


class StreamFile:
    """ Manage parsing of the segments of one input printstream file. """

    def __init__(self, parser, name, file_type=None, type="input"):
        self.parser = parser
        self.name = name
        self.file_type = file_type
        self.type = type
        self.documents = 0
        self.pages = 0
        self.records = 0
        self.segments = []
        self.bytes = os.path.getsize(name) if type == "input" and os.path.exists(name) else 0
        if type == "input":
            if self.file_type not in SEGMENT_CLASSES:
                raise ValueError(f"Unsupported input file_type: {self.file_type!r}")
            # Single segment per file until concurrent segment parsing is enabled.
            if self.file_type == "afp":
                self.add_segment(self, 1, start_byte_offset=0, end_byte_offset=self.bytes)
            else:
                self.add_segment(self, 1, start_page_offset=0)
        self.cur_segment = self.segments[0] if self.segments else None

    def add_segment(self, file, key, start_byte_offset=None, end_byte_offset=None,
                    start_page_offset=None, end_page_offset=None):
        """ Instantiate and register a reader segment for this file. AFP uses a byte
        range; page-based formats use page offsets. """
        cls = SEGMENT_CLASSES[self.file_type]
        if self.file_type == "afp":
            segment = cls(self, key, start_byte_offset=start_byte_offset,
                          end_byte_offset=end_byte_offset)
        else:
            segment = cls(self, key, start_page_offset=start_page_offset,
                          end_page_offset=end_page_offset)
        self.segments.append(segment)
        return segment

    def parse(self, threads=1):
        """ Parse all segments of this file into the shared model. """
        for segment in self.segments:
            segment.parse()
        logger.info("Input %s: documents=%d pages=%d records=%d bytes=%d",
                    self.name, self.documents, self.pages, self.records, self.bytes)
        print(f"\nInput file name:  {self.name}")
        print(f"  Type:             {self.file_type}")
        print(f"  Documents:        {self.documents}")
        print(f"  Pages:            {self.pages}")
        print(f"  Records:          {self.records}")
        print(f"  Bytes:            {self.bytes}")
