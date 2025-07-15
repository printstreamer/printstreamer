""" AFP MPS Record """

from struct import pack, unpack

from stream_field_afp import StreamFieldAFP


afp_mps_fields_list = [
    StreamFieldAFP(name="RGLength", offset=0, length=1, type="UBIN", optional=True, exception='\x06', range_values=["X'0C'", '', ''], meaning=['Length of each repeating', 'group', '']),
    StreamFieldAFP(name="Reserved_1", offset=1, length=3, type="", optional=False, exception='\x06', range_values=['', ''], meaning=['Reserved; must be zero', '']),
    StreamFieldAFP(name="Reserved_2", offset=0, length=4, type="", optional=False, exception='\x06', range_values=['', ''], meaning=['Reserved; must be zero', '']),
    StreamFieldAFP(name="PsegName", offset=4, length=8, type="CHAR", optional=True, exception='\x06', range_values=['', '', ''], meaning=['External name of page', 'segment', '']),
    ]
afp_mps_fields = {}
for field in afp_mps_fields_list:
    afp_mps_fields[field.name] = field


class AFP_MPS:

    def __init__(self, segment):
        self.segment = segment
        self.document = self.segment.cur_document
        self.page = self.segment.cur_page
                                        # Offset: Length: Type: Optional: Exception: Range:                Meaning:
        self.RGLength = None            #      0       1  UBIN  y         X'06'      X'0C'                 Length of each repeating
                                        #                                                                  group
        self.Reserved_1 = None          #      1       3        n         X'06'                            Reserved; must be zero
        self.Reserved_2 = None          #      0       4        n         X'06'                            Reserved; must be zero
        self.PsegName = None            #      4       8  CHAR  y         X'06'                            External name of page
                                        #                                                                  segment

    def parse(self, data):
        """ Parse the data from a record into the record class fields.

        :param bytes data: Record data
        """
        pass
        # self.RGLength, self.Reserved_1, self.Reserved_2, self.PsegName = unpack(f">B3s4s8s", data)

    def format(self):
        """ Format the data from the record class fields into a record.

        :returns: Record data
        """
        data = pack(f">B3s4s8s", self.RGLength, self.Reserved_1, self.Reserved_2, self.PsegName)
        return data
