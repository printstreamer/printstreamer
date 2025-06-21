""" AFP PTX SIA Sequence """

from struct import pack, unpack

from afp_class import AFPClass
from stream_field_afp import StreamFieldAFP


afp_ptx_sia_fields_list = [
    StreamFieldAFP(name="ADJSTMNT", offset=0, length=2, type="SBIN", optional=False, range_values=["X'0000' -", ''], default=True, indicator=True, meaning=['Adjustment', '']),
    StreamFieldAFP(name="DIRCTION", offset=2, length=1, type="CODE", optional=True, range_values=["X'00' -", ''], default=True, indicator=True, meaning=['Direction', '']),
    ]
afp_ptx_sia_fields = {}
for field in afp_ptx_sia_fields_list:
    afp_ptx_sia_fields[field.name] = field


class AFP_PTX_SIA(AFPClass):

    def __init__(self):
                                        # Offset: Length: Type: Range:        Meaning:                  Optional: Def: Ind:
        self.ADJSTMNT = None            #      0       2  SBIN  X'0000' -     Adjustment                       n    y    y
        self.DIRCTION = None            #      2       1  CODE  X'00' -       Direction                        y    y    y

    def parse(self, data):
        """ Parse the data from a record into the record class fields.

        :param bytes data: Record data
        """
        self.ADJSTMNT, self.DIRCTION = unpack(f">h1s", data)

    def format(self):
        """ Format the data from the record class fields into a record.

        :returns: Record data
        """
        data = pack(f">h1s", self.ADJSTMNT, self.DIRCTION)
        return data
