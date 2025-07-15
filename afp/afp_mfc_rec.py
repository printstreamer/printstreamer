""" AFP MFC Record """

from struct import pack, unpack

from stream_field_afp import StreamFieldAFP


afp_mfc_fields_list = [
    StreamFieldAFP(name="MFCFlgs", offset=0, length=1, type="BITS", optional=True, exception='\x06', range_values=['', '', '', ''], meaning=['See "MFC Semantics" on page', '238 for the MFCFlgs', 'parameter bit definitions.', '']),
    StreamFieldAFP(name="Reserved_1", offset=1, length=1, type="", optional=False, exception='\x06', range_values=['', ''], meaning=['Reserved; must be zero', '']),
    StreamFieldAFP(name="MedColl", offset=2, length=1, type="CODE", optional=False, exception='\x06', range_values=["X'00'-X'02'", ''], meaning=['Boundary conditions for', '']),
    StreamFieldAFP(name="MFCScpe", offset=3, length=1, type="CODE", optional=True, exception='\x06', range_values=["X'01'-X'05'", '', '', '', '', '', '', '', '', '', '', '', '', ''], meaning=['MFC Scope:', 'Printfile-level MFC', "X'01'", 'Document-level MFC,', "X'02'", 'all documents', 'Document-level MFC,', "X'03'", 'selected document', 'Medium-map-level', "X'04'", 'MFC, each medium', 'or sheet', '']),
    StreamFieldAFP(name="Triplets", offset=4, length=32757, type="", optional=True, exception='\x14', range_values=['', '', ''], meaning=['See "MFC Semantics" on page', '238 for triplet applicability.', '']),
    ]
afp_mfc_fields = {}
for field in afp_mfc_fields_list:
    afp_mfc_fields[field.name] = field


class AFP_MFC:

    def __init__(self, segment):
        self.segment = segment
        self.document = self.segment.cur_document
        self.page = self.segment.cur_page
                                        # Offset: Length: Type: Optional: Exception: Range:                Meaning:
        self.MFCFlgs = None             #      0       1  BITS  y         X'06'                            See "MFC Semantics" on page
                                        #                                                                  238 for the MFCFlgs
                                        #                                                                  parameter bit definitions.
        self.Reserved_1 = None          #      1       1        n         X'06'                            Reserved; must be zero
        self.MedColl = None             #      2       1  CODE  n         X'06'      X'00'-X'02'           Boundary conditions for
        self.MFCScpe = None             #      3       1  CODE  y         X'06'      X'01'-X'05'           MFC Scope:
                                        #                                                                  Printfile-level MFC
                                        #                                                                  X'01'
                                        #                                                                  Document-level MFC,
                                        #                                                                  X'02'
                                        #                                                                  all documents
                                        #                                                                  Document-level MFC,
                                        #                                                                  X'03'
                                        #                                                                  selected document
                                        #                                                                  Medium-map-level
                                        #                                                                  X'04'
                                        #                                                                  MFC, each medium
                                        #                                                                  or sheet
        self.Triplets = None            #      4   32757        y         X'14'                            See "MFC Semantics" on page
                                        #                                                                  238 for triplet applicability.

    def parse(self, data):
        """ Parse the data from a record into the record class fields.

        :param bytes data: Record data
        """
        pass
        # self.MFCFlgs, self.Reserved_1, self.MedColl, self.MFCScpe, self.Triplets = unpack(f">1s1s1s1s{self.Triplets.len()}s", data)

    def format(self):
        """ Format the data from the record class fields into a record.

        :returns: Record data
        """
        data = pack(f">1s1s1s1s{self.Triplets.len()}s", self.MFCFlgs, self.Reserved_1, self.MedColl, self.MFCScpe, self.Triplets)
        return data
