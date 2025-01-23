""" AFP PTX TRN Sequence """

from struct import pack, unpack

from stream_field_afp import StreamFieldAFP


afp_ptx_trn_fields_list = [
    StreamFieldAFP(name="PREFIX", offset=0, length=1, type="CODE", optional=True, range_values=["X'2B'", ''], default=False, indicator=False, meaning=['Control Sequence', '']),
    StreamFieldAFP(name="CLASS", offset=1, length=1, type="CODE", optional=True, range_values=["X'D3'", ''], default=False, indicator=False, meaning=['Control sequence class', '']),
    StreamFieldAFP(name="LENGTH", offset=2, length=1, type="UBIN", optional=True, range_values=['2-255', ''], default=False, indicator=False, meaning=['Control sequence', '']),
    StreamFieldAFP(name="TYPE", offset=3, length=1, type="CODE", optional=True, range_values=["X'DA' -", ''], default=False, indicator=False, meaning=['Control sequence', '']),
    StreamFieldAFP(name="TRNDATA", offset=4, length=253, type="CHAR", optional=True, range_values=['Not', ''], default=False, indicator=False, meaning=['Transparent data', '']),
    ]
afp_ptx_trn_fields = {}
for field in afp_ptx_trn_fields_list:
    afp_ptx_trn_fields[field.name] = field


class AFP_PTX_TRN:

    def __init__(self):
                                        # Offset: Length: Type: Range:        Meaning:                  Optional: Def: Ind:
        self.PREFIX = None              #      0       1  CODE  X'2B'         Control Sequence                 y    n    n
        self.CLASS = None               #      1       1  CODE  X'D3'         Control sequence class           y    n    n
        self.LENGTH = None              #      2       1  UBIN  2-255         Control sequence                 y    n    n
        self.TYPE = None                #      3       1  CODE  X'DA' -       Control sequence                 y    n    n
        self.TRNDATA = None             #      4     253  CHAR  Not           Transparent data                 y    n    n

    def parse(self, data):
        """ Parse the data from a record into the record class fields.

        :param bytes data: Record data
        """
        self.PREFIX, self.CLASS, self.LENGTH, self.TYPE, self.TRNDATA = unpack(f">1s1sB1s253s", data)

    def format(self):
        """ Format the data from the record class fields into a record.

        :returns: Record data
        """
        data = pack(f">1s1sB1s253s", self.PREFIX, self.CLASS, self.LENGTH, self.TYPE, self.TRNDATA)
        return data
