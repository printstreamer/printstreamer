""" AFP PTX STO Sequence """

from struct import pack, unpack

from stream_field_afp import StreamFieldAFP


afp_ptx_sto_fields_list = [
    StreamFieldAFP(name="PREFIX", offset=0, length=1, type="CODE", optional=False, range_values=["X'2B'", ''], default=False, indicator=False, meaning=['Control Sequence', '']),
    StreamFieldAFP(name="CLASS", offset=1, length=1, type="CODE", optional=False, range_values=["X'D3'", ''], default=False, indicator=False, meaning=['Control sequence class', '']),
    StreamFieldAFP(name="LENGTH", offset=2, length=1, type="UBIN", optional=False, range_values=['6', ''], default=False, indicator=False, meaning=['Control sequence', '']),
    StreamFieldAFP(name="TYPE", offset=3, length=1, type="CODE", optional=False, range_values=["X'F6' -", ''], default=False, indicator=False, meaning=['Control sequence', '']),
    StreamFieldAFP(name="IORNTION", offset=4, length=2, type="CODE", optional=False, range_values=['See', ''], default=True, indicator=True, meaning=['I-axis orientation', '']),
    StreamFieldAFP(name="BORNTION", offset=6, length=2, type="CODE", optional=False, range_values=['See', ''], default=True, indicator=True, meaning=['B-axis orientation', '']),
    ]
afp_ptx_sto_fields = {}
for field in afp_ptx_sto_fields_list:
    afp_ptx_sto_fields[field.name] = field


class AFP_PTX_STO:

    def __init__(self):
                                        # Offset: Length: Type: Range:        Meaning:                  Optional: Def: Ind:
        self.PREFIX = None              #      0       1  CODE  X'2B'         Control Sequence                 n    n    n
        self.CLASS = None               #      1       1  CODE  X'D3'         Control sequence class           n    n    n
        self.LENGTH = None              #      2       1  UBIN  6             Control sequence                 n    n    n
        self.TYPE = None                #      3       1  CODE  X'F6' -       Control sequence                 n    n    n
        self.IORNTION = None            #      4       2  CODE  See           I-axis orientation               n    y    y
        self.BORNTION = None            #      6       2  CODE  See           B-axis orientation               n    y    y

    def parse(self, data):
        """ Parse the data from a record into the record class fields.

        :param bytes data: Record data
        """
        self.PREFIX, self.CLASS, self.LENGTH, self.TYPE, self.IORNTION, self.BORNTION = unpack(f">1s1sB1s2s2s", data)

    def format(self):
        """ Format the data from the record class fields into a record.

        :returns: Record data
        """
        data = pack(f">1s1sB1s2s2s", self.PREFIX, self.CLASS, self.LENGTH, self.TYPE, self.IORNTION, self.BORNTION)
        return data
