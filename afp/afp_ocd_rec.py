""" AFP OCD Record """

from struct import pack, unpack

from stream_field_afp import StreamFieldAFP


afp_ocd_fields_list = [
    StreamFieldAFP(name="ObjCdat", offset=0, length=32761, type="UNDF", optional=True, exception='\x00', range_values=['', '', ''], meaning=['Up to 32,759 bytes of object', 'data', '']),
    ]
afp_ocd_fields = {}
for field in afp_ocd_fields_list:
    afp_ocd_fields[field.name] = field


class AFP_OCD:

    def __init__(self):
                                        # Offset: Length: Type: Optional: Exception: Range:                Meaning:
        self.ObjCdat = None             #      0   32761  UNDF  y         X'00'                            Up to 32,759 bytes of object
                                        #                                                                  data

    def parse(self, data):
        """ Parse the data from a record into the record class fields.

        :param bytes data: Record data
        """
        self.ObjCdat = unpack(f">{self.ObjCdat.len()}s", data)

    def format(self):
        """ Format the data from the record class fields into a record.

        :returns: Record data
        """
        data = pack(f">{self.ObjCdat.len()}s", self.ObjCdat)
        return data
