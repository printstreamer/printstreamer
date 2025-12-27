""" AFP CPI Record - Code Page Index """

from struct import unpack, pack


class AFP_CPI:

    def __init__(self, segment):
        self.segment = segment
        self.Entries = []

    def parse(self, data):
        offset = 0
        while offset + 4 <= len(data):
            code_point, glyph_id = unpack(">HH", data[offset:offset+4])
            self.Entries.append((code_point, glyph_id))
            offset += 4

    def format(self):
        data = b""
        for cp, gid in self.Entries:
            data += pack(">HH", cp, gid)
        return data
