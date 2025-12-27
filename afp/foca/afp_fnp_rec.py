""" AFP FNP Record - Font Position """

from struct import unpack, pack


class AFP_FNP:

    def __init__(self, segment):
        self.segment = segment
        self.X = None
        self.Y = None

    def parse(self, data):
        self.X, self.Y = unpack(">hh", data[0:4])

    def format(self):
        return pack(">hh", self.X, self.Y)
