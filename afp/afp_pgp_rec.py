""" AFP PGP Record """

from struct import pack, unpack

from stream_field_afp import StreamFieldAFP


afp_pgp_fields_list = [
    StreamFieldAFP(name="Constant", offset=0, length=1, type="CODE", optional=True, exception='\x06', range_values=["X'01'", '', ''], meaning=['Reserved constant; must be', "X'01'", '']),
    StreamFieldAFP(name="RGLength", offset=0, length=1, type="UBIN", optional=True, exception='\x06', range_values=["X'0A'-X'0C'", '', ''], meaning=['Length of each repeating', 'group', '']),
    StreamFieldAFP(name="XmOset", offset=1, length=3, type="SBIN", optional=True, exception='\x06', range_values=['-32768-32767', '', ''], meaning=['Xm coordinate of page', 'presentation space origin', '']),
    StreamFieldAFP(name="YmOset", offset=4, length=3, type="SBIN", optional=True, exception='\x06', range_values=['-32768-32767', '', ''], meaning=['Ym coordinate of page', 'presentation space origin', '']),
    StreamFieldAFP(name="PGorient", offset=7, length=2, type="CODE", optional=True, exception='\x06', range_values=["X'0000', X'2D00',", "X'5A00', X'8700'", '', '', '', '', '', '', '', '', '', '', ''], meaning=['The page presentation space', 'X-axis rotation from the X axis', 'of the medium presentation', 'space:', '0° rotation', "X'0000'", '90° rotation', "X'2D00'", '180° rotation', "X'5A00'", '270° rotation', "X'8700'", '']),
    StreamFieldAFP(name="SHside", offset=9, length=1, type="CODE", optional=True, exception='\x06', range_values=["X'00'-X'01',", "X'10'-X'11',", "X'20'-X'21',", '', "X'30'-X'31',", "X'40'-X'41'", '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', ''], meaning=['Sheet side and partition', 'selection', 'Page on front side if', "X'00'", 'no N-up, default', 'page placement on', 'front side if N-up', 'Page on back side if', "X'01'", 'no N-up, default', 'page placement on', 'back side if N-up', 'Explicit N-up page', "X'10'", 'placement: partition', '1, front side', 'Explicit N-up page', "X'11'", 'placement: partition', '1, back side', 'Explicit N-up page', "X'20'", 'placement: partition', '2, front side', 'Explicit N-up page', "X'21'", 'placement: partition', '2, back side', 'Explicit N-up page', "X'30'", 'placement: partition', '3, front side', 'Explicit N-up page', "X'31'", 'placement: partition', '3, back side', 'Explicit N-up page', "X'40'", 'placement: partition', '4, front side', 'Explicit N-up page', "X'41'", 'placement: partition', '4, back side', '']),
    StreamFieldAFP(name="PgFlgs", offset=10, length=1, type="BITS", optional=True, exception='\x02', range_values=['', '', '', '', ''], meaning=['Specify additional presentation', 'controls for the partition. See', '"PGP Semantics" for PgFlgs', 'bit definitions.', '']),
    StreamFieldAFP(name="PMCid", offset=11, length=1, type="CODE", optional=True, exception='\x02', range_values=['0-127', '', "X'FF'", ''], meaning=['Page Modification Control', 'identifier', 'Apply all modifications', '']),
    ]
afp_pgp_fields = {}
for field in afp_pgp_fields_list:
    afp_pgp_fields[field.name] = field


class AFP_PGP:

    def __init__(self):
                                        # Offset: Length: Type: Optional: Exception: Range:                Meaning:
        self.Constant = None            #      0       1  CODE  y         X'06'      X'01'                 Reserved constant; must be
                                        #                                                                  X'01'
        self.RGLength = None            #      0       1  UBIN  y         X'06'      X'0A'-X'0C'           Length of each repeating
                                        #                                                                  group
        self.XmOset = None              #      1       3  SBIN  y         X'06'      -32768-32767          Xm coordinate of page
                                        #                                                                  presentation space origin
        self.YmOset = None              #      4       3  SBIN  y         X'06'      -32768-32767          Ym coordinate of page
                                        #                                                                  presentation space origin
        self.PGorient = None            #      7       2  CODE  y         X'06'      X'0000', X'2D00',     The page presentation space
                                        #                                            X'5A00', X'8700'      X-axis rotation from the X axis
                                        #                                                                  of the medium presentation
                                        #                                                                  space:
                                        #                                                                  0° rotation
                                        #                                                                  X'0000'
                                        #                                                                  90° rotation
                                        #                                                                  X'2D00'
                                        #                                                                  180° rotation
                                        #                                                                  X'5A00'
                                        #                                                                  270° rotation
                                        #                                                                  X'8700'
        self.SHside = None              #      9       1  CODE  y         X'06'      X'00'-X'01',          Sheet side and partition
                                        #                                            X'10'-X'11',          selection
                                        #                                            X'20'-X'21',          Page on front side if
                                        #                                                                  X'00'
                                        #                                            X'30'-X'31',          no N-up, default
                                        #                                            X'40'-X'41'           page placement on
                                        #                                                                  front side if N-up
                                        #                                                                  Page on back side if
                                        #                                                                  X'01'
                                        #                                                                  no N-up, default
                                        #                                                                  page placement on
                                        #                                                                  back side if N-up
                                        #                                                                  Explicit N-up page
                                        #                                                                  X'10'
                                        #                                                                  placement: partition
                                        #                                                                  1, front side
                                        #                                                                  Explicit N-up page
                                        #                                                                  X'11'
                                        #                                                                  placement: partition
                                        #                                                                  1, back side
                                        #                                                                  Explicit N-up page
                                        #                                                                  X'20'
                                        #                                                                  placement: partition
                                        #                                                                  2, front side
                                        #                                                                  Explicit N-up page
                                        #                                                                  X'21'
                                        #                                                                  placement: partition
                                        #                                                                  2, back side
                                        #                                                                  Explicit N-up page
                                        #                                                                  X'30'
                                        #                                                                  placement: partition
                                        #                                                                  3, front side
                                        #                                                                  Explicit N-up page
                                        #                                                                  X'31'
                                        #                                                                  placement: partition
                                        #                                                                  3, back side
                                        #                                                                  Explicit N-up page
                                        #                                                                  X'40'
                                        #                                                                  placement: partition
                                        #                                                                  4, front side
                                        #                                                                  Explicit N-up page
                                        #                                                                  X'41'
                                        #                                                                  placement: partition
                                        #                                                                  4, back side
        self.PgFlgs = None              #     10       1  BITS  y         X'02'                            Specify additional presentation
                                        #                                                                  controls for the partition. See
                                        #                                                                  "PGP Semantics" for PgFlgs
                                        #                                                                  bit definitions.
        self.PMCid = None               #     11       1  CODE  y         X'02'      0-127                 Page Modification Control
                                        #                                                                  identifier
                                        #                                            X'FF'                 Apply all modifications

    def parse(self, data):
        """ Parse the data from a record into the record class fields.

        :param bytes data: Record data
        """
        self.Constant, self.RGLength, self.XmOset, self.YmOset, self.PGorient, self.SHside, self.PgFlgs, self.PMCid = unpack(f">1sBxhxh2s1s1s1s", data)

    def format(self):
        """ Format the data from the record class fields into a record.

        :returns: Record data
        """
        data = pack(f">1sBxhxh2s1s1s1s", self.Constant, self.RGLength, self.XmOset, self.YmOset, self.PGorient, self.SHside, self.PgFlgs, self.PMCid)
        return data
