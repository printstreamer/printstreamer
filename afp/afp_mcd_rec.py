""" AFP MCD Record """

from struct import pack, unpack

from stream_field_afp import StreamFieldAFP


afp_mcd_fields_list = [
    StreamFieldAFP(name="RGLength", offset=0, length=2, type="UBIN", optional=True, exception='\x06', range_values=['5', '', ''], meaning=['Total length of this repeating', 'group', '']),
    StreamFieldAFP(name="Triplets", offset=2, length=3, type="", optional=False, exception='\x14', range_values=['', ''], meaning=['Mapping Option triplet', '']),
    ]
afp_mcd_fields = {}
for field in afp_mcd_fields_list:
    afp_mcd_fields[field.name] = field


class AFP_MCD:

    def __init__(self, segment):
        self.segment = segment
        self.document = self.segment.cur_document
        self.page = self.segment.cur_page
                                        # Offset: Length: Type: Optional: Exception: Range:                Meaning:
        self.RGLength = None            #      0       2  UBIN  y         X'06'      5                     Total length of this repeating
                                        #                                                                  group
        self.Triplets = None            #      2       3        n         X'14'                            Mapping Option triplet

    def parse(self, data):
        """ Parse the data from a record into the record class fields.

        :param bytes data: Record data
        """
        pass
        # self.RGLength, self.Triplets = unpack(f">H{self.Triplets.len()}s", data)

    def format(self):
        """ Format the data from the record class fields into a record.

        :returns: Record data
        """
        data = pack(f">H{self.Triplets.len()}s", self.RGLength, self.Triplets)
        return data
