""" AFP BPS Record """

from struct import pack, unpack

from stream_field_afp import StreamFieldAFP


afp_bps_fields_list = [
    StreamFieldAFP(name="PsegName", offset=0, length=8, type="CHAR", optional=False, exception='\x06', range_values=['', ''], meaning=['Name of the page segment', '']),
    StreamFieldAFP(name="Triplets", offset=8, length=32753, type="", optional=True, exception='\x10', range_values=['', '', ''], meaning=['See "BPS Semantics" for triplet', 'applicability.', '']),
    ]
afp_bps_fields = {}
for field in afp_bps_fields_list:
    afp_bps_fields[field.name] = field


class AFP_BPS:

    def __init__(self):
                                        # Offset: Length: Type: Optional: Exception: Range:                Meaning:
        self.PsegName = None            #      0       8  CHAR  n         X'06'                            Name of the page segment
        self.Triplets = None            #      8   32753        y         X'10'                            See "BPS Semantics" for triplet
                                        #                                                                  applicability.

    def parse(self, data):
        """ Parse the data from a record into the record class fields.

        :param bytes data: Record data
        """
        self.PsegName, self.Triplets = unpack(f">8s{self.Triplets.len()}s", data)

    def format(self):
        """ Format the data from the record class fields into a record.

        :returns: Record data
        """
        data = pack(f">8s{self.Triplets.len()}s", self.PsegName, self.Triplets)
        return data
