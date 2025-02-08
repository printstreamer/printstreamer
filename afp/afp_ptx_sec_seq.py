""" AFP PTX SEC Sequence """

from struct import pack, unpack

from stream_field_afp import StreamFieldAFP


afp_ptx_sec_fields_list = [
    StreamFieldAFP(name="Reserved_1", offset=0, length=1, type="", optional=False, range_values=['', ''], default=False, indicator=False, meaning=['Reserved; must be', '']),
    StreamFieldAFP(name="COLSPCE", offset=1, length=1, type="CODE", optional=False, range_values=['', ''], default=False, indicator=False, meaning=['Color space', '']),
    StreamFieldAFP(name="Reserved_2", offset=2, length=4, type="", optional=False, range_values=['', ''], default=False, indicator=False, meaning=['Reserved; must be', '']),
    StreamFieldAFP(name="COLSIZE1", offset=6, length=1, type="UBIN", optional=False, range_values=["X'01' �\x03��", ''], default=False, indicator=False, meaning=['Number of bits in', '']),
    StreamFieldAFP(name="COLSIZE2", offset=7, length=1, type="UBIN", optional=False, range_values=["X'00' �\x03��", ''], default=False, indicator=False, meaning=['Number of bits in', '']),
    StreamFieldAFP(name="COLSIZE3", offset=8, length=1, type="UBIN", optional=False, range_values=["X'00' �\x03��", ''], default=False, indicator=False, meaning=['Number of bits in', '']),
    StreamFieldAFP(name="COLSIZE4", offset=9, length=1, type="UBIN", optional=False, range_values=["X'00' �\x03��", ''], default=False, indicator=False, meaning=['Number of bits in', '']),
    StreamFieldAFP(name="COLVALUE", offset=10, length=4, type="UBIN", optional=False, range_values=["X'00' �\x03��", ''], default=False, indicator=False, meaning=['Number of bits in', ''])
    ]
afp_ptx_sec_fields = {}
for field in afp_ptx_sec_fields_list:
    afp_ptx_sec_fields[field.name] = field


class AFP_PTX_SEC:

    def __init__(self):
                                        # Offset: Length: Type: Range:        Meaning:                  Optional: Def: Ind:
        self.Reserved_1 = None          #      0       1                      Reserved; must be                n    n    n
        self.COLSPCE = None             #      1       1  CODE                Color space                      n    n    n
        self.Reserved_2 = None          #      2       4                      Reserved; must be                n    n    n
        self.COLSIZE1 = None            #      6       1  UBIN  X'01'         Number of bits in                n    n    n
        self.COLSIZE2 = None            #      7       1  UBIN  X'00'         Number of bits in                n    n    n
        self.COLSIZE3 = None            #      8       1  UBIN  X'00'         Number of bits in                n    n    n
        self.COLSIZE4 = None            #      9       1  UBIN  X'00'         Number of bits in                n    n    n
        self.COLVALUE = None            #     10       4  UBIN  X'00'         Number of bits in                n    n    n

    def parse(self, data):
        """ Parse the data from a record into the record class fields.

        :param bytes data: Record data
        """
        self.Reserved_1, self.COLSPCE, self.Reserved_2, self.COLSIZE1, self.COLSIZE2, self.COLSIZE3, self.COLSIZE4, self.COLVALUE = unpack(f">1s1s1sBBBB1s", data)

    def format(self):
        """ Format the data from the record class fields into a record.

        :returns: Record data
        """
        data = pack(f">1s1s1sBBBB1s", self.Reserved_1, self.COLSPCE, self.Reserved_2, self.COLSIZE1, self.COLSIZE2, self.COLSIZE3, self.COLSIZE4, self.COLVALUE)
        return data
