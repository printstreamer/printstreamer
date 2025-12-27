""" AFP OBD Record """

from struct import pack, unpack

from stream_field_afp import StreamFieldAFP


afp_obd_fields_list = [
    StreamFieldAFP(name="Triplets", offset=0, length=20, type="", optional=True, exception='14', range_values=['', '', ''], meaning=['See "OBD Semantics" for', 'triplet applicability.', '']),
    ]
afp_obd_fields = {}
for field in afp_obd_fields_list:
    afp_obd_fields[field.name] = field


class AFP_OBD:

    def __init__(self, segment):
        self.segment = segment
        self.document = self.segment.cur_document
        self.page = self.segment.cur_page
                                        # Offset: Length: Type: Optional: Exception: Range:                Meaning:
        self.Triplets = None            #      0      20        y         '14'                             See "OBD Semantics" for
                                        #                                                                  triplet applicability.

    def parse(self, data):
        """ Parse the data from a record into the record class fields.

        :param bytes data: Record data
        """
        pass
        # self.Triplets = unpack(f">{self.Triplets.len()}s", data)

    def format(self):
        """ Format the data from the record class fields into a record.

        :returns: Record data
        """
        data = pack(f">{self.Triplets.len()}s", self.Triplets)
        return data
