""" AFP BDG Record """

from struct import pack, unpack

from stream_field_afp import StreamFieldAFP


afp_bdg_fields_list = [
    StreamFieldAFP(name="DEGName", offset=0, length=8, type="CHAR", optional=True, exception='02', range_values=['', '', ''], meaning=['Name of the document', 'environment group', '']),
    StreamFieldAFP(name="Triplets", offset=8, length=32753, type="", optional=True, exception='10', range_values=['', '', ''], meaning=['See "BDG Semantics" for', 'triplet applicability.', '']),
    ]
afp_bdg_fields = {}
for field in afp_bdg_fields_list:
    afp_bdg_fields[field.name] = field


class AFP_BDG:

    def __init__(self, segment):
        self.segment = segment
        self.document = self.segment.cur_document
        self.page = self.segment.cur_page
                                        # Offset: Length: Type: Optional: Exception: Range:                Meaning:
        self.DEGName = None             #      0       8  CHAR  y         '02'                             Name of the document
                                        #                                                                  environment group
        self.Triplets = None            #      8   32753        y         '10'                             See "BDG Semantics" for
                                        #                                                                  triplet applicability.

    def parse(self, data):
        """ Parse the data from a record into the record class fields.

        :param bytes data: Record data
        """
        pass
        # self.DEGName, self.Triplets = unpack(f">8s{self.Triplets.len()}s", data)

    def format(self):
        """ Format the data from the record class fields into a record.

        :returns: Record data
        """
        data = pack(f">8s{self.Triplets.len()}s", self.DEGName, self.Triplets)
        return data
