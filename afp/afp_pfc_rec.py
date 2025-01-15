""" AFP PFC Record """

from struct import pack, unpack

from stream_field_afp import StreamFieldAFP


afp_pfc_fields_list = [
    StreamFieldAFP(name="Reserved_1", offset=0, length=1, type="", optional=False, exception='\x06', range_values=['', ''], meaning=['Reserved; must be zero', '']),
    StreamFieldAFP(name="PFCFlgs", offset=1, length=1, type="BITS", optional=False, exception='\x06', range_values=['', ''], meaning=['Flags', '']),
    StreamFieldAFP(name="Reserved_2", offset=2, length=2, type="", optional=False, exception='\x06', range_values=['', ''], meaning=['Reserved; must be zero', '']),
    StreamFieldAFP(name="Triplets", offset=4, length=32757, type="", optional=True, exception='\x10', range_values=['', '', ''], meaning=['See "PFC Semantics" for', 'triplet applicability.', '']),
    ]
afp_pfc_fields = {}
for field in afp_pfc_fields_list:
    afp_pfc_fields[field.name] = field


class AFP_PFC:

    def __init__(self):
                                        # Offset: Length: Type: Optional: Exception: Range:                Meaning:
        self.Reserved_1 = None          #      0       1        n         X'06'                            Reserved; must be zero
        self.PFCFlgs = None             #      1       1  BITS  n         X'06'                            Flags
        self.Reserved_2 = None          #      2       2        n         X'06'                            Reserved; must be zero
        self.Triplets = None            #      4   32757        y         X'10'                            See "PFC Semantics" for
                                        #                                                                  triplet applicability.

    def parse(self, data):
        """ Parse the data from a record into the record class fields.

        :param bytes data: Record data
        """
        self.Reserved_1, self.PFCFlgs, self.Reserved_2, self.Triplets = unpack(f">1s1s2s{self.Triplets.len()}s", data)

    def format(self):
        """ Format the data from the record class fields into a record.

        :returns: Record data
        """
        data = pack(f">1s1s2s{self.Triplets.len()}s", self.Reserved_1, self.PFCFlgs, self.Reserved_2, self.Triplets)
        return data
