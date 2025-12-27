""" AFP CFI Record - Coded Font Index """

from struct import unpack, pack
from stream_field_afp import StreamFieldAFP


class AFP_CFI:

    def __init__(self, segment):
        self.segment = segment
        self.Entries = []

    def parse(self, data):
        offset = 0
        while offset + 4 <= len(data):
            code_point, font_id = unpack(">HH", data[offset:offset+4])
            self.Entries.append((code_point, font_id))
            offset += 4

    def format(self):
        data = b""
        for cp, fid in self.Entries:
            data += pack(">HH", cp, fid)
        return data
