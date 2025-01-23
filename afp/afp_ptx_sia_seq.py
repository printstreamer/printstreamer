""" AFP PTX SIA Sequence """

from struct import pack, unpack

from stream_field_afp import StreamFieldAFP


afp_ptx_sia_fields_list = [
    StreamFieldAFP(name="PREFIX", offset=0, length=1, type="CODE", optional=False, range_values=["X'2B'", ''], default=False, indicator=False, meaning=['Control Sequence', '']),
    StreamFieldAFP(name="CLASS", offset=1, length=1, type="CODE", optional=False, range_values=["X'D3'", ''], default=False, indicator=False, meaning=['Control sequence class', '']),
    StreamFieldAFP(name="LENGTH", offset=2, length=1, type="UBIN", optional=False, range_values=['4-5', ''], default=False, indicator=False, meaning=['Control sequence', '']),
    StreamFieldAFP(name="TYPE", offset=3, length=1, type="CODE", optional=False, range_values=["X'C2' -", ''], default=False, indicator=False, meaning=['Control sequence', '']),
    StreamFieldAFP(name="ADJSTMNT", offset=4, length=2, type="SBIN", optional=False, range_values=["X'0000' -", ''], default=True, indicator=True, meaning=['Adjustment', '']),
    StreamFieldAFP(name="DIRCTION", offset=6, length=1, type="CODE", optional=True, range_values=["X'00' -", ''], default=True, indicator=True, meaning=['Direction', '']),
    ]
afp_ptx_sia_fields = {}
for field in afp_ptx_sia_fields_list:
    afp_ptx_sia_fields[field.name] = field


class AFP_PTX_SIA:

    def __init__(self):
                                        # Offset: Length: Type: Range:        Meaning:                  Optional: Def: Ind:
        self.PREFIX = None              #      0       1  CODE  X'2B'         Control Sequence                 n    n    n
        self.CLASS = None               #      1       1  CODE  X'D3'         Control sequence class           n    n    n
        self.LENGTH = None              #      2       1  UBIN  4-5           Control sequence                 n    n    n
        self.TYPE = None                #      3       1  CODE  X'C2' -       Control sequence                 n    n    n
        self.ADJSTMNT = None            #      4       2  SBIN  X'0000' -     Adjustment                       n    y    y
        self.DIRCTION = None            #      6       1  CODE  X'00' -       Direction                        y    y    y

    def parse(self, data):
        """ Parse the data from a record into the record class fields.

        :param bytes data: Record data
        """
        self.PREFIX, self.CLASS, self.LENGTH, self.TYPE, self.ADJSTMNT, self.DIRCTION = unpack(f">1s1sB1sh1s", data)

    def format(self):
        """ Format the data from the record class fields into a record.

        :returns: Record data
        """
        data = pack(f">1s1sB1sh1s", self.PREFIX, self.CLASS, self.LENGTH, self.TYPE, self.ADJSTMNT, self.DIRCTION)
        return data
