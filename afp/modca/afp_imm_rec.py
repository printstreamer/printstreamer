""" AFP IMM Record """

from struct import pack, unpack

from stream_field_afp import StreamFieldAFP


afp_imm_fields_list = [
    StreamFieldAFP(name="MMPName", offset=0, length=8, type="CHAR", optional=True, exception='\x0E', range_values=['', '', ''], meaning=['Name of the medium map to', 'be invoked', '']),
    StreamFieldAFP(name="Triplets", offset=8, length=32753, type="", optional=True, exception='\x10', range_values=['', '', ''], meaning=['See "IMM Semantics" for', 'triplet applicability.', '']),
    ]
afp_imm_fields = {}
for field in afp_imm_fields_list:
    afp_imm_fields[field.name] = field


class AFP_IMM:

    def __init__(self, segment):
        self.segment = segment
        self.document = self.segment.cur_document
        self.page = self.segment.cur_page
                                        # Offset: Length: Type: Optional: Exception: Range:                Meaning:
        self.MMPName = None             #      0       8  CHAR  y         X'0E'                            Name of the medium map to
                                        #                                                                  be invoked
        self.Triplets = None            #      8   32753        y         X'10'                            See "IMM Semantics" for
                                        #                                                                  triplet applicability.

    def parse(self, data):
        """ Parse the data from a record into the record class fields.

        :param bytes data: Record data
        """
        pass
        # self.MMPName, self.Triplets = unpack(f">8s{self.Triplets.len()}s", data)

    def format(self):
        """ Format the data from the record class fields into a record.

        :returns: Record data
        """
        data = pack(f">8s{self.Triplets.len()}s", self.MMPName, self.Triplets)
        return data
