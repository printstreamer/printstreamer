""" AFP BFN Record - Begin Font """

from struct import pack
from afp_foca_triplet import AFP_FOCA_Triplet
from stream_field_afp import StreamFieldAFP


afp_bfn_fields_list = [
    StreamFieldAFP("Triplets", 0, 32761, "UNDF", True, '\x00', None,
                   ["FOCA triplets", "", ""]),
]

afp_bfn_fields = {f.name: f for f in afp_bfn_fields_list}


class AFP_BFN:

    def __init__(self, segment):
        self.segment = segment
        self.Triplets = []

    def parse(self, data):
        offset = 0
        while offset < len(data):
            t = AFP_FOCA_Triplet()
            t.parse(data[offset:])
            self.Triplets.append(t)
            offset += t.length

    def format(self):
        data = b""
        for t in self.Triplets:
            data += pack(">BB", t.length, t.triplet_id) + t.data
        return data
