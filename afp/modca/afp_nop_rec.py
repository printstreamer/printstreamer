""" AFP NOP Record """

from struct import pack, unpack

from stream_field_afp import StreamFieldAFP


afp_nop_fields_list = [
    StreamFieldAFP(name="UndfData", offset=0, length=32761, type="UNDF", optional=True, exception='\x00', range_values=['', '', '', ''], meaning=['Up to 32,759 bytes of data', 'with no architectural', 'definition', '']),
    ]
afp_nop_fields = {}
for field in afp_nop_fields_list:
    afp_nop_fields[field.name] = field


class AFP_NOP:

    def __init__(self, segment):
        self.segment = segment
        self.document = self.segment.cur_document
        self.page = self.segment.cur_page
                                        # Offset: Length: Type: Optional: Exception: Range:                Meaning:
        self.UndfData = None            #      0   32761  UNDF  y         X'00'                            Up to 32,759 bytes of data
                                        #                                                                  with no architectural
                                        #                                                                  definition

    def parse(self, data):
        """ Parse the data from a record into the record class fields.

        :param bytes data: Record data
        """
        pass
        # self.UndfData = unpack(f">{self.UndfData.len()}s", data)

    def format(self):
        """ Format the data from the record class fields into a record.

        :returns: Record data
        """
        data = pack(f">{self.UndfData.len()}s", self.UndfData)
        return data
