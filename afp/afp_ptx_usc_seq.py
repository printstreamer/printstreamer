""" AFP PTX USC Sequence """

from struct import pack, unpack

from stream_field_afp import StreamFieldAFP


afp_ptx_usc_fields_list = [
    StreamFieldAFP(name="BYPSIDEN", offset=0, length=1, type="BITS", optional=True, range_values=['See', ''], default=True, indicator=True, meaning=['Bypass identifiers', '']),
    ]
afp_ptx_usc_fields = {}
for field in afp_ptx_usc_fields_list:
    afp_ptx_usc_fields[field.name] = field


class AFP_PTX_USC:

    def __init__(self):
                                        # Offset: Length: Type: Range:        Meaning:                  Optional: Def: Ind:
        self.BYPSIDEN = None            #      0       1  BITS  See           Bypass identifiers               y    y    y

    def parse(self, data):
        """ Parse the data from a record into the record class fields.

        :param bytes data: Record data
        """
        self.BYPSIDEN = unpack(f">1s", data)

    def format(self):
        """ Format the data from the record class fields into a record.

        :returns: Record data
        """
        data = pack(f">1s", self.BYPSIDEN)
        return data
