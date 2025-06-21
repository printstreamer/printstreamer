""" AFP PTX TBM Sequence """

from struct import pack, unpack

from afp_class import AFPClass
from stream_field_afp import StreamFieldAFP


afp_ptx_tbm_fields_list = [
    StreamFieldAFP(name="DIRCTION", offset=0, length=1, type="CODE", optional=True, range_values=["X'00' -", ''], default=True, indicator=True, meaning=['Direction', '']),
    StreamFieldAFP(name="PRECSION", offset=1, length=1, type="BITS", optional=True, range_values=["X'00' -", ''], default=True, indicator=True, meaning=['Precision', '']),
    StreamFieldAFP(name="INCRMENT", offset=2, length=2, type="SBIN", optional=True, range_values=["X'0000' -", ''], default=True, indicator=True, meaning=['Temporary baseline', '']),
    ]
afp_ptx_tbm_fields = {}
for field in afp_ptx_tbm_fields_list:
    afp_ptx_tbm_fields[field.name] = field


class AFP_PTX_TBM(AFPClass):

    def __init__(self):
                                        # Offset: Length: Type: Range:        Meaning:                  Optional: Def: Ind:
        self.DIRCTION = None            #      0       1  CODE  X'00' -       Direction                        y    y    y
        self.PRECSION = None            #      1       1  BITS  X'00' -       Precision                        y    y    y
        self.INCRMENT = None            #      2       2  SBIN  X'0000' -     Temporary baseline               y    y    y

    def parse(self, data):
        """ Parse the data from a record into the record class fields.

        :param bytes data: Record data
        """
        self.DIRCTION, self.PRECSION, self.INCRMENT = unpack(f">1s1sh", data)

    def format(self):
        """ Format the data from the record class fields into a record.

        :returns: Record data
        """
        data = pack(f">1s1sh", self.DIRCTION, self.PRECSION, self.INCRMENT)
        return data
