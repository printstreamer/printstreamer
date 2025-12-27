""" AFP PTX BLN Sequence """

from struct import pack, unpack

from afp_class import AFPClass
from stream_field_afp import StreamFieldAFP


afp_ptx_bln_fields_list = [
    ]
afp_ptx_bln_fields = {}
for field in afp_ptx_bln_fields_list:
    afp_ptx_bln_fields[field.name] = field


class AFP_PTX_BLN(AFPClass):

    def __init__(self, segment):
        self.segment = segment
        self.document = self.segment.cur_document
        self.page = self.segment.cur_page
                                        # Offset: Length: Type: Range:        Meaning:                  Optional: Def: Ind:
        pass

    def parse(self, data):
        """ Parse the data from a record into the record class fields.

        :param bytes data: Record data
        """
        pass
        # pass

    def format(self):
        """ Format the data from the record class fields into a record.

        :returns: Record data
        """
        return None
