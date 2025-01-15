""" AFP TLE Record """

from struct import pack, unpack

from stream_field_afp import StreamFieldAFP


afp_tle_fields_list = [
    StreamFieldAFP(name="Triplets", offset=0, length=32761, type="", optional=True, exception='14', range_values=['', '', ''], meaning=['See "TLE Semantics" for', 'triplet applicability.', '']),
    ]
afp_tle_fields = {}
for field in afp_tle_fields_list:
    afp_tle_fields[field.name] = field


class AFP_TLE:

    def __init__(self):
                                        # Offset: Length: Type: Optional: Exception: Range:                Meaning:
        self.Triplets = None            #      0   32761        y         '14'                             See "TLE Semantics" for
                                        #                                                                  triplet applicability.

    def parse(self, data):
        """ Parse the data from a record into the record class fields.

        :param bytes data: Record data
        """
        self.Triplets = unpack(f">{self.Triplets.len()}s", data)

    def format(self):
        """ Format the data from the record class fields into a record.

        :returns: Record data
        """
        data = pack(f">{self.Triplets.len()}s", self.Triplets)
        return data
