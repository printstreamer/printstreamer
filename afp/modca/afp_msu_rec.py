""" AFP MSU Record """

from struct import pack, unpack

from stream_field_afp import StreamFieldAFP


afp_msu_fields_list = [
    StreamFieldAFP(name="SUPname", offset=0, length=8, type="CHAR", optional=True, exception='\x06', range_values=['', '', ''], meaning=['External name of text', 'suppression', '']),
    StreamFieldAFP(name="Reserved_1", offset=8, length=1, type="", optional=False, exception='\x06', range_values=['', ''], meaning=['Reserved; must be zero', '']),
    StreamFieldAFP(name="SUPid", offset=9, length=1, type="CODE", optional=True, exception='\x06', range_values=["X'01'-X'7F'", '', ''], meaning=['Text suppression local', 'identifier', '']),
    ]
afp_msu_fields = {}
for field in afp_msu_fields_list:
    afp_msu_fields[field.name] = field


class AFP_MSU:

    def __init__(self, segment):
        self.segment = segment
        self.document = self.segment.cur_document
        self.page = self.segment.cur_page
                                        # Offset: Length: Type: Optional: Exception: Range:                Meaning:
        self.SUPname = None             #      0       8  CHAR  y         X'06'                            External name of text
                                        #                                                                  suppression
        self.Reserved_1 = None          #      8       1        n         X'06'                            Reserved; must be zero
        self.SUPid = None               #      9       1  CODE  y         X'06'      X'01'-X'7F'           Text suppression local
                                        #                                                                  identifier

    def parse(self, data):
        """ Parse the data from a record into the record class fields.

        :param bytes data: Record data
        """
        pass
        # self.SUPname, self.Reserved_1, self.SUPid = unpack(f">8s1s1s", data)

    def format(self):
        """ Format the data from the record class fields into a record.

        :returns: Record data
        """
        data = pack(f">8s1s1s", self.SUPname, self.Reserved_1, self.SUPid)
        return data
