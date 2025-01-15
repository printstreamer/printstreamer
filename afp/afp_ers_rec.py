""" AFP ERS Record """

from struct import pack, unpack

from stream_field_afp import StreamFieldAFP


afp_ers_fields_list = [
    StreamFieldAFP(name="RSName", offset=0, length=8, type="CHAR", optional=True, exception='\x02', range_values=['', ''], meaning=['Name of the resource', '']),
    ]
afp_ers_fields = {}
for field in afp_ers_fields_list:
    afp_ers_fields[field.name] = field


class AFP_ERS:

    def __init__(self):
                                        # Offset: Length: Type: Optional: Exception: Range:                Meaning:
        self.RSName = None              #      0       8  CHAR  y         X'02'                            Name of the resource

    def parse(self, data):
        """ Parse the data from a record into the record class fields.

        :param bytes data: Record data
        """
        self.RSName = unpack(f">8s", data)

    def format(self):
        """ Format the data from the record class fields into a record.

        :returns: Record data
        """
        data = pack(f">8s", self.RSName)
        return data
