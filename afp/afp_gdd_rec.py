""" AFP GDD Record """

from struct import pack, unpack

from stream_field_afp import StreamFieldAFP


afp_gdd_fields_list = [
    StreamFieldAFP(name="GOCAdes", offset=0, length=32761, type="UNDF", optional=True, exception='\x00', range_values=['', '', ''], meaning=['Up to 32759 bytes of', 'GOCA-defined descriptor data', '']),
    ]
afp_gdd_fields = {}
for field in afp_gdd_fields_list:
    afp_gdd_fields[field.name] = field


class AFP_GDD:

    def __init__(self):
                                        # Offset: Length: Type: Optional: Exception: Range:                Meaning:
        self.GOCAdes = None             #      0   32761  UNDF  y         X'00'                            Up to 32759 bytes of
                                        #                                                                  GOCA-defined descriptor data

    def parse(self, data):
        """ Parse the data from a record into the record class fields.

        :param bytes data: Record data
        """
        self.GOCAdes = unpack(f">{self.GOCAdes.len()}s", data)

    def format(self):
        """ Format the data from the record class fields into a record.

        :returns: Record data
        """
        data = pack(f">{self.GOCAdes.len()}s", self.GOCAdes)
        return data
