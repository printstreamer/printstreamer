""" AFP IPO Record """

from struct import pack, unpack

from stream_field_afp import StreamFieldAFP


afp_ipo_fields_list = [
    StreamFieldAFP(name="OvlyName", offset=0, length=8, type="CHAR", optional=False, exception='\x06', range_values=['', ''], meaning=['Name of the overlay resource', '']),
    StreamFieldAFP(name="XolOset", offset=8, length=3, type="SBIN", optional=True, exception='\x06', range_values=['-32768-32767', '', "X'FFFFFF'", ''], meaning=['X-axis origin for the page', 'overlay', 'Retired value', '']),
    StreamFieldAFP(name="YolOset", offset=11, length=3, type="SBIN", optional=True, exception='\x06', range_values=['-32768-32767', '', "X'FFFFFF'", ''], meaning=['Y-axis origin for the page', 'overlay', 'Retired value', '']),
    StreamFieldAFP(name="OvlyOrent", offset=14, length=2, type="CODE", optional=True, exception='\x02', range_values=["X'0000', X'2D00',", "X'5A00', X'8700'", '', '', '', '', '', '', '', '', '', '', ''], meaning=["The overlay's X-axis rotation", 'from the X axis of the', 'including page coordinate', 'system:', '0 degrees', "X'0000'", '90 degrees', "X'2D00'", '180 degrees', "X'5A00'", '270 degrees', "X'8700'", '']),
    StreamFieldAFP(name="Triplets", offset=16, length=32745, type="", optional=True, exception='\x10', range_values=['', '', ''], meaning=['See "IPO Semantics" for triplet', 'applicability.', '']),
    ]
afp_ipo_fields = {}
for field in afp_ipo_fields_list:
    afp_ipo_fields[field.name] = field


class AFP_IPO:

    def __init__(self, segment):
        self.segment = segment
        self.document = self.segment.cur_document
        self.page = self.segment.cur_page
                                        # Offset: Length: Type: Optional: Exception: Range:                Meaning:
        self.OvlyName = None            #      0       8  CHAR  n         X'06'                            Name of the overlay resource
        self.XolOset = None             #      8       3  SBIN  y         X'06'      -32768-32767          X-axis origin for the page
                                        #                                                                  overlay
                                        #                                            X'FFFFFF'             Retired value
        self.YolOset = None             #     11       3  SBIN  y         X'06'      -32768-32767          Y-axis origin for the page
                                        #                                                                  overlay
                                        #                                            X'FFFFFF'             Retired value
        self.OvlyOrent = None           #     14       2  CODE  y         X'02'      X'0000', X'2D00',     The overlay's X-axis rotation
                                        #                                            X'5A00', X'8700'      from the X axis of the
                                        #                                                                  including page coordinate
                                        #                                                                  system:
                                        #                                                                  0 degrees
                                        #                                                                  X'0000'
                                        #                                                                  90 degrees
                                        #                                                                  X'2D00'
                                        #                                                                  180 degrees
                                        #                                                                  X'5A00'
                                        #                                                                  270 degrees
                                        #                                                                  X'8700'
        self.Triplets = None            #     16   32745        y         X'10'                            See "IPO Semantics" for triplet
                                        #                                                                  applicability.

    def parse(self, data):
        """ Parse the data from a record into the record class fields.

        :param bytes data: Record data
        """
        pass
        # self.OvlyName, self.XolOset, self.YolOset, self.OvlyOrent, self.Triplets = unpack(f">8sxhxh2s{self.Triplets.len()}s", data)

    def format(self):
        """ Format the data from the record class fields into a record.

        :returns: Record data
        """
        data = pack(f">8sxhxh2s{self.Triplets.len()}s", self.OvlyName, self.XolOset, self.YolOset, self.OvlyOrent, self.Triplets)
        return data
