""" AFP EBC Record """

from struct import pack, unpack

from stream_field_afp import StreamFieldAFP


afp_ebc_fields_list = [
    StreamFieldAFP(name="BCdoName", offset=0, length=8, type="CHAR", optional=True, exception='\x02', range_values=['', '', ''], meaning=['Name of the bar code data', 'object', '']),
    StreamFieldAFP(name="Triplets", offset=8, length=32753, type="", optional=True, exception='\x10', range_values=['', '', ''], meaning=['See "EBC Semantics" for', 'triplet applicability.', '']),
    ]
afp_ebc_fields = {}
for field in afp_ebc_fields_list:
    afp_ebc_fields[field.name] = field


class AFP_EBC:

    def __init__(self, segment):
        self.segment = segment
        self.document = self.segment.cur_document
        self.page = self.segment.cur_page
                                        # Offset: Length: Type: Optional: Exception: Range:                Meaning:
        self.BCdoName = None            #      0       8  CHAR  y         X'02'                            Name of the bar code data
                                        #                                                                  object
        self.Triplets = None            #      8   32753        y         X'10'                            See "EBC Semantics" for
                                        #                                                                  triplet applicability.

    def parse(self, data):
        """ Parse the data from a record into the record class fields.

        :param bytes data: Record data
        """
        pass
        # self.BCdoName, self.Triplets = unpack(f">8s{self.Triplets.len()}s", data)

    def format(self):
        """ Format the data from the record class fields into a record.

        :returns: Record data
        """
        data = pack(f">8s{self.Triplets.len()}s", self.BCdoName, self.Triplets)
        return data
