""" AFP PTX OVS Sequence """

from struct import pack, unpack

from afp_class import AFPClass
from stream_field_afp import StreamFieldAFP


afp_ptx_ovs_fields_list = [
    StreamFieldAFP(name="BYPSIDEN", offset=0, length=1, type="BITS", optional=False, range_values=['See', ''], default=True, indicator=True, meaning=['Bypass identifiers', '']),
    StreamFieldAFP(name="OVERCHAR", offset=1, length=2, type="CODE", optional=False, range_values=["X'0000' -", ''], default=False, indicator=False, meaning=['Overstrike character', '']),
    ]
afp_ptx_ovs_fields = {}
for field in afp_ptx_ovs_fields_list:
    afp_ptx_ovs_fields[field.name] = field


class AFP_PTX_OVS(AFPClass):

    def __init__(self, segment):
        self.segment = segment
        self.document = self.segment.cur_document
        self.page = self.segment.cur_page
                                        # Offset: Length: Type: Range:        Meaning:                  Optional: Def: Ind:
        self.BYPSIDEN = None            #      0       1  BITS  See           Bypass identifiers               n    y    y
        self.OVERCHAR = None            #      1       2  CODE  X'0000' -     Overstrike character             n    n    n

    def parse(self, data):
        """ Parse the data from a record into the record class fields.

        :param bytes data: Record data
        """
        pass
        # self.BYPSIDEN, self.OVERCHAR = unpack(f">1s2s", data)

    def format(self):
        """ Format the data from the record class fields into a record.

        :returns: Record data
        """
        data = pack(f">1s2s", self.BYPSIDEN, self.OVERCHAR)
        return data
