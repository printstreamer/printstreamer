""" AFP PTX OVS Sequence """

from struct import pack, unpack

from stream_field_afp import StreamFieldAFP


afp_ptx_ovs_fields_list = [
    StreamFieldAFP(name="PREFIX", offset=0, length=1, type="CODE", optional=False, range_values=["X'2B'", ''], default=False, indicator=False, meaning=['Control Sequence', '']),
    StreamFieldAFP(name="CLASS", offset=1, length=1, type="CODE", optional=False, range_values=["X'D3'", ''], default=False, indicator=False, meaning=['Control sequence class', '']),
    StreamFieldAFP(name="LENGTH", offset=2, length=1, type="UBIN", optional=False, range_values=['5', ''], default=False, indicator=False, meaning=['Control sequence', '']),
    StreamFieldAFP(name="TYPE", offset=3, length=1, type="CODE", optional=False, range_values=["X'72' -", ''], default=False, indicator=False, meaning=['Control sequence', '']),
    StreamFieldAFP(name="BYPSIDEN", offset=4, length=1, type="BITS", optional=False, range_values=['See', ''], default=True, indicator=True, meaning=['Bypass identifiers', '']),
    StreamFieldAFP(name="OVERCHAR X'0000' -", offset=5, length=2, type="CODE", optional=False, range_values=['', ''], default=False, indicator=False, meaning=['Overstrike character', '']),
    ]
afp_ptx_ovs_fields = {}
for field in afp_ptx_ovs_fields_list:
    afp_ptx_ovs_fields[field.name] = field


class AFP_PTX_OVS:

    def __init__(self):
                                        # Offset: Length: Type: Range:        Meaning:                  Optional: Def: Ind:
        self.PREFIX = None              #      0       1  CODE  X'2B'         Control Sequence                 n    n    n
        self.CLASS = None               #      1       1  CODE  X'D3'         Control sequence class           n    n    n
        self.LENGTH = None              #      2       1  UBIN  5             Control sequence                 n    n    n
        self.TYPE = None                #      3       1  CODE  X'72' -       Control sequence                 n    n    n
        self.BYPSIDEN = None            #      4       1  BITS  See           Bypass identifiers               n    y    y
        self.OVERCHAR X'0000' - = None  #      5       2  CODE                Overstrike character             n    n    n

    def parse(self, data):
        """ Parse the data from a record into the record class fields.

        :param bytes data: Record data
        """
        self.PREFIX, self.CLASS, self.LENGTH, self.TYPE, self.BYPSIDEN, self.OVERCHAR X'0000' - = unpack(f">1s1sB1s1s2s", data)

    def format(self):
        """ Format the data from the record class fields into a record.

        :returns: Record data
        """
        data = pack(f">1s1sB1s1s2s", self.PREFIX, self.CLASS, self.LENGTH, self.TYPE, self.BYPSIDEN, self.OVERCHAR X'0000' -)
        return data
