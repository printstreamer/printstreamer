""" AFP PTX Record """

from struct import pack, unpack

from stream_field_afp import StreamFieldAFP


afp_ptx_fields_list = [
    StreamFieldAFP(name="PTOCAdat", offset=0, length=32761, type="UNDF", optional=True, exception='\x00', range_values=['', '', ''], meaning=['Up to 32,759 bytes of', 'PTOCA-defined data', '']),
    ]
afp_ptx_fields = {}
for field in afp_ptx_fields_list:
    afp_ptx_fields[field.name] = field


class AFP_PTX:

    def __init__(self):
                                        # Offset: Length: Type: Optional: Exception: Range:                Meaning:
        self.PTOCAdat = None            #      0   32761  UNDF  y         X'00'                            Up to 32,759 bytes of
                                        #                                                                  PTOCA-defined data

    def parse(self, data):
        """ Parse the data from a record into the record class fields.

        :param bytes data: Record data
        """
        self.PTOCAdat = unpack(f">{self.PTOCAdat.len()}s", data)

    def format(self):
        """ Format the data from the record class fields into a record.

        :returns: Record data
        """
        data = pack(f">{self.PTOCAdat.len()}s", self.PTOCAdat)
        return data
