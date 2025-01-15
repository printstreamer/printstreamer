""" AFP MMT Record """

from struct import pack, unpack

from stream_field_afp import StreamFieldAFP


afp_mmt_fields_list = [
    StreamFieldAFP(name="RGLength", offset=0, length=2, type="UBIN", optional=True, exception='\x06', range_values=['14-(n+1)', '', ''], meaning=['Total length of this repeating', 'group', '']),
    StreamFieldAFP(name="Triplets", offset=8, length=32753, type="", optional=True, exception='\x14', range_values=['', '', ''], meaning=['See "MMT Semantics" for', 'triplet applicability.', '']),
    ]
afp_mmt_fields = {}
for field in afp_mmt_fields_list:
    afp_mmt_fields[field.name] = field


class AFP_MMT:

    def __init__(self):
                                        # Offset: Length: Type: Optional: Exception: Range:                Meaning:
        self.RGLength = None            #      0       2  UBIN  y         X'06'      14-(n+1)              Total length of this repeating
                                        #                                                                  group
        self.Triplets = None            #      8   32753        y         X'14'                            See "MMT Semantics" for
                                        #                                                                  triplet applicability.

    def parse(self, data):
        """ Parse the data from a record into the record class fields.

        :param bytes data: Record data
        """
        self.RGLength, self.Triplets = unpack(f">H{self.Triplets.len()}s", data)

    def format(self):
        """ Format the data from the record class fields into a record.

        :returns: Record data
        """
        data = pack(f">H{self.Triplets.len()}s", self.RGLength, self.Triplets)
        return data
