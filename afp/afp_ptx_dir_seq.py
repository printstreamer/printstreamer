""" AFP PTX DIR Sequence """

from struct import pack, unpack

from afp_class import AFPClass
from stream_field_afp import StreamFieldAFP


afp_ptx_dir_fields_list = [
    StreamFieldAFP(name="RLENGTH", offset=0, length=2, type="SBIN", optional=False, range_values=["X'8000' -", ''], default=False, indicator=False, meaning=['Length', '']),
    StreamFieldAFP(name="RWIDTH", offset=2, length=3, type="SBIN", optional=True, range_values=['See', ''], default=True, indicator=True, meaning=['Width', '']),
    ]
afp_ptx_dir_fields = {}
for field in afp_ptx_dir_fields_list:
    afp_ptx_dir_fields[field.name] = field


class AFP_PTX_DIR(AFPClass):

    def __init__(self, segment):
        self.segment = segment
        self.document = self.segment.cur_document
        self.page = self.segment.cur_page
                                        # Offset: Length: Type: Range:        Meaning:                  Optional: Def: Ind:
        self.RLENGTH = None             #      0       2  SBIN  X'8000' -     Length                           n    n    n
        self.RWIDTH = None              #      2       3  SBIN  See           Width                            y    y    y

    def parse(self, data):
        """ Parse the data from a record into the record class fields.

        :param bytes data: Record data
        """
        pass
        # self.RLENGTH, self.RWIDTH = unpack(f">hxh", data)

    def format(self):
        """ Format the data from the record class fields into a record.

        :returns: Record data
        """
        data = pack(f">hxh", self.RLENGTH, self.RWIDTH)
        return data
