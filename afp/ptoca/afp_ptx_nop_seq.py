""" AFP PTX NOP Sequence """

from struct import pack, unpack

from afp_class import AFPClass
from stream_field_afp import StreamFieldAFP


afp_ptx_nop_fields_list = [
    StreamFieldAFP(name="IGNDATA", offset=0, length=253, type="UNDF", optional=True, range_values=['Not', ''], default=False, indicator=False, meaning=['Ignored data', '']),
    ]
afp_ptx_nop_fields = {}
for field in afp_ptx_nop_fields_list:
    afp_ptx_nop_fields[field.name] = field


class AFP_PTX_NOP(AFPClass):

    def __init__(self, segment):
        self.segment = segment
        self.document = self.segment.cur_document
        self.page = self.segment.cur_page
                                        # Offset: Length: Type: Range:        Meaning:                  Optional: Def: Ind:
        self.IGNDATA = None             #      0     253  UNDF  Not           Ignored data                     y    n    n

    def parse(self, data):
        """ Parse the data from a record into the record class fields.

        :param bytes data: Record data
        """
        pass
        # self.IGNDATA = unpack(f">{len(data)}s", data)

    def format(self):
        """ Format the data from the record class fields into a record.

        :returns: Record data
        """
        data = pack(f">{len(self.IGNDATA)}s", self.IGNDATA)
        return data
