""" Parse a printstream file record. """

from afp_ptx_rec import AFP_PTX


class StreamRecordAFP:
    """ Manage the parsing of printstream records. """
    
    def __init__(self, segment):
        self.segment = segment
        self.length = 0
        self.data = ""
        self.type = ""
        
    def parse(self):
        """ Parse a printstream record. """
        # Parse record types.
        start = 9
        length = self.length - start
        data = self.data[start:length]
        if self.type == "PTX":
            ptx = AFP_PTX()
            ptx.parse(data)
        elif self.type == "BPG":
            self.segment.pages += 1
