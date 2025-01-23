""" AFP PTX USC Sequence """

from struct import pack, unpack

from stream_field_afp import StreamFieldAFP


afp_ptx_usc_fields_list = [
    StreamFieldAFP(name="PREFIX", offset=0, length=1, type="CODE", optional=True, range_values=["X'2B'", ''], default=False, indicator=False, meaning=['Control Sequence', '']),
    StreamFieldAFP(name="CLASS", offset=1, length=1, type="CODE", optional=True, range_values=["X'D3'", ''], default=False, indicator=False, meaning=['Control sequence class', '']),
    StreamFieldAFP(name="LENGTH", offset=2, length=1, type="UBIN", optional=True, range_values=['3', ''], default=False, indicator=False, meaning=['Control sequence', '']),
    StreamFieldAFP(name="TYPE", offset=3, length=1, type="CODE", optional=True, range_values=["X'76' -", ''], default=False, indicator=False, meaning=['Control sequence', '']),
    StreamFieldAFP(name="BYPSIDEN", offset=4, length=1, type="BITS", optional=True, range_values=['See', ''], default=True, indicator=True, meaning=['Bypass identifiers', '']),
    StreamFieldAFP(name="bypass is in e", offset=1, length=1, type="means no", optional=True, range_values=['ffect.', ''], default=True, indicator=True, meaning=['', '']),
    StreamFieldAFP(name="Reserved_1", offset=0, length=4, type="", optional=True, range_values=['at is, set to', ''], default=True, indicator=True, meaning=['0 by generators and ignored', '']),
    StreamFieldAFP(name="Reserved_2", offset=4, length=1, type="", optional=True, range_values=['ive Move Inlin', ''], default=True, indicator=True, meaning=['e', '']),
    StreamFieldAFP(name="Reserved_3", offset=5, length=1, type="", optional=True, range_values=['ute Move Inlin', ''], default=True, indicator=True, meaning=['e', '']),
    StreamFieldAFP(name="Reserved_4", offset=6, length=1, type="", optional=True, range_values=['characters an', ''], default=True, indicator=True, meaning=['d variable space characters', '']),
    StreamFieldAFP(name="Reserved_5", offset=7, length=1, type="", optional=True, range_values=['effect', ''], default=True, indicator=True, meaning=['', '']),
    ]
afp_ptx_usc_fields = {}
for field in afp_ptx_usc_fields_list:
    afp_ptx_usc_fields[field.name] = field


class AFP_PTX_USC:

    def __init__(self):
                                        # Offset: Length: Type: Range:        Meaning:                  Optional: Def: Ind:
        self.PREFIX = None              #      0       1  CODE  X'2B'         Control Sequence                 y    n    n
        self.CLASS = None               #      1       1  CODE  X'D3'         Control sequence class           y    n    n
        self.LENGTH = None              #      2       1  UBIN  3             Control sequence                 y    n    n
        self.TYPE = None                #      3       1  CODE  X'76' -       Control sequence                 y    n    n
        self.BYPSIDEN = None            #      4       1  BITS  See           Bypass identifiers               y    y    y
        self.bypass is in e = None      #      1       1  mean  ffect.                                         y    y    y
        self.Reserved_1 = None          #      0       4        at is, set to 0 by generators and ignor        y    y    y
        self.Reserved_2 = None          #      4       1        ive Move Inli e                                y    y    y
        self.Reserved_3 = None          #      5       1        ute Move Inli e                                y    y    y
        self.Reserved_4 = None          #      6       1        characters an d variable space characte        y    y    y
        self.Reserved_5 = None          #      7       1        effect                                         y    y    y

    def parse(self, data):
        """ Parse the data from a record into the record class fields.

        :param bytes data: Record data
        """
        self.PREFIX, self.CLASS, self.LENGTH, self.TYPE, self.BYPSIDEN, self.bypass is in e, self.Reserved_1, self.Reserved_2, self.Reserved_3, self.Reserved_4, self.Reserved_5 = unpack(f">1s1sB1s1s4s1s1s1s1s", data)

    def format(self):
        """ Format the data from the record class fields into a record.

        :returns: Record data
        """
        data = pack(f">1s1sB1s1s4s1s1s1s1s", self.PREFIX, self.CLASS, self.LENGTH, self.TYPE, self.BYPSIDEN, self.bypass is in e, self.Reserved_1, self.Reserved_2, self.Reserved_3, self.Reserved_4, self.Reserved_5)
        return data
