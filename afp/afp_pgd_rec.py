""" AFP PGD Record """

from struct import pack, unpack

from stream_field_afp import StreamFieldAFP


afp_pgd_fields_list = [
    StreamFieldAFP(name="PTOCAdes", offset=0, length=32761, type="UNDF", optional=True, exception='\x00', range_values=['', '', '', ''], meaning=['Up to 32,759 bytes of', 'PTOCA-defined descriptor', 'data', '']),
    ]
afp_pgd_fields = {}
for field in afp_pgd_fields_list:
    afp_pgd_fields[field.name] = field


class AFP_PGD:

    def __init__(self):
                                        # Offset: Length: Type: Optional: Exception: Range:                Meaning:
        self.PTOCAdes = None            #      0   32761  UNDF  y         X'00'                            Up to 32,759 bytes of
                                        #                                                                  PTOCA-defined descriptor
                                        #                                                                  data

    def parse(self, data):
        """ Parse the data from a record into the record class fields.

        :param bytes data: Record data
        """
        self.PTOCAdes = unpack(f">{self.PTOCAdes.len()}s", data)

    def format(self):
        """ Format the data from the record class fields into a record.

        :returns: Record data
        """
        data = pack(f">{self.PTOCAdes.len()}s", self.PTOCAdes)
        return data
