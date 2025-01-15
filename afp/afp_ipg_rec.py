""" AFP IPG Record """

from struct import pack, unpack

from stream_field_afp import StreamFieldAFP


afp_ipg_fields_list = [
    StreamFieldAFP(name="PgName", offset=0, length=8, type="CHAR", optional=False, exception='\x06', range_values=['', ''], meaning=['Name of the page', '']),
    StreamFieldAFP(name="Reserved_1", offset=8, length=8, type="", optional=False, exception='\x06', range_values=['', ''], meaning=['Reserved; must be zero', '']),
    StreamFieldAFP(name="IPgFlgs", offset=16, length=1, type="BITS", optional=True, exception='\x06', range_values=['', '', '', ''], meaning=['Specify control information for', 'the included page. See "IPG', 'Semantics" for bit definitions.', '']),
    StreamFieldAFP(name="Triplets", offset=17, length=32744, type="", optional=True, exception='\x14', range_values=['', '', ''], meaning=['See "IPG Semantics" for triplet', 'applicability.', '']),
    ]
afp_ipg_fields = {}
for field in afp_ipg_fields_list:
    afp_ipg_fields[field.name] = field


class AFP_IPG:

    def __init__(self):
                                        # Offset: Length: Type: Optional: Exception: Range:                Meaning:
        self.PgName = None              #      0       8  CHAR  n         X'06'                            Name of the page
        self.Reserved_1 = None          #      8       8        n         X'06'                            Reserved; must be zero
        self.IPgFlgs = None             #     16       1  BITS  y         X'06'                            Specify control information for
                                        #                                                                  the included page. See "IPG
                                        #                                                                  Semantics" for bit definitions.
        self.Triplets = None            #     17   32744        y         X'14'                            See "IPG Semantics" for triplet
                                        #                                                                  applicability.

    def parse(self, data):
        """ Parse the data from a record into the record class fields.

        :param bytes data: Record data
        """
        self.PgName, self.Reserved_1, self.IPgFlgs, self.Triplets = unpack(f">8s8s1s{self.Triplets.len()}s", data)

    def format(self):
        """ Format the data from the record class fields into a record.

        :returns: Record data
        """
        data = pack(f">8s8s1s{self.Triplets.len()}s", self.PgName, self.Reserved_1, self.IPgFlgs, self.Triplets)
        return data
