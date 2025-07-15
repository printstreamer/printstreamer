""" AFP OBP Record """

from struct import pack, unpack

from stream_field_afp import StreamFieldAFP


afp_obp_fields_list = [
    StreamFieldAFP(name="OAPosID", offset=0, length=1, type="CODE", optional=True, exception='\x06', range_values=["X'01'-X'7F'", '', ''], meaning=['The object area position', 'identifier', '']),
    StreamFieldAFP(name="RGLength", offset=1, length=1, type="UBIN", optional=True, exception='\x06', range_values=['23', '', ''], meaning=['Total length of this repeating', 'group', '']),
    StreamFieldAFP(name="XoaOset", offset=2, length=3, type="SBIN", optional=False, exception='\x06', range_values=['-32768-32767', ''], meaning=['X-axis origin of the object area', '']),
    StreamFieldAFP(name="YoaOset", offset=5, length=3, type="SBIN", optional=False, exception='\x06', range_values=['-32768-32767', ''], meaning=['Y-axis origin of the object area', '']),
    StreamFieldAFP(name="XoaOrent", offset=8, length=2, type="CODE", optional=True, exception='\x06', range_values=["X'0000', X'2D00',", "X'5A00', X'8700'", '', '', '', '', '', '', '', '', '', ''], meaning=["The object area's X-axis", 'rotation from the X axis of the', 'reference coordinate system:', '0 degrees', "X'0000'", '90 degrees', "X'2D00'", '180 degrees', "X'5A00'", '270 degrees', "X'8700'", '']),
    StreamFieldAFP(name="YoaOrent", offset=10, length=2, type="CODE", optional=True, exception='\x06', range_values=["X'0000', X'2D00',", "X'5A00', X'8700'", '', '', '', '', '', '', '', '', '', ''], meaning=["The object area's Y axis", 'rotation from the X axis of the', 'reference coordinate system:', '0 degrees', "X'0000'", '90 degrees', "X'2D00'", '180 degrees', "X'5A00'", '270 degrees', "X'8700'", '']),
    StreamFieldAFP(name="Reserved_1", offset=12, length=1, type="", optional=False, exception='\x06', range_values=['', ''], meaning=['Reserved; must be binary zero', '']),
    StreamFieldAFP(name="XocaOset", offset=13, length=3, type="SBIN", optional=False, exception='\x06', range_values=['-32768-32767', ''], meaning=['X-axis origin for object content', '']),
    StreamFieldAFP(name="YocaOset", offset=16, length=3, type="SBIN", optional=False, exception='\x06', range_values=['-32768-32767', ''], meaning=['Y-axis origin for object content', '']),
    StreamFieldAFP(name="XocaOrent", offset=19, length=2, type="CODE", optional=True, exception='\x06', range_values=["X'0000'", '', '', ''], meaning=["The object content's X-axis", 'rotation from the X axis of the', 'object area coordinate system', '']),
    StreamFieldAFP(name="YocaOrent", offset=21, length=2, type="CODE", optional=True, exception='\x06', range_values=["X'2D00'", '', '', ''], meaning=["The object content's Y-axis", 'rotation from the X axis of the', 'object area coordinate system', '']),
    StreamFieldAFP(name="RefCSys", offset=23, length=1, type="CODE", optional=True, exception='\x06', range_values=["X'00', X'01', X'05'", '', '', '', '', '', '', '', '', '', '', '', ''], meaning=['Reference coordinate system:', 'Page or overlay', "X'00'", 'coordinate system;', 'origin is defined by', 'IPS structured field', 'Page or overlay', "X'01'", 'coordinate system;', 'standard origin', 'Retired value', "X'05'", '']),
    ]
afp_obp_fields = {}
for field in afp_obp_fields_list:
    afp_obp_fields[field.name] = field


class AFP_OBP:

    def __init__(self, segment):
        self.segment = segment
        self.document = self.segment.cur_document
        self.page = self.segment.cur_page
                                        # Offset: Length: Type: Optional: Exception: Range:                Meaning:
        self.OAPosID = None             #      0       1  CODE  y         X'06'      X'01'-X'7F'           The object area position
                                        #                                                                  identifier
        self.RGLength = None            #      1       1  UBIN  y         X'06'      23                    Total length of this repeating
                                        #                                                                  group
        self.XoaOset = None             #      2       3  SBIN  n         X'06'      -32768-32767          X-axis origin of the object area
        self.YoaOset = None             #      5       3  SBIN  n         X'06'      -32768-32767          Y-axis origin of the object area
        self.XoaOrent = None            #      8       2  CODE  y         X'06'      X'0000', X'2D00',     The object area's X-axis
                                        #                                            X'5A00', X'8700'      rotation from the X axis of the
                                        #                                                                  reference coordinate system:
                                        #                                                                  0 degrees
                                        #                                                                  X'0000'
                                        #                                                                  90 degrees
                                        #                                                                  X'2D00'
                                        #                                                                  180 degrees
                                        #                                                                  X'5A00'
                                        #                                                                  270 degrees
                                        #                                                                  X'8700'
        self.YoaOrent = None            #     10       2  CODE  y         X'06'      X'0000', X'2D00',     The object area's Y axis
                                        #                                            X'5A00', X'8700'      rotation from the X axis of the
                                        #                                                                  reference coordinate system:
                                        #                                                                  0 degrees
                                        #                                                                  X'0000'
                                        #                                                                  90 degrees
                                        #                                                                  X'2D00'
                                        #                                                                  180 degrees
                                        #                                                                  X'5A00'
                                        #                                                                  270 degrees
                                        #                                                                  X'8700'
        self.Reserved_1 = None          #     12       1        n         X'06'                            Reserved; must be binary zero
        self.XocaOset = None            #     13       3  SBIN  n         X'06'      -32768-32767          X-axis origin for object content
        self.YocaOset = None            #     16       3  SBIN  n         X'06'      -32768-32767          Y-axis origin for object content
        self.XocaOrent = None           #     19       2  CODE  y         X'06'      X'0000'               The object content's X-axis
                                        #                                                                  rotation from the X axis of the
                                        #                                                                  object area coordinate system
        self.YocaOrent = None           #     21       2  CODE  y         X'06'      X'2D00'               The object content's Y-axis
                                        #                                                                  rotation from the X axis of the
                                        #                                                                  object area coordinate system
        self.RefCSys = None             #     23       1  CODE  y         X'06'      X'00', X'01', X'05'   Reference coordinate system:
                                        #                                                                  Page or overlay
                                        #                                                                  X'00'
                                        #                                                                  coordinate system;
                                        #                                                                  origin is defined by
                                        #                                                                  IPS structured field
                                        #                                                                  Page or overlay
                                        #                                                                  X'01'
                                        #                                                                  coordinate system;
                                        #                                                                  standard origin
                                        #                                                                  Retired value
                                        #                                                                  X'05'

    def parse(self, data):
        """ Parse the data from a record into the record class fields.

        :param bytes data: Record data
        """
        pass
        # self.OAPosID, self.RGLength, self.XoaOset, self.YoaOset, self.XoaOrent, self.YoaOrent, self.Reserved_1, self.XocaOset, self.YocaOset, self.XocaOrent, self.YocaOrent, self.RefCSys = unpack(f">1sBxhxh2s2s1sxhxh2s2s1s", data)

    def format(self):
        """ Format the data from the record class fields into a record.

        :returns: Record data
        """
        data = pack(f">1sBxhxh2s2s1sxhxh2s2s1s", self.OAPosID, self.RGLength, self.XoaOset, self.YoaOset, self.XoaOrent, self.YoaOrent, self.Reserved_1, self.XocaOset, self.YocaOset, self.XocaOrent, self.YocaOrent, self.RefCSys)
        return data
