""" Parse printstream file segment. """

import os
import sys
import struct

from stream_record import StreamRecord
import stream_afp


class StreamSegment:
    """ Manage the detail parsing of a segment of a printstream segment. """
    
    def __init__(self, file, key, start_offset=None, end_offset=None):
        self.file = file
        self.parser = self.file.parser
        self.name = self.file.name
        self.file_type = self.file.file_type
        self.key = key
        self.start_offset = start_offset
        self.end_offset = end_offset
        self.documents = 0
        self.pages = 0
        self.records = 0
        self.bytes = self.end_offset - self.start_offset

    def parse(self):
        """ Parse a file segment. """
        # Open files.
        input_file = open(self.name, "rb")
        # Position to segment start in input file.
        input_file.seek(self.start_offset, 1)
        # Parse records until end of segment
        cur_offset = self.start_offset
        rec_count = 0
        while cur_offset < self.end_offset:
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
                cur_rec = StreamRecord(self)
                cur_rec.data = rec_data
                cur_rec.length = rec_len
                cur_rec.type = rec_type_cur["type"]
                cur_rec.parse()
                self.records += 1
            else:
                break
        # Close files.
        input_file.close()
        # Report.
        print(f"\nInput file name:  {self.name}")
        print(f"  Segment:          {self.key}")
        print(f"  Documents:        {self.documents}")
        print(f"  Pages:            {self.pages}")
        print(f"  Records:          {self.records}")
        print(f"  Bytes:            {self.bytes}")
