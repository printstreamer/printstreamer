""" AFP CPD Record - Code Page Descriptor """

from struct import pack, unpack
from afp_foca_triplet import AFP_FOCA_Triplet
from stream_field_afp import StreamFieldAFP


afp_cpd_fields_list = [
    StreamFieldAFP("CharSet", 0, 2, "UBIN", False, None, None,
                   ["Character set ID", "", ""]),
    StreamFieldAFP("Triplets", 2, 32759, "UNDF", True, '\x00', None,
                   ["FOCA triplets", "", ""]),
]

afp_cpd_fields = {}
for field in afp_cpd_fields_list:
    afp_cpd_fields[field.name] = field


class AFP_CPD:
    """ Code Page Descriptor """

    def __init__(self, segment):
        self.segment = segment
        self.CharSet = None
        self.Triplets = []

    def parse(self, data):
        self.CharSet = unpack(">H", data[0:2])[0]

        offset = 2
        while offset < len(data):
            triplet = AFP_FOCA_Triplet()
            triplet.parse(data[offset:])
            self.Triplets.append(triplet)
            offset += triplet.length

    def format(self):
        data = pack(">H", self.CharSet)
        for t in self.Triplets:
            data += pack(">B B", t.length, t.triplet_id)
            data += t.data
        return data
