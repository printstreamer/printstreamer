""" Parse a printstream file record. """

#from afp_bpg_rec import AFP_BPG
#from afp_ptx_rec import AFP_PTX
from stream_afp import afp_rec_type_text


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
        rec = afp_rec_type_text[self.type]["class"](self.segment)
        rec.parse(data)
