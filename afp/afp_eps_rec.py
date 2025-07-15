""" AFP EPS Record """

from struct import pack, unpack

from stream_field_afp import StreamFieldAFP


afp_eps_fields_list = [
    StreamFieldAFP(name="PsegName", offset=0, length=8, type="CHAR", optional=True, exception='\x02', range_values=['', ''], meaning=['Name of the page segment', '']),
    ]
afp_eps_fields = {}
for field in afp_eps_fields_list:
    afp_eps_fields[field.name] = field


class AFP_EPS:

    def __init__(self, segment):
        self.segment = segment
        self.document = self.segment.cur_document
        self.page = self.segment.cur_page
                                        # Offset: Length: Type: Optional: Exception: Range:                Meaning:
        self.PsegName = None            #      0       8  CHAR  y         X'02'                            Name of the page segment

    def parse(self, data):
        """ Parse the data from a record into the record class fields.

        :param bytes data: Record data
        """
        pass
        # self.PsegName = unpack(f">8s", data)

    def format(self):
        """ Format the data from the record class fields into a record.

        :returns: Record data
        """
        data = pack(f">8s", self.PsegName)
        return data
