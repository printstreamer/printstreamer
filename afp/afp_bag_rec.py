""" AFP BAG Record """

from struct import pack, unpack

from stream_field_afp import StreamFieldAFP


afp_bag_fields_list = [
    StreamFieldAFP(name="AEGName", offset=0, length=8, type="CHAR", optional=True, exception='\x02', range_values=['', '', ''], meaning=['Name of the active', 'environment group', '']),
    StreamFieldAFP(name="Triplets", offset=8, length=32753, type="", optional=True, exception='\x10', range_values=['', '', ''], meaning=['See "BAG Semantics" for', 'triplet applicability.', '']),
    ]
afp_bag_fields = {}
for field in afp_bag_fields_list:
    afp_bag_fields[field.name] = field


class AFP_BAG:

    def __init__(self):
                                        # Offset: Length: Type: Optional: Exception: Range:                Meaning:
        self.AEGName = None             #      0       8  CHAR  y         X'02'                            Name of the active
                                        #                                                                  environment group
        self.Triplets = None            #      8   32753        y         X'10'                            See "BAG Semantics" for
                                        #                                                                  triplet applicability.

    def parse(self, data):
        """ Parse the data from a record into the record class fields.

        :param bytes data: Record data
        """
        self.AEGName, self.Triplets = unpack(f">8s{self.Triplets.len()}s", data)

    def format(self):
        """ Format the data from the record class fields into a record.

        :returns: Record data
        """
        data = pack(f">8s{self.Triplets.len()}s", self.AEGName, self.Triplets)
        return data
