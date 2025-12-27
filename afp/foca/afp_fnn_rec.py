""" AFP FNN Record - Font Name Map """

class AFP_FNN:

    def __init__(self, segment):
        self.segment = segment
        self.FontName = None

    def parse(self, data):
        self.FontName = data.decode("cp500").rstrip()

    def format(self):
        return self.FontName.encode("cp500")
