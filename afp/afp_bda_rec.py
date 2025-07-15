""" AFP BDA Record """

from struct import pack, unpack

from stream_field_afp import StreamFieldAFP


afp_bda_fields_list = [
    StreamFieldAFP(name="BCOCAdat", offset=0, length=32761, type="UNDF", optional=True, exception='\x00', range_values=['', '', ''], meaning=['Up to 32759 bytes of', 'BCOCA-defined data', '']),
    ]
afp_bda_fields = {}
for field in afp_bda_fields_list:
    afp_bda_fields[field.name] = field


class AFP_BDA:

    def __init__(self, segment):
        self.segment = segment
        self.document = self.segment.cur_document
        self.page = self.segment.cur_page
                                        # Offset: Length: Type: Optional: Exception: Range:                Meaning:
        self.BCOCAdat = None            #      0   32761  UNDF  y         X'00'                            Up to 32759 bytes of
                                        #                                                                  BCOCA-defined data

    def parse(self, data):
        """ Parse the data from a record into the record class fields.

        :param bytes data: Record data
        """
        pass
        # self.BCOCAdat = unpack(f">{self.BCOCAdat.len()}s", data)

    def format(self):
        """ Format the data from the record class fields into a record.

        :returns: Record data
        """
        data = pack(f">{self.BCOCAdat.len()}s", self.BCOCAdat)
        return data
