""" AFP PTX RMB Sequence """

from struct import pack, unpack

from afp_class import AFPClass
from stream_field_afp import StreamFieldAFP


afp_ptx_rmb_fields_list = [
    StreamFieldAFP(name="INCRMENT", offset=0, length=2, type="SBIN", optional=True, range_values=["X'8000' -", ''], default=False, indicator=False, meaning=['Increment', '']),
    ]
afp_ptx_rmb_fields = {}
for field in afp_ptx_rmb_fields_list:
    afp_ptx_rmb_fields[field.name] = field


class AFP_PTX_RMB(AFPClass):

    def __init__(self):
                                        # Offset: Length: Type: Range:        Meaning:                  Optional: Def: Ind:
        self.INCRMENT = None            #      0       2  SBIN  X'8000' -     Increment                        y    n    n

    def parse(self, data):
        """ Parse the data from a record into the record class fields.

        :param bytes data: Record data
        """
        self.INCRMENT = unpack(f">h", data)

    def format(self):
        """ Format the data from the record class fields into a record.

        :returns: Record data
        """
        data = pack(f">h", self.INCRMENT)
        return data
