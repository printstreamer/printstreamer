""" AFP LLE Record """

from struct import pack, unpack

from stream_field_afp import StreamFieldAFP


afp_lle_fields_list = [
    StreamFieldAFP(name="LnkType", offset=0, length=1, type="CODE", optional=True, exception='\x06', range_values=["X'01'-X'03'", '', '', '', '', '', '', ''], meaning=['Link type:', 'Navigation link', "X'01'", 'Annotation link', "X'02'", 'Append link', "X'03'", '']),
    StreamFieldAFP(name="Reserved_1", offset=1, length=1, type="", optional=False, exception='\x06', range_values=['', ''], meaning=['Reserved; must be zero', '']),
    StreamFieldAFP(name="RGLength", offset=0, length=2, type="UBIN", optional=True, exception='\x06', range_values=['3-(n+1)', '', ''], meaning=['Total length of this repeating', 'group', '']),
    StreamFieldAFP(name="RGFunct", offset=2, length=1, type="CODE", optional=True, exception='\x06', range_values=["X'01'-X'03'", '', '', '', '', '', '', '', '', '', ''], meaning=['Repeating group function:', 'Link attribute', "X'01'", 'specification', 'Link source', "X'02'", 'specification', 'Link target', "X'03'", 'specification', '']),
    StreamFieldAFP(name="Triplets", offset=3, length=32758, type="", optional=True, exception='\x10', range_values=['', '', ''], meaning=['See "LLE Semantics" for', 'triplet applicability.', '']),
    ]
afp_lle_fields = {}
for field in afp_lle_fields_list:
    afp_lle_fields[field.name] = field


class AFP_LLE:

    def __init__(self):
                                        # Offset: Length: Type: Optional: Exception: Range:                Meaning:
        self.LnkType = None             #      0       1  CODE  y         X'06'      X'01'-X'03'           Link type:
                                        #                                                                  Navigation link
                                        #                                                                  X'01'
                                        #                                                                  Annotation link
                                        #                                                                  X'02'
                                        #                                                                  Append link
                                        #                                                                  X'03'
        self.Reserved_1 = None          #      1       1        n         X'06'                            Reserved; must be zero
        self.RGLength = None            #      0       2  UBIN  y         X'06'      3-(n+1)               Total length of this repeating
                                        #                                                                  group
        self.RGFunct = None             #      2       1  CODE  y         X'06'      X'01'-X'03'           Repeating group function:
                                        #                                                                  Link attribute
                                        #                                                                  X'01'
                                        #                                                                  specification
                                        #                                                                  Link source
                                        #                                                                  X'02'
                                        #                                                                  specification
                                        #                                                                  Link target
                                        #                                                                  X'03'
                                        #                                                                  specification
        self.Triplets = None            #      3   32758        y         X'10'                            See "LLE Semantics" for
                                        #                                                                  triplet applicability.

    def parse(self, data):
        """ Parse the data from a record into the record class fields.

        :param bytes data: Record data
        """
        self.LnkType, self.Reserved_1, self.RGLength, self.RGFunct, self.Triplets = unpack(f">1s1sH1s{self.Triplets.len()}s", data)

    def format(self):
        """ Format the data from the record class fields into a record.

        :returns: Record data
        """
        data = pack(f">1s1sH1s{self.Triplets.len()}s", self.LnkType, self.Reserved_1, self.RGLength, self.RGFunct, self.Triplets)
        return data
