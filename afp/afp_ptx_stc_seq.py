""" AFP PTX STC Sequence """

from struct import pack, unpack

from stream_field_afp import StreamFieldAFP


afp_ptx_stc_fields_list = [
    StreamFieldAFP(name="PREFIX", offset=0, length=1, type="CODE", optional=True, range_values=["X'2B'", ''], default=False, indicator=False, meaning=['Control Sequence', '']),
    StreamFieldAFP(name="CLASS", offset=1, length=1, type="CODE", optional=True, range_values=["X'D3'", ''], default=False, indicator=False, meaning=['Control sequence class', '']),
    StreamFieldAFP(name="LENGTH", offset=2, length=1, type="UBIN", optional=True, range_values=['4-5', ''], default=False, indicator=False, meaning=['Control sequence', '']),
    StreamFieldAFP(name="TYPE", offset=3, length=1, type="CODE", optional=True, range_values=["X'74' -", ''], default=False, indicator=False, meaning=['Control sequence', '']),
    StreamFieldAFP(name="FRGCOLOR See", offset=4, length=2, type="CODE", optional=True, range_values=['', ''], default=True, indicator=True, meaning=['Foreground color', '']),
    StreamFieldAFP(name="PRECSION", offset=6, length=1, type="BITS", optional=True, range_values=["X'00' -", ''], default=True, indicator=True, meaning=['Precision', '']),
    StreamFieldAFP(name="actly like tho", offset=6, length=1, type="treated ex", optional=True, range_values=['se colors. A c', ''], default=True, indicator=True, meaning=["olor attribute value of X'F", '']),
    ]
afp_ptx_stc_fields = {}
for field in afp_ptx_stc_fields_list:
    afp_ptx_stc_fields[field.name] = field


class AFP_PTX_STC:

    def __init__(self):
                                        # Offset: Length: Type: Range:        Meaning:                  Optional: Def: Ind:
        self.PREFIX = None              #      0       1  CODE  X'2B'         Control Sequence                 y    n    n
        self.CLASS = None               #      1       1  CODE  X'D3'         Control sequence class           y    n    n
        self.LENGTH = None              #      2       1  UBIN  4-5           Control sequence                 y    n    n
        self.TYPE = None                #      3       1  CODE  X'74' -       Control sequence                 y    n    n
        self.FRGCOLOR See = None        #      4       2  CODE                Foreground color                 y    y    y
        self.PRECSION = None            #      6       1  BITS  X'00' -       Precision                        y    y    y
        self.actly like tho = None      #      6       1  trea  se colors. A  olor attribute value of X        y    y    y

    def parse(self, data):
        """ Parse the data from a record into the record class fields.

        :param bytes data: Record data
        """
        self.PREFIX, self.CLASS, self.LENGTH, self.TYPE, self.FRGCOLOR See, self.PRECSION, self.actly like tho = unpack(f">1s1sB1s2s1s", data)

    def format(self):
        """ Format the data from the record class fields into a record.

        :returns: Record data
        """
        data = pack(f">1s1sB1s2s1s", self.PREFIX, self.CLASS, self.LENGTH, self.TYPE, self.FRGCOLOR See, self.PRECSION, self.actly like tho)
        return data
