""" AFP IPS Record """

from struct import pack, unpack

from stream_field_afp import StreamFieldAFP


afp_ips_fields_list = [
    StreamFieldAFP(name="PsegName", offset=0, length=8, type="CHAR", optional=True, exception='\x06', range_values=['', '', ''], meaning=['Name of the page segment', 'resource', '']),
    StreamFieldAFP(name="XpsOset", offset=8, length=3, type="SBIN", optional=True, exception='\x06', range_values=['-32768-32767', '', "X'FFFFFF'", ''], meaning=['X axis origin for positioning', 'objects', 'Retired value', '']),
    StreamFieldAFP(name="YpsOset", offset=11, length=3, type="SBIN", optional=True, exception='\x06', range_values=['-32768-32767', '', "X'FFFFFF'", ''], meaning=['Y-axis origin for positioning', 'objects', 'Retired value', '']),
    StreamFieldAFP(name="Triplets", offset=14, length=32747, type="", optional=True, exception='\x10', range_values=['', '', ''], meaning=['See "IPS Semantics" for triplet', 'applicability.', '']),
    ]
afp_ips_fields = {}
for field in afp_ips_fields_list:
    afp_ips_fields[field.name] = field


class AFP_IPS:

    def __init__(self):
                                        # Offset: Length: Type: Optional: Exception: Range:                Meaning:
        self.PsegName = None            #      0       8  CHAR  y         X'06'                            Name of the page segment
                                        #                                                                  resource
        self.XpsOset = None             #      8       3  SBIN  y         X'06'      -32768-32767          X axis origin for positioning
                                        #                                                                  objects
                                        #                                            X'FFFFFF'             Retired value
        self.YpsOset = None             #     11       3  SBIN  y         X'06'      -32768-32767          Y-axis origin for positioning
                                        #                                                                  objects
                                        #                                            X'FFFFFF'             Retired value
        self.Triplets = None            #     14   32747        y         X'10'                            See "IPS Semantics" for triplet
                                        #                                                                  applicability.

    def parse(self, data):
        """ Parse the data from a record into the record class fields.

        :param bytes data: Record data
        """
        self.PsegName, self.XpsOset, self.YpsOset, self.Triplets = unpack(f">8sxhxh{self.Triplets.len()}s", data)

    def format(self):
        """ Format the data from the record class fields into a record.

        :returns: Record data
        """
        data = pack(f">8sxhxh{self.Triplets.len()}s", self.PsegName, self.XpsOset, self.YpsOset, self.Triplets)
        return data
