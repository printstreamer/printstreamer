""" AFP PTX SEC Sequence """

from struct import pack, unpack

from stream_field_afp import StreamFieldAFP


afp_ptx_sec_fields_list = [
    StreamFieldAFP(name="PREFIX", offset=0, length=1, type="CODE", optional=False, range_values=["X'2B'", ''], default=False, indicator=False, meaning=['Control Sequence', '']),
    StreamFieldAFP(name="CLASS", offset=1, length=1, type="CODE", optional=False, range_values=["X'D3'", ''], default=False, indicator=False, meaning=['Control sequence class', '']),
    StreamFieldAFP(name="LENGTH", offset=2, length=1, type="UBIN", optional=False, range_values=['14-16', ''], default=False, indicator=False, meaning=['Control sequence', '']),
    StreamFieldAFP(name="TYPE", offset=3, length=1, type="CODE", optional=False, range_values=["X'80' -", ''], default=False, indicator=False, meaning=['Control sequence', '']),
    StreamFieldAFP(name="Reserved_1", offset=4, length=1, type="", optional=False, range_values=['', ''], default=False, indicator=False, meaning=['Reserved; must be', '']),
    StreamFieldAFP(name="COLSPCE", offset=5, length=1, type="CODE", optional=False, range_values=['', ''], default=False, indicator=False, meaning=['Color space', '']),
    StreamFieldAFP(name="Reserved_2", offset=6, length=4, type="", optional=False, range_values=['', ''], default=False, indicator=False, meaning=['Reserved; must be', '']),
    StreamFieldAFP(name="COLSIZE1", offset=10, length=1, type="UBIN", optional=False, range_values=["X'01' �\x03��", ''], default=False, indicator=False, meaning=['Number of bits in', '']),
    StreamFieldAFP(name="COLSIZE2", offset=11, length=1, type="UBIN", optional=False, range_values=["X'00' �\x03��", ''], default=False, indicator=False, meaning=['Number of bits in', '']),
    StreamFieldAFP(name="COLSIZE3", offset=12, length=1, type="UBIN", optional=False, range_values=["X'00' �\x03��", ''], default=False, indicator=False, meaning=['Number of bits in', '']),
    StreamFieldAFP(name="COLSIZE4", offset=13, length=1, type="UBIN", optional=False, range_values=["X'00' �\x03��", ''], default=False, indicator=False, meaning=['Number of bits in', '']),
    StreamFieldAFP(name="COLVALUE", offset=14, length=4, type="UBIN", optional=False, range_values=["X'00' �\x03��", ''], default=False, indicator=False, meaning=['Number of bits in', ''])
    ]
afp_ptx_sec_fields = {}
for field in afp_ptx_sec_fields_list:
    afp_ptx_sec_fields[field.name] = field


class AFP_PTX_SEC:

    def __init__(self):
                                        # Offset: Length: Type: Range:        Meaning:                  Optional: Def: Ind:
        self.PREFIX = None              #      0       1  CODE  X'2B'         Control Sequence                 n    n    n
        self.CLASS = None               #      1       1  CODE  X'D3'         Control sequence class           n    n    n
        self.LENGTH = None              #      2       1  UBIN  14-16         Control sequence                 n    n    n
        self.TYPE = None                #      3       1  CODE  X'80' -       Control sequence                 n    n    n
        self.Reserved_1 = None          #      4       1                      Reserved; must be                n    n    n
        self.COLSPCE = None             #      5       1  CODE                Color space                      n    n    n
        self.Reserved_2 = None          #      6       4                      Reserved; must be                n    n    n
        self.COLSIZE1 = None            #     10       1  UBIN  X'01' ���    Number of bits in                n    n    n
        self.COLSIZE2 = None            #     11       1  UBIN  X'00' ���    Number of bits in                n    n    n
        self.COLSIZE3 = None            #     12       1  UBIN  X'00' ���    Number of bits in                n    n    n
        self.COLSIZE4 = None            #     13       1  UBIN  X'00' ���    Number of bits in                n    n    n
        self.COLVALUE = None            #     14       4  UBIN  X'00' ���    Number of bits in                n    n    n

    def parse(self, data):
        """ Parse the data from a record into the record class fields.

        :param bytes data: Record data
        """
        self.PREFIX, self.CLASS, self.LENGTH, self.TYPE, self.Reserved_1, self.COLSPCE, self.Reserved_2, self.COLSIZE1, self.COLSIZE2, self.COLSIZE3, self.COLSIZE4, self.COLVALUE = unpack(f">1s1sB1s1s1s1sBBBB1s", data)

    def format(self):
        """ Format the data from the record class fields into a record.

        :returns: Record data
        """
        data = pack(f">1s1sB1s1s1s1sBBBB1s", self.PREFIX, self.CLASS, self.LENGTH, self.TYPE, self.Reserved_1, self.COLSPCE, self.Reserved_2, self.COLSIZE1, self.COLSIZE2, self.COLSIZE3, self.COLSIZE4, self.COLVALUE)
        return data
