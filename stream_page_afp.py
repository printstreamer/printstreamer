""" afp printstream file page. """


class StreamPageAFP:
    """ afp printstream page. """
    
    def __init__(self, segment):
        self.segment = segment
        self.length = 0
        self.type = ""
        self.offset = None
        self.text = []
        self.images = []
        self.attributes = {}

    def parse(self):
        """ Parse an afp printstream page. """
        pass
