""" AFP CFC Record - Coded Font Control """

from struct import pack, unpack
from afp_foca_triplet import AFP_FOCA_Triplet
from stream_field_afp import StreamFieldAFP


afp_cfc_fields_list = [
    StreamFieldAFP("Flags", 0, 1, "UBIN", False, None, None,
                   ["Coded font flags", "", ""]),
    StreamFieldAFP("Triplets", 1, 32760, "UNDF", True, '\x00', None,
                   ["FOCA triplets", "", ""]),
]

afp_cfc_fields = {f.name: f for f in afp_cfc_fields_list}


class AFP_CFC:

    def __init__(self, segment):
        self.segment = segment
        self.Flags = None
        self.Triplets = []

    def parse(self, data):
        self.Flags = unpack(">B", data[0:1])[0]
        offset = 1
        while offset < len(data):
            t = AFP_FOCA_Triplet()
            t.parse(data[offset:])
            self.Triplets.append(t)
            offset += t.length

    def format(self):
        data = pack(">B", self.Flags)
        for t in self.Triplets:
            data += pack(">BB", t.length, t.triplet_id) + t.data
        return data
