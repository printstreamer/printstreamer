""" AFP PTX TBM Sequence """

from struct import pack, unpack

from stream_field_afp import StreamFieldAFP


afp_ptx_tbm_fields_list = [
    StreamFieldAFP(name="PREFIX", offset=0, length=1, type="CODE", optional=True, range_values=["X'2B'", ''], default=False, indicator=False, meaning=['Control Sequence', '']),
    StreamFieldAFP(name="CLASS", offset=1, length=1, type="CODE", optional=True, range_values=["X'D3'", ''], default=False, indicator=False, meaning=['Control sequence class', '']),
    StreamFieldAFP(name="LENGTH", offset=2, length=1, type="UBIN", optional=True, range_values=['3, 4, 6', ''], default=False, indicator=False, meaning=['Control sequence', '']),
    StreamFieldAFP(name="TYPE", offset=3, length=1, type="CODE", optional=True, range_values=["X'78' -", ''], default=False, indicator=False, meaning=['Control sequence', '']),
    StreamFieldAFP(name="DIRCTION", offset=4, length=1, type="CODE", optional=True, range_values=["X'00' -", ''], default=True, indicator=True, meaning=['Direction', '']),
    StreamFieldAFP(name="PRECSION", offset=5, length=1, type="BITS", optional=True, range_values=["X'00' -", ''], default=True, indicator=True, meaning=['Precision', '']),
    StreamFieldAFP(name="INCRMENT", offset=6, length=2, type="SBIN", optional=True, range_values=["X'0000' -", ''], default=True, indicator=True, meaning=['Temporary baseline', '']),
    StreamFieldAFP(name="ment value. Th", offset=2, length=1, type="line incre", optional=True, range_values=['e PTOCA defaul', ''], default=True, indicator=True, meaning=['t value for DIRCTION and', '']),
    StreamFieldAFP(name="not change the", offset=0, length=1, type="Do", optional=True, range_values=['baseline.', ''], default=True, indicator=True, meaning=['', '']),
    StreamFieldAFP(name="urn to the est", offset=1, length=1, type="Ret", optional=True, range_values=['ablished basel', ''], default=True, indicator=True, meaning=['ine. Delete the temporary b', '']),
    StreamFieldAFP(name="e the temporar", offset=2, length=1, type="Mov", optional=True, range_values=['y baseline awa', ''], default=True, indicator=True, meaning=['y from the I-axis one value', '']),
    StreamFieldAFP(name="e the temporar", offset=3, length=1, type="Mov", optional=True, range_values=['y baseline tow', ''], default=True, indicator=True, meaning=['ard the I-axis one value of', '']),
    ]
afp_ptx_tbm_fields = {}
for field in afp_ptx_tbm_fields_list:
    afp_ptx_tbm_fields[field.name] = field


class AFP_PTX_TBM:

    def __init__(self):
                                        # Offset: Length: Type: Range:        Meaning:                  Optional: Def: Ind:
        self.PREFIX = None              #      0       1  CODE  X'2B'         Control Sequence                 y    n    n
        self.CLASS = None               #      1       1  CODE  X'D3'         Control sequence class           y    n    n
        self.LENGTH = None              #      2       1  UBIN  3, 4, 6       Control sequence                 y    n    n
        self.TYPE = None                #      3       1  CODE  X'78' -       Control sequence                 y    n    n
        self.DIRCTION = None            #      4       1  CODE  X'00' -       Direction                        y    y    y
        self.PRECSION = None            #      5       1  BITS  X'00' -       Precision                        y    y    y
        self.INCRMENT = None            #      6       2  SBIN  X'0000' -     Temporary baseline               y    y    y
        self.ment value. Th = None      #      2       1  line  e PTOCA defau t value for DIRCTION and         y    y    y
        self.not change the = None      #      0       1  Do    baseline.                                      y    y    y
        self.urn to the est = None      #      1       1  Ret   ablished base ine. Delete the temporary        y    y    y
        self.e the temporar = None      #      2       1  Mov   y baseline aw y from the I-axis one val        y    y    y
        self.e the temporar = None      #      3       1  Mov   y baseline to ard the I-axis one value         y    y    y

    def parse(self, data):
        """ Parse the data from a record into the record class fields.

        :param bytes data: Record data
        """
        self.PREFIX, self.CLASS, self.LENGTH, self.TYPE, self.DIRCTION, self.PRECSION, self.INCRMENT, self.ment value. Th, self.not change the, self.urn to the est, self.e the temporar, self.e the temporar = unpack(f">1s1sB1s1s1sh", data)

    def format(self):
        """ Format the data from the record class fields into a record.

        :returns: Record data
        """
        data = pack(f">1s1sB1s1s1sh", self.PREFIX, self.CLASS, self.LENGTH, self.TYPE, self.DIRCTION, self.PRECSION, self.INCRMENT, self.ment value. Th, self.not change the, self.urn to the est, self.e the temporar, self.e the temporar)
        return data
