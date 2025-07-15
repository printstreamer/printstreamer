""" AFP PTX AMB Sequence """

from struct import pack, unpack

from afp_class import AFPClass
from stream_field_afp import StreamFieldAFP


afp_ptx_amb_fields_list = [
    StreamFieldAFP(name="DSPLCMNT", offset=0, length=2, type="SBIN", optional=True, range_values=["X'0000' -", ''], default=False, indicator=False, meaning=['Displacement', '']),
    ]
afp_ptx_amb_fields = {}
for field in afp_ptx_amb_fields_list:
    afp_ptx_amb_fields[field.name] = field


class AFP_PTX_AMB(AFPClass):

    def __init__(self, segment):
        self.segment = segment
        self.document = self.segment.cur_document
        self.page = self.segment.cur_page
                                        # Offset: Length: Type: Range:        Meaning:                  Optional: Def: Ind:
        self.DSPLCMNT = None            #      0       2  SBIN  X'0000' -     Displacement                     y    n    n

    def parse(self, data):
        """ Parse the data from a record into the record class fields.

        :param bytes data: Record data
        """
        self.DSPLCMNT = unpack(f">h", data)

    def format(self):
        """ Format the data from the record class fields into a record.

        :returns: Record data
        """
        data = pack(f">h", self.DSPLCMNT)
        return data
