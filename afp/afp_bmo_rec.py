""" AFP BMO Record """

from struct import pack, unpack

from stream_field_afp import StreamFieldAFP


afp_bmo_fields_list = [
    StreamFieldAFP(name="OvlyName", offset=0, length=8, type="CHAR", optional=True, exception='06', range_values=['', ''], meaning=['Name of the overlay', '']),
    StreamFieldAFP(name="Triplets", offset=8, length=32753, type="", optional=True, exception='10', range_values=['', '', ''], meaning=['See "BMO Semantics" for', 'triplet applicability.', '']),
    ]
afp_bmo_fields = {}
for field in afp_bmo_fields_list:
    afp_bmo_fields[field.name] = field


class AFP_BMO:

    def __init__(self, segment):
        self.segment = segment
        self.document = self.segment.cur_document
        self.page = self.segment.cur_page
                                        # Offset: Length: Type: Optional: Exception: Range:                Meaning:
        self.OvlyName = None            #      0       8  CHAR  y         '06'                             Name of the overlay
        self.Triplets = None            #      8   32753        y         '10'                             See "BMO Semantics" for
                                        #                                                                  triplet applicability.

    def parse(self, data):
        """ Parse the data from a record into the record class fields.

        :param bytes data: Record data
        """
        pass
        # self.OvlyName, self.Triplets = unpack(f">8s{self.Triplets.len()}s", data)

    def format(self):
        """ Format the data from the record class fields into a record.

        :returns: Record data
        """
        data = pack(f">8s{self.Triplets.len()}s", self.OvlyName, self.Triplets)
        return data
