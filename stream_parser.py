""" Parse one to many chunks of one to many printstream files concurrently. """

import os
import sys
import struct

from stream_record import StreamRecord
import stream_afp


class StreamParser:
    """ Manage the detail parsing of segments of printstream files. """
    
    def __init__(self):
        self.segments = []

    def add_segment(self, input_name=None, start_offset="0", end_offset="-0", output_name=None):
        """ Add a parsing segment to the parser segment list.

        :param input_name:
        :param start_offset:
        :param end_offset:
        :param output_name:
        :return:
        """
        # Set input and output files.
        segment = {'input_name': input_name, 'output_name': output_name}
        # Capture size of input file.
        input_size = os.path.getsize(input_name)
        # Set start offset and reference in input file.
        if '-' in start_offset:
            segment['start_offset'] = input_size - int(start_offset)
        else:
            segment['start_offset'] = int(start_offset)
        # Set end offset and reference in input file.
        if '-' in end_offset:
            segment['end_offset'] = input_size - int(end_offset)
        else:
            segment['end_offset'] = int(end_offset)
        # Append segment to parser list.
        self.segments.append(segment)
        
    def parse_segment(self, segment):
        """ Parse a file segment. """
        # Initialize variables.
        input_name = segment['input_name']
        output_name = segment['output_name']
        start_offset = segment['start_offset']
        end_offset = segment['end_offset']

        # Open files.
        input = open(input_name, 'rb')        
        if output_name:
            output = open(output_name, 'wb')
        else:
            output = None
        # Position to segment start in input file.
        input.seek(start_offset,1)
        # Parse records until end of segment
        cur_offset = start_offset
        rec_count = 0
        while cur_offset < end_offset:
            cc = input.read(1)
            work = input.read(2)
            rec_type = input.read(3)
            if not work:
                break
            else:
                rec_count += 1
                rec_len, = struct.unpack(">h", work)
                rec_len += 1
                rec_len_read = rec_len - 6
                rec_data = cc + work + rec_type + input.read(rec_len_read)
                rec_type_cur = stream_afp.afp_rec_type[rec_type]
                if not rec_type_cur:
                    print(f"Error:  missing afp record type ({rec_type})")
                    sys.exit(12)
                # s.decode('EBCDIC-CP-BE').encode('ascii')
                print("record #%d (%s->%s):  %i bytes" % (rec_count, rec_type_cur['type'], rec_type_cur['code'], rec_len))
                cur_offset = input.tell()
                cur_rec = StreamRecord()
                cur_rec.data = rec_data
                cur_rec.length = rec_len
                cur_rec.type = rec_type_cur['type']
                cur_rec.parse()
        # Close files.
        input.close()
        if output:
            output.close()

    def parse_segments(self, threads=2):
        """ Parse all segments and manage the parsing threads.

        :param threads:
        :return:
        """
        for segment in self.segments:
            self.parse_segment(segment)
            