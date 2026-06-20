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
        # Skip the structured-field introducer: carriage control (1) + length (2)
        # + identifier (3) + flags (1) + sequence (2) = 9 bytes. The remainder is
        # the structured-field data the record class knows how to parse.
        start = 9
        data = self.data[start:self.length]
        rec = afp_rec_type_text[self.type]["class"](self.segment)
        rec.parse(data)
        return rec
