""" AFP FNM Record - Font Patterns Map """

from struct import unpack, pack


class AFP_FNM:

    def __init__(self, segment):
        self.segment = segment
        self.Mappings = []

    def parse(self, data):
        offset = 0
        while offset + 6 <= len(data):
            char_id, pattern_id = unpack(">HI", data[offset:offset+6])
            self.Mappings.append((char_id, pattern_id))
            offset += 6

    def format(self):
        data = b""
        for cid, pid in self.Mappings:
            data += pack(">HI", cid, pid)
        return data
