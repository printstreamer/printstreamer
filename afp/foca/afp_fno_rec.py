""" AFP FNO Record - Font Orientation """

from struct import unpack, pack


class AFP_FNO:

    def __init__(self, segment):
        self.segment = segment
        self.Orientation = None

    def parse(self, data):
        self.Orientation = unpack(">H", data[0:2])[0]

    def format(self):
        return pack(">H", self.Orientation)
