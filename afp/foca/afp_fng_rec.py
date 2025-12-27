""" AFP FNG Record - Font Patterns """

class AFP_FNG:

    def __init__(self, segment):
        self.segment = segment
        self.PatternData = b""

    def parse(self, data):
        self.PatternData = data

    def format(self):
        return self.PatternData
