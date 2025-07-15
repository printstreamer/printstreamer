""" AFP CAT Record """

from struct import pack, unpack

from stream_field_afp import StreamFieldAFP


afp_cat_fields_list = [
    StreamFieldAFP(name="CATData", offset=0, length=32761, type="UNDF", optional=True, exception='\x00', range_values=['', '', ''], meaning=['Up to 32759 bytes of color', 'table data', '']),
    ]
afp_cat_fields = {}
for field in afp_cat_fields_list:
    afp_cat_fields[field.name] = field


class AFP_CAT:

    def __init__(self, segment):
        self.segment = segment
        self.document = self.segment.cur_document
        self.page = self.segment.cur_page
                                        # Offset: Length: Type: Optional: Exception: Range:                Meaning:
        self.CATData = None             #      0   32761  UNDF  y         X'00'                            Up to 32759 bytes of color
                                        #                                                                  table data

    def parse(self, data):
        """ Parse the data from a record into the record class fields.

        :param bytes data: Record data
        """
        pass
        # self.CATData = unpack(f">{self.CATData.len()}s", data)

    def format(self):
        """ Format the data from the record class fields into a record.

        :returns: Record data
        """
        data = pack(f">{self.CATData.len()}s", self.CATData)
        return data
