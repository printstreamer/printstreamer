""" AFP MMC Record """

from struct import pack, unpack

from stream_field_afp import StreamFieldAFP


afp_mmc_fields_list = [
    StreamFieldAFP(name="MMCid", offset=0, length=1, type="CODE", optional=True, exception='\x06', range_values=['1-127', '', ''], meaning=['Medium Modification Control', 'identifier', '']),
    StreamFieldAFP(name="Constant", offset=1, length=1, type="CODE", optional=False, exception='\x06', range_values=["X'FF'", ''], meaning=['Constant data', '']),
    StreamFieldAFP(name="Keywords", offset=2, length=32759, type="CODE", optional=False, exception=None, range_values=[''], meaning=['']),
    ]
afp_mmc_fields = {}
for field in afp_mmc_fields_list:
    afp_mmc_fields[field.name] = field


class AFP_MMC:

    def __init__(self):
                                        # Offset: Length: Type: Optional: Exception: Range:                Meaning:
        self.MMCid = None               #      0       1  CODE  y         X'06'      1-127                 Medium Modification Control
                                        #                                                                  identifier
        self.Constant = None            #      1       1  CODE  n         X'06'      X'FF'                 Constant data
        self.Keywords = None            #      2   32759  CODE            None                             

    def parse(self, data):
        """ Parse the data from a record into the record class fields.

        :param bytes data: Record data
        """
        self.MMCid, self.Constant, self.Keywords = unpack(f">1s1s{self.Keywords.len()}s", data)

    def format(self):
        """ Format the data from the record class fields into a record.

        :returns: Record data
        """
        data = pack(f">1s1s{self.Keywords.len()}s", self.MMCid, self.Constant, self.Keywords)
        return data
