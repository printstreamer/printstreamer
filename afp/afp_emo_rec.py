""" AFP EMO Record """

from struct import pack, unpack

from stream_field_afp import StreamFieldAFP


afp_emo_fields_list = [
    StreamFieldAFP(name="OvlyName", offset=0, length=8, type="CHAR", optional=True, exception='\x02', range_values=['', ''], meaning=['Name of the overlay', '']),
    StreamFieldAFP(name="Triplets", offset=8, length=32753, type="", optional=True, exception='\x10', range_values=['', '', ''], meaning=['See "EMO Semantics" for', 'triplet applicability.', '']),
    ]
afp_emo_fields = {}
for field in afp_emo_fields_list:
    afp_emo_fields[field.name] = field


class AFP_EMO:

    def __init__(self):
                                        # Offset: Length: Type: Optional: Exception: Range:                Meaning:
        self.OvlyName = None            #      0       8  CHAR  y         X'02'                            Name of the overlay
        self.Triplets = None            #      8   32753        y         X'10'                            See "EMO Semantics" for
                                        #                                                                  triplet applicability.

    def parse(self, data):
        """ Parse the data from a record into the record class fields.

        :param bytes data: Record data
        """
        self.OvlyName, self.Triplets = unpack(f">8s{self.Triplets.len()}s", data)

    def format(self):
        """ Format the data from the record class fields into a record.

        :returns: Record data
        """
        data = pack(f">8s{self.Triplets.len()}s", self.OvlyName, self.Triplets)
        return data
