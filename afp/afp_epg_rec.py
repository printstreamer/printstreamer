""" AFP EPG Record """

from struct import pack, unpack

from stream_field_afp import StreamFieldAFP


afp_epg_fields_list = [
    StreamFieldAFP(name="PageName", offset=0, length=8, type="CHAR", optional=True, exception='\x02', range_values=['', ''], meaning=['Name of the page', '']),
    StreamFieldAFP(name="Triplets", offset=8, length=32753, type="", optional=True, exception='\x10', range_values=['', '', ''], meaning=['See "EPG Semantics" for', 'triplet applicability.', '']),
    ]
afp_epg_fields = {}
for field in afp_epg_fields_list:
    afp_epg_fields[field.name] = field


class AFP_EPG:

    def __init__(self):
                                        # Offset: Length: Type: Optional: Exception: Range:                Meaning:
        self.PageName = None            #      0       8  CHAR  y         X'02'                            Name of the page
        self.Triplets = None            #      8   32753        y         X'10'                            See "EPG Semantics" for
                                        #                                                                  triplet applicability.

    def parse(self, data):
        """ Parse the data from a record into the record class fields.

        :param bytes data: Record data
        """
        self.PageName, self.Triplets = unpack(f">8s{self.Triplets.len()}s", data)

    def format(self):
        """ Format the data from the record class fields into a record.

        :returns: Record data
        """
        data = pack(f">8s{self.Triplets.len()}s", self.PageName, self.Triplets)
        return data
