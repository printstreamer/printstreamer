""" AFP BCA Record """

from struct import pack, unpack

from stream_field_afp import StreamFieldAFP


afp_bca_fields_list = [
    StreamFieldAFP(name="CATName", offset=0, length=8, type="CHAR", optional=True, exception='\x06', range_values=['', '', ''], meaning=['Name of the color attribute', 'table', '']),
    StreamFieldAFP(name="Triplets", offset=8, length=32753, type="", optional=True, exception='\x10', range_values=['', '', ''], meaning=['See "BCA Semantics" for', 'triplet applicability.', '']),
    ]
afp_bca_fields = {}
for field in afp_bca_fields_list:
    afp_bca_fields[field.name] = field


class AFP_BCA:

    def __init__(self, segment):
        self.segment = segment
        self.document = self.segment.cur_document
        self.page = self.segment.cur_page
                                        # Offset: Length: Type: Optional: Exception: Range:                Meaning:
        self.CATName = None             #      0       8  CHAR  y         X'06'                            Name of the color attribute
                                        #                                                                  table
        self.Triplets = None            #      8   32753        y         X'10'                            See "BCA Semantics" for
                                        #                                                                  triplet applicability.

    def parse(self, data):
        """ Parse the data from a record into the record class fields.

        :param bytes data: Record data
        """
        pass
        # self.CATName, self.Triplets = unpack(f">8s{self.Triplets.len()}s", data)

    def format(self):
        """ Format the data from the record class fields into a record.

        :returns: Record data
        """
        data = pack(f">8s{self.Triplets.len()}s", self.CATName, self.Triplets)
        return data
