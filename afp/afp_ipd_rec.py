""" AFP IPD Record """

from struct import pack, unpack

from stream_field_afp import StreamFieldAFP


afp_ipd_fields_list = [
    StreamFieldAFP(name="IOCAdat", offset=0, length=32761, type="UNDF", optional=True, exception='\x00', range_values=['', '', ''], meaning=['Up to 32759 bytes of IOCA', 'defined data', '']),
    ]
afp_ipd_fields = {}
for field in afp_ipd_fields_list:
    afp_ipd_fields[field.name] = field


class AFP_IPD:

    def __init__(self):
                                        # Offset: Length: Type: Optional: Exception: Range:                Meaning:
        self.IOCAdat = None             #      0   32761  UNDF  y         X'00'                            Up to 32759 bytes of IOCA
                                        #                                                                  defined data

    def parse(self, data):
        """ Parse the data from a record into the record class fields.

        :param bytes data: Record data
        """
        self.IOCAdat = unpack(f">{self.IOCAdat.len()}s", data)

    def format(self):
        """ Format the data from the record class fields into a record.

        :returns: Record data
        """
        data = pack(f">{self.IOCAdat.len()}s", self.IOCAdat)
        return data
