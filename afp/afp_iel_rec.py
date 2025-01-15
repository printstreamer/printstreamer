""" AFP IEL Record """

from struct import pack, unpack

from stream_field_afp import StreamFieldAFP


afp_iel_fields_list = [
    StreamFieldAFP(name="Triplets", offset=0, length=32761, type="", optional=True, exception='\x14', range_values=['', '', ''], meaning=['See "IEL Semantics" for triplet', 'applicability.', '']),
    ]
afp_iel_fields = {}
for field in afp_iel_fields_list:
    afp_iel_fields[field.name] = field


class AFP_IEL:

    def __init__(self):
                                        # Offset: Length: Type: Optional: Exception: Range:                Meaning:
        self.Triplets = None            #      0   32761        y         X'14'                            See "IEL Semantics" for triplet
                                        #                                                                  applicability.

    def parse(self, data):
        """ Parse the data from a record into the record class fields.

        :param bytes data: Record data
        """
        self.Triplets = unpack(f">{self.Triplets.len()}s", data)

    def format(self):
        """ Format the data from the record class fields into a record.

        :returns: Record data
        """
        data = pack(f">{self.Triplets.len()}s", self.Triplets)
        return data
