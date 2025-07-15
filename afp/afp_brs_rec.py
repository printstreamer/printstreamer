""" AFP BRS Record """

from struct import pack, unpack

from stream_field_afp import StreamFieldAFP


afp_brs_fields_list = [
    StreamFieldAFP(name="RSName", offset=0, length=8, type="CHAR", optional=False, exception='\x02', range_values=['', ''], meaning=['Identifier of the resource', '']),
    StreamFieldAFP(name="Reserved_1", offset=8, length=2, type="", optional=False, exception='\x06', range_values=['', ''], meaning=['', '']),
    StreamFieldAFP(name="Reserved_2", offset=10, length=32751, type="", optional=False, exception='\x14', range_values=['', ''], meaning=['See "BRS Semantics" for', '']),
    ]
afp_brs_fields = {}
for field in afp_brs_fields_list:
    afp_brs_fields[field.name] = field


class AFP_BRS:

    def __init__(self, segment):
        self.segment = segment
        self.document = self.segment.cur_document
        self.page = self.segment.cur_page
                                        # Offset: Length: Type: Optional: Exception: Range:                Meaning:
        self.RSName = None              #      0       8  CHAR  n         X'02'                            Identifier of the resource
        self.Reserved_1 = None          #      8       2        n         X'06'                            
        self.Reserved_2 = None          #     10   32751        n         X'14'                            See "BRS Semantics" for

    def parse(self, data):
        """ Parse the data from a record into the record class fields.

        :param bytes data: Record data
        """
        pass
        # self.RSName, self.Reserved_1, self.Reserved_2 = unpack(f">8s2s{self.Reserved_2.len()}s", data)

    def format(self):
        """ Format the data from the record class fields into a record.

        :returns: Record data
        """
        data = pack(f">8s2s{self.Reserved_2.len()}s", self.RSName, self.Reserved_1, self.Reserved_2)
        return data
