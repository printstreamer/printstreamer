""" AFP FNI Record - Font Index """

from struct import unpack, pack


class AFP_FNI:

    def __init__(self, segment):
        self.segment = segment
        self.Entries = []

    def parse(self, data):
        offset = 0
        while offset + 4 <= len(data):
            char_id, pattern_id = unpack(">HH", data[offset:offset+4])
            self.Entries.append((char_id, pattern_id))
            offset += 4

    def format(self):
        data = b""
        for cid, pid in self.Entries:
            data += pack(">HH", cid, pid)
        return data
