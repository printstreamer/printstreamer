""" StreamRecord class manages records in printstream files. """

import struct

from stream_function import StreamFunction
import stream_afp

    
class StreamRecord:
    """ Manage the parsing of printstream records. """
    
    def __init__(self):
        self.length = 0
        self.data = ''
        self.type = ''
        
    def parse(self):
        """ Parse a printstream record. """
        # Parse record types.
        if self.type == 'PTX':
            start = 9
            while start < self.length:
                cur_function = StreamFunction()
                if self.data[start:start + 1] == b'\x2B':
                    cur_function.length = 2
                    cur_function.type = 'ESC'
                else:
                    # cur_function.length = struct.unpack(">h", self.data[start:start + 1])
                    # cur_function.length = int(self.data[start:start + 1], 2)
                    cur_function.length = ord(self.data[start:start + 1])
                    cur_function.type = stream_afp.afp_ptx_by_value[self.data[start + 1:start + 2]]['type']
                    if (cur_function.type == 'TRN') or (cur_function.type == 'TRN-C'):
                        cur_function.data = self.data[start + 2:start + 2 + cur_function.length - 2]
                print(f"  PTX function:  type={cur_function.type} start={start} length={cur_function.length} data=({cur_function.data})")
                start += cur_function.length
