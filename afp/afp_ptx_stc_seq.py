""" AFP PTX STC Sequence """

from struct import pack, unpack

from afp_class import AFPClass
from stream_field_afp import StreamFieldAFP


afp_ptx_stc_fields_list = [
    StreamFieldAFP(name="FRGCOLOR See", offset=0, length=2, type="CODE", optional=True, range_values=['', ''], default=True, indicator=True, meaning=['Foreground color', '']),
    StreamFieldAFP(name="PRECSION", offset=2, length=1, type="BITS", optional=True, range_values=["X'00' -", ''], default=True, indicator=True, meaning=['Precision', '']),
    ]
afp_ptx_stc_fields = {}
for field in afp_ptx_stc_fields_list:
    afp_ptx_stc_fields[field.name] = field


class AFP_PTX_STC(AFPClass):

    def __init__(self):
                                        # Offset: Length: Type: Range:        Meaning:                  Optional: Def: Ind:
        self.FRGCOLOR = None            #      0       2  CODE                Foreground color                 y    y    y
        self.PRECSION = None            #      2       1  BITS  X'00' -       Precision                        y    y    y

    def parse(self, data):
        """ Parse the data from a record into the record class fields.

        :param bytes data: Record data
        """
        self.FRGCOLOR, self.PRECSION = unpack(f">2s1s", data)

    def format(self):
        """ Format the data from the record class fields into a record.

        :returns: Record data
        """
        data = pack(f">2s1s", self.FRGCOLOR, self.PRECSION)
        return data
