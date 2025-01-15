""" AFP PMC Record """

from struct import pack, unpack

from stream_field_afp import StreamFieldAFP


afp_pmc_fields_list = [
    StreamFieldAFP(name="PMCid", offset=0, length=1, type="CODE", optional=True, exception='\x06', range_values=['0-127', '', ''], meaning=['Page Modification Control', 'identifier', '']),
    StreamFieldAFP(name="Reserved_1", offset=1, length=1, type="", optional=False, exception='\x06', range_values=['', ''], meaning=['Reserved; must be zero', '']),
    StreamFieldAFP(name="Triplets", offset=2, length=32759, type="", optional=True, exception='\x10', range_values=['', '', ''], meaning=['See "PMC Semantics" for', 'triplet applicability.', '']),
    ]
afp_pmc_fields = {}
for field in afp_pmc_fields_list:
    afp_pmc_fields[field.name] = field


class AFP_PMC:

    def __init__(self):
                                        # Offset: Length: Type: Optional: Exception: Range:                Meaning:
        self.PMCid = None               #      0       1  CODE  y         X'06'      0-127                 Page Modification Control
                                        #                                                                  identifier
        self.Reserved_1 = None          #      1       1        n         X'06'                            Reserved; must be zero
        self.Triplets = None            #      2   32759        y         X'10'                            See "PMC Semantics" for
                                        #                                                                  triplet applicability.

    def parse(self, data):
        """ Parse the data from a record into the record class fields.

        :param bytes data: Record data
        """
        self.PMCid, self.Reserved_1, self.Triplets = unpack(f">1s1s{self.Triplets.len()}s", data)

    def format(self):
        """ Format the data from the record class fields into a record.

        :returns: Record data
        """
        data = pack(f">1s1s{self.Triplets.len()}s", self.PMCid, self.Reserved_1, self.Triplets)
        return data
