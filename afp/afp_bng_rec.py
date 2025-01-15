""" AFP BNG Record """

from struct import pack, unpack

from stream_field_afp import StreamFieldAFP


afp_bng_fields_list = [
    StreamFieldAFP(name="PGrpName", offset=0, length=8, type="CHAR", optional=True, exception='06', range_values=['', ''], meaning=['Name of the page group', '']),
    StreamFieldAFP(name="Triplets", offset=8, length=32753, type="", optional=True, exception='10', range_values=['', '', ''], meaning=['See "BNG Semantics" for', 'triplet applicability.', '']),
    ]
afp_bng_fields = {}
for field in afp_bng_fields_list:
    afp_bng_fields[field.name] = field


class AFP_BNG:

    def __init__(self):
                                        # Offset: Length: Type: Optional: Exception: Range:                Meaning:
        self.PGrpName = None            #      0       8  CHAR  y         '06'                             Name of the page group
        self.Triplets = None            #      8   32753        y         '10'                             See "BNG Semantics" for
                                        #                                                                  triplet applicability.

    def parse(self, data):
        """ Parse the data from a record into the record class fields.

        :param bytes data: Record data
        """
        self.PGrpName, self.Triplets = unpack(f">8s{self.Triplets.len()}s", data)

    def format(self):
        """ Format the data from the record class fields into a record.

        :returns: Record data
        """
        data = pack(f">8s{self.Triplets.len()}s", self.PGrpName, self.Triplets)
        return data
