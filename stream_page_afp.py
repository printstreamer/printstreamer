""" afp printstream file page. """


class StreamPageAFP:
    """ afp printstream page. """
    
    def __init__(self, segment, byte_offset=None):
        self.segment = segment
        self.byte_offset = byte_offset
        self.length = 0
        self.type = ""
        self.text = []
        self.images = []
        self.attributes = {}

    def parse(self):
        """ Parse an afp printstream page. """
        pass
