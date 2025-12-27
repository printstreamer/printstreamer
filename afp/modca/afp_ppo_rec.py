""" AFP PPO Record """

from struct import pack, unpack

from stream_field_afp import StreamFieldAFP


afp_ppo_fields_list = [
    StreamFieldAFP(name="RGLength", offset=0, length=2, type="UBIN", optional=False, exception='\x06', range_values=['18-(n+1)', ''], meaning=['Total length of this repeating', '']),
    StreamFieldAFP(name="ObjType", offset=2, length=1, type="CODE", optional=False, exception='\x06', range_values=["X'92', X'DF', X'FB'", ''], meaning=['Object type:', '']),
    StreamFieldAFP(name="Reserved_1", offset=3, length=2, type="", optional=False, exception='\x06', range_values=['', ''], meaning=['Reserved; must be zero', '']),
    StreamFieldAFP(name="ObjOrent", offset=5, length=1, type="BITS", optional=False, exception='\x06', range_values=['', ''], meaning=['Object orientations relative to', '']),
    StreamFieldAFP(name="XocaOset", offset=6, length=3, type="SBIN", optional=False, exception='\x06', range_values=['-32768-32767', ''], meaning=['X axis origin for object content', '']),
    StreamFieldAFP(name="YocaOset", offset=9, length=3, type="SBIN", optional=False, exception='\x06', range_values=['-32768-32767', ''], meaning=['Y axis origin for object content', '']),
    StreamFieldAFP(name="Reserved_2", offset=12, length=32749, type="", optional=False, exception='\x14', range_values=['', ''], meaning=['See "PPO Semantics" for', '']),
    ]
afp_ppo_fields = {}
for field in afp_ppo_fields_list:
    afp_ppo_fields[field.name] = field


class AFP_PPO:

    def __init__(self, segment):
        self.segment = segment
        self.document = self.segment.cur_document
        self.page = self.segment.cur_page
                                        # Offset: Length: Type: Optional: Exception: Range:                Meaning:
        self.RGLength = None            #      0       2  UBIN  n         X'06'      18-(n+1)              Total length of this repeating
        self.ObjType = None             #      2       1  CODE  n         X'06'      X'92', X'DF', X'FB'   Object type:
        self.Reserved_1 = None          #      3       2        n         X'06'                            Reserved; must be zero
        self.ObjOrent = None            #      5       1  BITS  n         X'06'                            Object orientations relative to
        self.XocaOset = None            #      6       3  SBIN  n         X'06'      -32768-32767          X axis origin for object content
        self.YocaOset = None            #      9       3  SBIN  n         X'06'      -32768-32767          Y axis origin for object content
        self.Reserved_2 = None          #     12   32749        n         X'14'                            See "PPO Semantics" for

    def parse(self, data):
        """ Parse the data from a record into the record class fields.

        :param bytes data: Record data
        """
        pass
        # self.RGLength, self.ObjType, self.Reserved_1, self.ObjOrent, self.XocaOset, self.YocaOset, self.Reserved_2 = unpack(f">H1s2s1sxhxh{self.Reserved_2.len()}s", data)

    def format(self):
        """ Format the data from the record class fields into a record.

        :returns: Record data
        """
        data = pack(f">H1s2s1sxhxh{self.Reserved_2.len()}s", self.RGLength, self.ObjType, self.Reserved_1, self.ObjOrent, self.XocaOset, self.YocaOset, self.Reserved_2)
        return data
