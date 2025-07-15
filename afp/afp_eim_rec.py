""" AFP EIM Record """

from struct import pack, unpack

from stream_field_afp import StreamFieldAFP


afp_eim_fields_list = [
    StreamFieldAFP(name="IdoName", offset=0, length=8, type="CHAR", optional=True, exception='\x02', range_values=['', ''], meaning=['Name of the image data object', '']),
    StreamFieldAFP(name="Triplets", offset=8, length=32753, type="", optional=True, exception='\x10', range_values=['', '', ''], meaning=['See "EIM Semantics" for', 'triplet applicability.', '']),
    ]
afp_eim_fields = {}
for field in afp_eim_fields_list:
    afp_eim_fields[field.name] = field


class AFP_EIM:

    def __init__(self, segment):
        self.segment = segment
        self.document = self.segment.cur_document
        self.page = self.segment.cur_page
                                        # Offset: Length: Type: Optional: Exception: Range:                Meaning:
        self.IdoName = None             #      0       8  CHAR  y         X'02'                            Name of the image data object
        self.Triplets = None            #      8   32753        y         X'10'                            See "EIM Semantics" for
                                        #                                                                  triplet applicability.

    def parse(self, data):
        """ Parse the data from a record into the record class fields.

        :param bytes data: Record data
        """
        pass
        # self.IdoName, self.Triplets = unpack(f">8s{self.Triplets.len()}s", data)

    def format(self):
        """ Format the data from the record class fields into a record.

        :returns: Record data
        """
        data = pack(f">8s{self.Triplets.len()}s", self.IdoName, self.Triplets)
        return data
