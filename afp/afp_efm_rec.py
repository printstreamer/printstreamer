""" AFP EFM Record """

from struct import pack, unpack

from stream_field_afp import StreamFieldAFP


afp_efm_fields_list = [
    StreamFieldAFP(name="FMName", offset=0, length=8, type="CHAR", optional=True, exception='\x02', range_values=['', ''], meaning=['Name of the form map', '']),
    ]
afp_efm_fields = {}
for field in afp_efm_fields_list:
    afp_efm_fields[field.name] = field


class AFP_EFM:

    def __init__(self):
                                        # Offset: Length: Type: Optional: Exception: Range:                Meaning:
        self.FMName = None              #      0       8  CHAR  y         X'02'                            Name of the form map

    def parse(self, data):
        """ Parse the data from a record into the record class fields.

        :param bytes data: Record data
        """
        self.FMName = unpack(f">8s", data)

    def format(self):
        """ Format the data from the record class fields into a record.

        :returns: Record data
        """
        data = pack(f">8s", self.FMName)
        return data
