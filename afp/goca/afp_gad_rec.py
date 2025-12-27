""" AFP GAD Record """

from struct import pack, unpack

from stream_field_afp import StreamFieldAFP


afp_gad_fields_list = [
    StreamFieldAFP(name="GOCAdat", offset=0, length=8, type="UNDF", optional=True, exception='\x00', range_values=['', '', ''], meaning=['Up to 32759 bytes of', 'GOCA-defined data', '']),
    ]
afp_gad_fields = {}
for field in afp_gad_fields_list:
    afp_gad_fields[field.name] = field


class AFP_GAD:

    def __init__(self, segment):
        self.segment = segment
        self.document = self.segment.cur_document
        self.page = self.segment.cur_page
                                        # Offset: Length: Type: Optional: Exception: Range:                Meaning:
        self.GOCAdat = None             #      0       8  UNDF  y         X'00'                            Up to 32759 bytes of
                                        #                                                                  GOCA-defined data

    def parse(self, data):
        """ Parse the data from a record into the record class fields.

        :param bytes data: Record data
        """
        pass
        # self.GOCAdat = unpack(f">8s", data)

    def format(self):
        """ Format the data from the record class fields into a record.

        :returns: Record data
        """
        data = pack(f">8s", self.GOCAdat)
        return data
