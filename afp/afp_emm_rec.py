""" AFP EMM Record """

from struct import pack, unpack

from stream_field_afp import StreamFieldAFP


afp_emm_fields_list = [
    StreamFieldAFP(name="MMName", offset=0, length=8, type="CHAR", optional=True, exception='\x02', range_values=['', ''], meaning=['Name of the medium map', '']),
    ]
afp_emm_fields = {}
for field in afp_emm_fields_list:
    afp_emm_fields[field.name] = field


class AFP_EMM:

    def __init__(self, segment):
        self.segment = segment
        self.document = self.segment.cur_document
        self.page = self.segment.cur_page
                                        # Offset: Length: Type: Optional: Exception: Range:                Meaning:
        self.MMName = None              #      0       8  CHAR  y         X'02'                            Name of the medium map

    def parse(self, data):
        """ Parse the data from a record into the record class fields.

        :param bytes data: Record data
        """
        pass
        # self.MMName = unpack(f">8s", data)

    def format(self):
        """ Format the data from the record class fields into a record.

        :returns: Record data
        """
        data = pack(f">8s", self.MMName)
        return data
