""" AFP PTX BLN Sequence """

from struct import pack, unpack

from stream_field_afp import StreamFieldAFP


afp_ptx_bln_fields_list = [
    ]
afp_ptx_bln_fields = {}
for field in afp_ptx_bln_fields_list:
    afp_ptx_bln_fields[field.name] = field


class AFP_PTX_BLN:

    def __init__(self):
                                        # Offset: Length: Type: Range:        Meaning:                  Optional: Def: Ind:
        pass

    def parse(self, data):
        """ Parse the data from a record into the record class fields.

        :param bytes data: Record data
        """
        pass

    def format(self):
        """ Format the data from the record class fields into a record.

        :returns: Record data
        """
        return None
