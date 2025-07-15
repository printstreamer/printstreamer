""" AFP MDD Record """

from struct import pack, unpack

from stream_field_afp import StreamFieldAFP


afp_mdd_fields_list = [
    StreamFieldAFP(name="XmBase", offset=0, length=1, type="CODE", optional=True, exception='\x06', range_values=["X'00'-X'01'", '', '', '', '', '', ''], meaning=['Medium unit base for the X', 'axis:', '10 inches', "X'00'", '10 centimeters', "X'01'", '']),
    StreamFieldAFP(name="YmBase", offset=1, length=1, type="CODE", optional=True, exception='\x06', range_values=["X'00'-X'01'", '', '', '', '', '', ''], meaning=['Medium unit base for the Y', 'axis:', '10 inches', "X'00'", '10 centimeters', "X'01'", '']),
    StreamFieldAFP(name="XmUnits", offset=2, length=2, type="UBIN", optional=True, exception='\x06', range_values=['1-32767', '', ''], meaning=['Medium units per unit base', 'for the X axis', '']),
    StreamFieldAFP(name="YmUnits", offset=4, length=2, type="UBIN", optional=True, exception='\x06', range_values=['1-32767', '', ''], meaning=['Medium units per unit base', 'for the Y axis', '']),
    StreamFieldAFP(name="XmSize", offset=6, length=3, type="UBIN", optional=True, exception='\x06', range_values=['1-32767', "X'000000'", "X'FFFFFF'", ''], meaning=['Medium extent for the X axis', 'X-axis extent not specified', 'Presentation process default', '']),
    StreamFieldAFP(name="YmSize", offset=9, length=3, type="UBIN", optional=True, exception='\x06', range_values=['1-32767', "X'000000'", "X'FFFFFF'", ''], meaning=['Medium extent for the Y axis', 'Y-axis extent not specified', 'Presentation process default', '']),
    StreamFieldAFP(name="MDDFlgs", offset=12, length=1, type="BITS", optional=True, exception='\x06', range_values=['', '', '', ''], meaning=['Specify control information for', 'the media. See "MDD', 'Semantics" for bit definitions.', '']),
    StreamFieldAFP(name="Triplets", offset=13, length=32748, type="", optional=True, exception='\x10', range_values=['', '', ''], meaning=['See "MDD Semantics" for', 'triplet applicability.', '']),
    ]
afp_mdd_fields = {}
for field in afp_mdd_fields_list:
    afp_mdd_fields[field.name] = field


class AFP_MDD:

    def __init__(self, segment):
        self.segment = segment
        self.document = self.segment.cur_document
        self.page = self.segment.cur_page
                                        # Offset: Length: Type: Optional: Exception: Range:                Meaning:
        self.XmBase = None              #      0       1  CODE  y         X'06'      X'00'-X'01'           Medium unit base for the X
                                        #                                                                  axis:
                                        #                                                                  10 inches
                                        #                                                                  X'00'
                                        #                                                                  10 centimeters
                                        #                                                                  X'01'
        self.YmBase = None              #      1       1  CODE  y         X'06'      X'00'-X'01'           Medium unit base for the Y
                                        #                                                                  axis:
                                        #                                                                  10 inches
                                        #                                                                  X'00'
                                        #                                                                  10 centimeters
                                        #                                                                  X'01'
        self.XmUnits = None             #      2       2  UBIN  y         X'06'      1-32767               Medium units per unit base
                                        #                                                                  for the X axis
        self.YmUnits = None             #      4       2  UBIN  y         X'06'      1-32767               Medium units per unit base
                                        #                                                                  for the Y axis
        self.XmSize = None              #      6       3  UBIN  y         X'06'      1-32767               Medium extent for the X axis
                                        #                                            X'000000'             X-axis extent not specified
                                        #                                            X'FFFFFF'             Presentation process default
        self.YmSize = None              #      9       3  UBIN  y         X'06'      1-32767               Medium extent for the Y axis
                                        #                                            X'000000'             Y-axis extent not specified
                                        #                                            X'FFFFFF'             Presentation process default
        self.MDDFlgs = None             #     12       1  BITS  y         X'06'                            Specify control information for
                                        #                                                                  the media. See "MDD
                                        #                                                                  Semantics" for bit definitions.
        self.Triplets = None            #     13   32748        y         X'10'                            See "MDD Semantics" for
                                        #                                                                  triplet applicability.

    def parse(self, data):
        """ Parse the data from a record into the record class fields.

        :param bytes data: Record data
        """
        pass
        # self.XmBase, self.YmBase, self.XmUnits, self.YmUnits, self.XmSize, self.YmSize, self.MDDFlgs, self.Triplets = unpack(f">1s1sHHxHxH1s{self.Triplets.len()}s", data)

    def format(self):
        """ Format the data from the record class fields into a record.

        :returns: Record data
        """
        data = pack(f">1s1sHHxHxH1s{self.Triplets.len()}s", self.XmBase, self.YmBase, self.XmUnits, self.YmUnits, self.XmSize, self.YmSize, self.MDDFlgs, self.Triplets)
        return data
