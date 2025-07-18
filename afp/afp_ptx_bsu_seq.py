""" AFP PTX BSU Sequence """

from struct import pack, unpack

from afp_class import AFPClass
from stream_field_afp import StreamFieldAFP


afp_ptx_bsu_fields_list = [
    StreamFieldAFP(name="LID", offset=0, length=1, type="CODE", optional=False, range_values=["X'00' -", ''], default=False, indicator=False, meaning=['Suppression identifier', '']),
    ]
afp_ptx_bsu_fields = {}
for field in afp_ptx_bsu_fields_list:
    afp_ptx_bsu_fields[field.name] = field


class AFP_PTX_BSU(AFPClass):

    def __init__(self, segment):
        self.segment = segment
        self.document = self.segment.cur_document
        self.page = self.segment.cur_page
                                        # Offset: Length: Type: Range:        Meaning:                  Optional: Def: Ind:
        self.LID = None                 #      0       1  CODE  X'00' -       Suppression identifier           n    n    n

    def parse(self, data):
        """ Parse the data from a record into the record class fields.

        :param bytes data: Record data
        """
        pass
        # self.LID = unpack(f">1s", data)

    def format(self):
        """ Format the data from the record class fields into a record.

        :returns: Record data
        """
        data = pack(f">1s", self.LID)
        return data
