""" AFP MCC Record """

from struct import pack, unpack

from stream_field_afp import StreamFieldAFP


afp_mcc_fields_list = [
    StreamFieldAFP(name="Startnum", offset=0, length=2, type="UBIN", optional=False, exception='\x06', range_values=['1-32386', ''], meaning=['Starting copy number', '']),
    StreamFieldAFP(name="Stopnum", offset=2, length=2, type="UBIN", optional=False, exception='\x06', range_values=['1-32640', ''], meaning=['Ending copy number', '']),
    StreamFieldAFP(name="Reserved_1", offset=4, length=1, type="", optional=False, exception='\x06', range_values=['', ''], meaning=['Reserved; must be zero', '']),
    StreamFieldAFP(name="MMCid", offset=5, length=1, type="CODE", optional=True, exception='\x06', range_values=['0-127', '', ''], meaning=['Medium Modification Control', 'identifier', '']),
    ]
afp_mcc_fields = {}
for field in afp_mcc_fields_list:
    afp_mcc_fields[field.name] = field


class AFP_MCC:

    def __init__(self, segment):
        self.segment = segment
        self.document = self.segment.cur_document
        self.page = self.segment.cur_page
                                        # Offset: Length: Type: Optional: Exception: Range:                Meaning:
        self.Startnum = None            #      0       2  UBIN  n         X'06'      1-32386               Starting copy number
        self.Stopnum = None             #      2       2  UBIN  n         X'06'      1-32640               Ending copy number
        self.Reserved_1 = None          #      4       1        n         X'06'                            Reserved; must be zero
        self.MMCid = None               #      5       1  CODE  y         X'06'      0-127                 Medium Modification Control
                                        #                                                                  identifier

    def parse(self, data):
        """ Parse the data from a record into the record class fields.

        :param bytes data: Record data
        """
        pass
        # self.Startnum, self.Stopnum, self.Reserved_1, self.MMCid = unpack(f">HH1s1s", data)

    def format(self):
        """ Format the data from the record class fields into a record.

        :returns: Record data
        """
        data = pack(f">HH1s1s", self.Startnum, self.Stopnum, self.Reserved_1, self.MMCid)
        return data
