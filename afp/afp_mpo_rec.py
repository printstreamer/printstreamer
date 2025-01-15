""" AFP MPO Record """

from struct import pack, unpack

from stream_field_afp import StreamFieldAFP


afp_mpo_fields_list = [
    StreamFieldAFP(name="RGLength", offset=0, length=2, type="UBIN", optional=True, exception='\x06', range_values=['11-(n)+1', '', ''], meaning=['Total length of this repeating', 'group', '']),
    StreamFieldAFP(name="Triplets", offset=2, length=32759, type="", optional=True, exception='\x14', range_values=['', '', ''], meaning=['See "MPO Semantics" for', 'triplet applicability.', '']),
    ]
afp_mpo_fields = {}
for field in afp_mpo_fields_list:
    afp_mpo_fields[field.name] = field


class AFP_MPO:

    def __init__(self):
                                        # Offset: Length: Type: Optional: Exception: Range:                Meaning:
        self.RGLength = None            #      0       2  UBIN  y         X'06'      11-(n)+1              Total length of this repeating
                                        #                                                                  group
        self.Triplets = None            #      2   32759        y         X'14'                            See "MPO Semantics" for
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
