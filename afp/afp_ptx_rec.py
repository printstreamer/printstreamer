""" AFP PTX Record """

from struct import pack, unpack

import stream_afp
from stream_field_afp import StreamFieldAFP
from stream_function_afp import StreamFunctionAFP


afp_ptx_fields_list = [
    StreamFieldAFP(name="PTOCAdat", offset=0, length=32761, type="UNDF", optional=True, exception='\x00', range_values=['', '', ''], meaning=['Up to 32,759 bytes of', 'PTOCA-defined data', '']),
    ]
afp_ptx_fields = {}
for field in afp_ptx_fields_list:
    afp_ptx_fields[field.name] = field


class AFP_PTX:

    def __init__(self):
                                        # Offset: Length: Type: Optional: Exception: Range:                Meaning:
        self.PTOCAdat = None            #      0   32761  UNDF  y         X'00'                            Up to 32,759 bytes of
                                        #                                                                  PTOCA-defined data

    def parse(self, data):
        """ Parse the data from a record into the record class fields.

        :param bytes data: Record data
        """
        # self.PTOCAdat = unpack(f">{self.PTOCAdat.len()}s", data)
        start = 0
        length = len(data)
        while start < length:
            cur_function = StreamFunctionAFP()
            value = ""
            if data[start:start + 1] == b"\x2B":
                cur_function.length = 2
                cur_function.type = "ESC"
            else:
                # cur_function.length = struct.unpack(">h", self.data[start:start + 1])
                # cur_function.length = int(self.data[start:start + 1], 2)
                cur_function.length = ord(data[start:start + 1])
                cur_function.type = stream_afp.afp_ptx_by_value[data[start + 1:start + 2]]["type"]
                if (cur_function.type == "TRN") or (cur_function.type == "TRN-C"):
                    cur_function.data = data[start + 2:start + 2 + cur_function.length - 2]
                    value = cur_function.data
            print(
                f"  PTX function:  type={cur_function.type} start={start} length={cur_function.length} value=({value})")
            start += cur_function.length

    def format(self):
        """ Format the data from the record class fields into a record.

        :returns: Record data
        """
        data = pack(f">{self.PTOCAdat.len()}s", self.PTOCAdat)
        return data
