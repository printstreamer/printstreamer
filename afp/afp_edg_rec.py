""" AFP EDG Record """

from struct import pack, unpack

from stream_field_afp import StreamFieldAFP


afp_edg_fields_list = [
    StreamFieldAFP(name="DEGName", offset=0, length=8, type="CHAR", optional=True, exception='\x02', range_values=['', '', ''], meaning=['Name of the document', 'environment group', '']),
    ]
afp_edg_fields = {}
for field in afp_edg_fields_list:
    afp_edg_fields[field.name] = field


class AFP_EDG:

    def __init__(self, segment):
        self.segment = segment
        self.document = self.segment.cur_document
        self.page = self.segment.cur_page
                                        # Offset: Length: Type: Optional: Exception: Range:                Meaning:
        self.DEGName = None             #      0       8  CHAR  y         X'02'                            Name of the document
                                        #                                                                  environment group

    def parse(self, data):
        """ Parse the data from a record into the record class fields.

        :param bytes data: Record data
        """
        pass
        # self.DEGName = unpack(f">8s", data)

    def format(self):
        """ Format the data from the record class fields into a record.

        :returns: Record data
        """
        data = pack(f">8s", self.DEGName)
        return data
