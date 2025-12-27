""" AFP CDD Record """

from struct import pack, unpack

from stream_field_afp import StreamFieldAFP


afp_cdd_fields_list = [
    StreamFieldAFP(name="Reserved_1", offset=0, length=12, type="", optional=True, exception='\x06', range_values=['', '', '', ''], meaning=['Retired parameters; see', '"Retired Parameters" on page', '515', '']),
    StreamFieldAFP(name="Triplets", offset=12, length=32749, type="", optional=True, exception='\x00', range_values=['', '', ''], meaning=['See "CDD Semantics" for', 'triplet applicability.', '']),
    ]
afp_cdd_fields = {}
for field in afp_cdd_fields_list:
    afp_cdd_fields[field.name] = field


class AFP_CDD:

    def __init__(self, segment):
        self.segment = segment
        self.document = self.segment.cur_document
        self.page = self.segment.cur_page
                                        # Offset: Length: Type: Optional: Exception: Range:                Meaning:
        self.Reserved_1 = None          #      0      12        y         X'06'                            Retired parameters; see
                                        #                                                                  "Retired Parameters" on page
                                        #                                                                  515
        self.Triplets = None            #     12   32749        y         X'00'                            See "CDD Semantics" for
                                        #                                                                  triplet applicability.

    def parse(self, data):
        """ Parse the data from a record into the record class fields.

        :param bytes data: Record data
        """
        pass
        # self.Reserved_1, self.Triplets = unpack(f">12s{self.Triplets.len()}s", data)

    def format(self):
        """ Format the data from the record class fields into a record.

        :returns: Record data
        """
        data = pack(f">12s{self.Triplets.len()}s", self.Reserved_1, self.Triplets)
        return data
