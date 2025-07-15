""" AFP BOC Record """

from struct import pack, unpack

from stream_field_afp import StreamFieldAFP


afp_boc_fields_list = [
    StreamFieldAFP(name="ObjCName", offset=0, length=8, type="CHAR", optional=False, exception='\x06', range_values=['', ''], meaning=['Name of the object container', '']),
    StreamFieldAFP(name="Triplets", offset=8, length=32753, type="", optional=True, exception='\x14', range_values=['', '', ''], meaning=['See "BOC Semantics" for', 'triplet applicability.', '']),
    ]
afp_boc_fields = {}
for field in afp_boc_fields_list:
    afp_boc_fields[field.name] = field


class AFP_BOC:

    def __init__(self, segment):
        self.segment = segment
        self.document = self.segment.cur_document
        self.page = self.segment.cur_page
                                        # Offset: Length: Type: Optional: Exception: Range:                Meaning:
        self.ObjCName = None            #      0       8  CHAR  n         X'06'                            Name of the object container
        self.Triplets = None            #      8   32753        y         X'14'                            See "BOC Semantics" for
                                        #                                                                  triplet applicability.

    def parse(self, data):
        """ Parse the data from a record into the record class fields.

        :param bytes data: Record data
        """
        pass
        # self.ObjCName, self.Triplets = unpack(f">8s{self.Triplets.len()}s", data)

    def format(self):
        """ Format the data from the record class fields into a record.

        :returns: Record data
        """
        data = pack(f">8s{self.Triplets.len()}s", self.ObjCName, self.Triplets)
        return data
