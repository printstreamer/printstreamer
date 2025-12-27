""" AFP IDD Record """

from struct import pack, unpack

from stream_field_afp import StreamFieldAFP


afp_idd_fields_list = [
    StreamFieldAFP(name="IOCAdes", offset=0, length=32761, type="UNDF", optional=True, exception='\x00', range_values=['', '', ''], meaning=['Up to 32759 bytes of', 'IOCA-defined descriptor data', '']),
    ]
afp_idd_fields = {}
for field in afp_idd_fields_list:
    afp_idd_fields[field.name] = field


class AFP_IDD:

    def __init__(self, segment):
        self.segment = segment
        self.document = self.segment.cur_document
        self.page = self.segment.cur_page
                                        # Offset: Length: Type: Optional: Exception: Range:                Meaning:
        self.IOCAdes = None             #      0   32761  UNDF  y         X'00'                            Up to 32759 bytes of
                                        #                                                                  IOCA-defined descriptor data

    def parse(self, data):
        """ Parse the data from a record into the record class fields.

        :param bytes data: Record data
        """
        pass
        # self.IOCAdes = unpack(f">{self.IOCAdes.len()}s", data)

    def format(self):
        """ Format the data from the record class fields into a record.

        :returns: Record data
        """
        data = pack(f">{self.IOCAdes.len()}s", self.IOCAdes)
        return data
