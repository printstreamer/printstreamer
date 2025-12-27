""" AFP PTX STO Sequence """

from struct import pack, unpack

from afp_class import AFPClass
from stream_field_afp import StreamFieldAFP


afp_ptx_sto_fields_list = [
    StreamFieldAFP(name="IORNTION", offset=0, length=2, type="CODE", optional=False, range_values=['See', ''], default=True, indicator=True, meaning=['I-axis orientation', '']),
    StreamFieldAFP(name="BORNTION", offset=2, length=2, type="CODE", optional=False, range_values=['See', ''], default=True, indicator=True, meaning=['B-axis orientation', '']),
    ]
afp_ptx_sto_fields = {}
for field in afp_ptx_sto_fields_list:
    afp_ptx_sto_fields[field.name] = field


class AFP_PTX_STO(AFPClass):

    def __init__(self, segment):
        self.segment = segment
        self.document = self.segment.cur_document
        self.page = self.segment.cur_page
                                        # Offset: Length: Type: Range:        Meaning:                  Optional: Def: Ind:
        self.IORNTION = None            #      0       2  CODE  See           I-axis orientation               n    y    y
        self.BORNTION = None            #      2       2  CODE  See           B-axis orientation               n    y    y

    def parse(self, data):
        """ Parse the data from a record into the record class fields.

        :param bytes data: Record data
        """
        pass
        # self.IORNTION, self.BORNTION = unpack(f">2s2s", data)

    def format(self):
        """ Format the data from the record class fields into a record.

        :returns: Record data
        """
        data = pack(f">2s2s", self.IORNTION, self.BORNTION)
        return data
