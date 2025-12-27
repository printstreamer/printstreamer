""" AFP PTX RPS Sequence """

from struct import pack, unpack

from afp_class import AFPClass
from stream_field_afp import StreamFieldAFP


afp_ptx_rps_fields_list = [
    StreamFieldAFP(name="RLENGTH", offset=0, length=2, type="UBIN", optional=True, range_values=['0-32767', ''], default=False, indicator=False, meaning=['Repeat length', '']),
    StreamFieldAFP(name="RPTDATA", offset=2, length=251, type="CHAR", optional=True, range_values=['Not', ''], default=False, indicator=False, meaning=['Repeated data', '']),
    ]
afp_ptx_rps_fields = {}
for field in afp_ptx_rps_fields_list:
    afp_ptx_rps_fields[field.name] = field


class AFP_PTX_RPS(AFPClass):

    def __init__(self, segment):
        self.segment = segment
        self.document = self.segment.cur_document
        self.page = self.segment.cur_page
                                        # Offset: Length: Type: Range:        Meaning:                  Optional: Def: Ind:
        self.RLENGTH = None             #      0       2  UBIN  0-32767       Repeat length                    y    n    n
        self.RPTDATA = None             #      2     251  CHAR  Not           Repeated data                    y    n    n

    def parse(self, data):
        """ Parse the data from a record into the record class fields.

        :param bytes data: Record data
        """
        pass
        # self.RLENGTH, self.RPTDATA = unpack(f">H{len(data)}s", data)

    def format(self):
        """ Format the data from the record class fields into a record.

        :returns: Record data
        """
        data = pack(f">H{len(self.RPTDATA)}s", self.RLENGTH, self.RPTDATA)
        return data
