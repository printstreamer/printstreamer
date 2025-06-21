""" Parse one-to-many segments of a printstream file. """

import os

from stream_segment_afp import StreamSegmentAFP
from stream_segment_pdf import StreamSegmentPDF


class StreamFile:
    """ Manage the parsing of segments of a printstream file. """
    
    def __init__(self, parser, name, file_type=None):
        self.parser = parser
        self.name = name
        self.file_type = file_type
        self.documents = 0
        self.pages = 0
        self.records = 0
        self.bytes = os.path.getsize(name)
        self.segments = []
        # Single-segment processing until multithreading of concurrent segments is implemented.
        if self.file_type == "afp":
            self.add_segment(self, 1, start_offset=0, end_offset=self.bytes)
        elif self.file_type == "pdf":
            self.add_segment(self, 1, start_offset=0)

    def add_segment(self, file, key, start_offset=None, end_offset=None):
        """ Add a parsing segment to the parser segment list.

        :param StreamFile file: Stream file object
        :param int key: Segment key
        :param int start_offset:
        :param int end_offset:
        :return: StreamSegment object
        """
        # Instantiate segment.
        segment = None
        if self.file_type == "afp":
            segment = StreamSegmentAFP(self, key, start_offset=start_offset, end_offset=end_offset)
        elif self.file_type == "pdf":
            segment = StreamSegmentPDF(self, key, start_offset=start_offset, end_offset=end_offset)
        # Append segment to parser list.
        self.segments.append(segment)
        return segment

    def parse(self, threads=1):
        """ Parse all segments.

        :param threads:
        :return:
        """
        for segment in self.segments:
            segment.parse()
        # Report.
        print(f"\nInput file name:  {self.name}")
        print(f"  Type:             {self.file_type}")
        print(f"  Documents:        {self.documents}")
        print(f"  Pages:            {self.pages}")
        print(f"  Records:          {self.records}")
        print(f"  Bytes:            {self.bytes}")
