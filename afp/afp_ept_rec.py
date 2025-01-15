""" AFP EPT Record """

from struct import pack, unpack

from stream_field_afp import StreamFieldAFP


afp_ept_fields_list = [
    StreamFieldAFP(name="PTdoName", offset=0, length=8, type="CHAR", optional=True, exception='02', range_values=['', '', ''], meaning=['Name of the presentation text', 'data object', '']),
    StreamFieldAFP(name="Triplets", offset=8, length=32753, type="", optional=True, exception='10', range_values=['', '', ''], meaning=['See "EPT Semantics" for', 'triplet applicability.', '']),
    ]
afp_ept_fields = {}
for field in afp_ept_fields_list:
    afp_ept_fields[field.name] = field


class AFP_EPT:

    def __init__(self):
                                        # Offset: Length: Type: Optional: Exception: Range:                Meaning:
        self.PTdoName = None            #      0       8  CHAR  y         '02'                             Name of the presentation text
                                        #                                                                  data object
        self.Triplets = None            #      8   32753        y         '10'                             See "EPT Semantics" for
                                        #                                                                  triplet applicability.

    def parse(self, data):
        """ Parse the data from a record into the record class fields.

        :param bytes data: Record data
        """
        self.PTdoName, self.Triplets = unpack(f">8s{self.Triplets.len()}s", data)

    def format(self):
        """ Format the data from the record class fields into a record.

        :returns: Record data
        """
        data = pack(f">8s{self.Triplets.len()}s", self.PTdoName, self.Triplets)
        return data
