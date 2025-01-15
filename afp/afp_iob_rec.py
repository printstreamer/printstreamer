""" AFP IOB Record """

from struct import pack, unpack

from stream_field_afp import StreamFieldAFP


afp_iob_fields_list = [
    StreamFieldAFP(name="ObjName", offset=0, length=8, type="CHAR", optional=False, exception='\x06', range_values=['', ''], meaning=['Name of the object', '']),
    StreamFieldAFP(name="Reserved_1", offset=8, length=1, type="", optional=False, exception='\x06', range_values=['', ''], meaning=['Reserved; must be zero', '']),
    StreamFieldAFP(name="ObjType", offset=9, length=1, type="CODE", optional=True, exception='\x06', range_values=["X'5F', X'92', X'BB',", "X'EB', X'FB'", '', '', '', '', '', '', '', '', '', ''], meaning=['Object type:', 'Page Segment', "X'5F'", 'Other object data', "X'92'", 'Graphics (GOCA)', "X'BB'", 'Bar Code (BCOCA)', "X'EB'", 'Image (IOCA)', "X'FB'", '']),
    StreamFieldAFP(name="XoaOset", offset=10, length=3, type="SBIN", optional=True, exception='\x06', range_values=['-32768-32767', "X'FFFFFF'", '', ''], meaning=['X-axis origin of the object area', 'Use the X-axis origin defined', 'in the object', '']),
    StreamFieldAFP(name="YoaOset", offset=13, length=3, type="SBIN", optional=True, exception='\x06', range_values=['-32768-32767', "X'FFFFFF'", '', ''], meaning=['Y-axis origin of the object area', 'Use the Y-axis origin defined', 'in the object', '']),
    StreamFieldAFP(name="XoaOrent", offset=16, length=2, type="CODE", optional=True, exception='\x06', range_values=["X'0000', X'2D00',", "X'5A00', X'8700'", '', '', '', '', '', '', '', '', '', "X'FFFFFF'", '', ''], meaning=["The object area's X-axis", 'rotation from the X axis of the', 'reference coordinate system:', '0 degrees', "X'0000'", '90 degrees', "X'2D00'", '180 degrees', "X'5A00'", '270 degrees', "X'8700'", 'Use the X-axis rotation', 'defined in the object', '']),
    StreamFieldAFP(name="YoaOrent", offset=18, length=2, type="CODE", optional=True, exception='\x06', range_values=["X'0000', X'2D00',", "X'5A00', X'8700'", '', '', '', '', '', '', '', '', '', "X'FFFF'", '', ''], meaning=["The object area's Y-axis", 'rotation from the X axis of the', 'reference coordinate system:', '0 degrees', "X'0000'", '90 degrees', "X'2D00'", '180 degrees', "X'5A00'", '270 degrees', "X'8700'", 'Use the Y-axis rotation defined', 'in the object', '']),
    StreamFieldAFP(name="XocaOset", offset=20, length=3, type="SBIN", optional=True, exception='\x06', range_values=['-32768-32767', "X'FFFFFF'", '', ''], meaning=['X-axis origin for object content', 'Use the X-axis origin defined', 'in the object', '']),
    StreamFieldAFP(name="YocaOset", offset=23, length=3, type="SBIN", optional=True, exception='\x06', range_values=['-32768-32767', "X'FFFFFF'", '', ''], meaning=['Y-axis origin for object content', 'Use the Y-axis origin defined', 'in the object', '']),
    StreamFieldAFP(name="RefCSys", offset=26, length=1, type="CODE", optional=True, exception='\x06', range_values=["X'01'", '', '', '', ''], meaning=['Reference coordinate system:', 'Page or overlay', "X'01'", 'coordinate system', '']),
    StreamFieldAFP(name="Triplets", offset=27, length=32734, type="", optional=True, exception='\x14', range_values=['', '', ''], meaning=['See "IOB Semantics" for triplet', 'applicability.', '']),
    ]
afp_iob_fields = {}
for field in afp_iob_fields_list:
    afp_iob_fields[field.name] = field


class AFP_IOB:

    def __init__(self):
                                        # Offset: Length: Type: Optional: Exception: Range:                Meaning:
        self.ObjName = None             #      0       8  CHAR  n         X'06'                            Name of the object
        self.Reserved_1 = None          #      8       1        n         X'06'                            Reserved; must be zero
        self.ObjType = None             #      9       1  CODE  y         X'06'      X'5F', X'92', X'BB',  Object type:
                                        #                                            X'EB', X'FB'          Page Segment
                                        #                                                                  X'5F'
                                        #                                                                  Other object data
                                        #                                                                  X'92'
                                        #                                                                  Graphics (GOCA)
                                        #                                                                  X'BB'
                                        #                                                                  Bar Code (BCOCA)
                                        #                                                                  X'EB'
                                        #                                                                  Image (IOCA)
                                        #                                                                  X'FB'
        self.XoaOset = None             #     10       3  SBIN  y         X'06'      -32768-32767          X-axis origin of the object area
                                        #                                            X'FFFFFF'             Use the X-axis origin defined
                                        #                                                                  in the object
        self.YoaOset = None             #     13       3  SBIN  y         X'06'      -32768-32767          Y-axis origin of the object area
                                        #                                            X'FFFFFF'             Use the Y-axis origin defined
                                        #                                                                  in the object
        self.XoaOrent = None            #     16       2  CODE  y         X'06'      X'0000', X'2D00',     The object area's X-axis
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
                                        #                                            X'FFFFFF'             Use the X-axis rotation
                                        #                                                                  defined in the object
        self.YoaOrent = None            #     18       2  CODE  y         X'06'      X'0000', X'2D00',     The object area's Y-axis
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
                                        #                                            X'FFFF'               Use the Y-axis rotation defined
                                        #                                                                  in the object
        self.XocaOset = None            #     20       3  SBIN  y         X'06'      -32768-32767          X-axis origin for object content
                                        #                                            X'FFFFFF'             Use the X-axis origin defined
                                        #                                                                  in the object
        self.YocaOset = None            #     23       3  SBIN  y         X'06'      -32768-32767          Y-axis origin for object content
                                        #                                            X'FFFFFF'             Use the Y-axis origin defined
                                        #                                                                  in the object
        self.RefCSys = None             #     26       1  CODE  y         X'06'      X'01'                 Reference coordinate system:
                                        #                                                                  Page or overlay
                                        #                                                                  X'01'
                                        #                                                                  coordinate system
        self.Triplets = None            #     27   32734        y         X'14'                            See "IOB Semantics" for triplet
                                        #                                                                  applicability.

    def parse(self, data):
        """ Parse the data from a record into the record class fields.

        :param bytes data: Record data
        """
        self.ObjName, self.Reserved_1, self.ObjType, self.XoaOset, self.YoaOset, self.XoaOrent, self.YoaOrent, self.XocaOset, self.YocaOset, self.RefCSys, self.Triplets = unpack(f">8s1s1sxhxh2s2sxhxh1s{self.Triplets.len()}s", data)

    def format(self):
        """ Format the data from the record class fields into a record.

        :returns: Record data
        """
        data = pack(f">8s1s1sxhxh2s2sxhxh1s{self.Triplets.len()}s", self.ObjName, self.Reserved_1, self.ObjType, self.XoaOset, self.YoaOset, self.XoaOrent, self.YoaOrent, self.XocaOset, self.YocaOset, self.RefCSys, self.Triplets)
        return data
