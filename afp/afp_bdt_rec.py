""" AFP BDT Record """

from struct import pack, unpack

from stream_field_afp import StreamFieldAFP


afp_bdt_fields_list = [
    StreamFieldAFP(name="DocName", offset=0, length=8, type="CHAR", optional=True, exception='06', range_values=['', ''], meaning=['Name of the document', '']),
    StreamFieldAFP(name="Reserved_1", offset=8, length=2, type="", optional=True, exception='06', range_values=['', ''], meaning=['Reserved; must be binary zero', '']),
    StreamFieldAFP(name="Triplets", offset=10, length=32751, type="", optional=True, exception='14', range_values=['', '', ''], meaning=['See "BDT Semantics" for', 'triplet applicability.', '']),
    ]
afp_bdt_fields = {}
for field in afp_bdt_fields_list:
    afp_bdt_fields[field.name] = field


class AFP_BDT:

    def __init__(self):
                                        # Offset: Length: Type: Optional: Exception: Range:                Meaning:
        self.DocName = None             #      0       8  CHAR  y         '06'                             Name of the document
        self.Reserved_1 = None          #      8       2        y         '06'                             Reserved; must be binary zero
        self.Triplets = None            #     10   32751        y         '14'                             See "BDT Semantics" for
                                        #                                                                  triplet applicability.

    def parse(self, data):
        """ Parse the data from a record into the record class fields.

        :param bytes data: Record data
        """
        self.DocName, self.Reserved_1, self.Triplets = unpack(f">8s2s{self.Triplets.len()}s", data)

    def format(self):
        """ Format the data from the record class fields into a record.

        :returns: Record data
        """
        data = pack(f">8s2s{self.Triplets.len()}s", self.DocName, self.Reserved_1, self.Triplets)
        return data
