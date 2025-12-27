""" AFP EAG Record """

from struct import pack, unpack

from stream_field_afp import StreamFieldAFP


afp_eag_fields_list = [
    StreamFieldAFP(name="AEGName", offset=0, length=8, type="CHAR", optional=True, exception='\x02', range_values=['', '', ''], meaning=['Name of the active', 'environment group', '']),
    ]
afp_eag_fields = {}
for field in afp_eag_fields_list:
    afp_eag_fields[field.name] = field


class AFP_EAG:

    def __init__(self, segment):
        self.segment = segment
        self.document = self.segment.cur_document
        self.page = self.segment.cur_page
                                        # Offset: Length: Type: Optional: Exception: Range:                Meaning:
        self.AEGName = None             #      0       8  CHAR  y         X'02'                            Name of the active
                                        #                                                                  environment group

    def parse(self, data):
        """ Parse the data from a record into the record class fields.

        :param bytes data: Record data
        """
        pass
        # self.AEGName = unpack(f">8s", data)

    def format(self):
        """ Format the data from the record class fields into a record.

        :returns: Record data
        """
        data = pack(f">8s", self.AEGName)
        return data
