""" AFP FNC Record - Font Control """

from struct import pack, unpack
from afp_foca_triplet import AFP_FOCA_Triplet
from stream_field_afp import StreamFieldAFP


afp_fnc_fields_list = [
    StreamFieldAFP("FontFlags", 0, 1, "UBIN", False, None, None,
                   ["Font control flags", "", ""]),
    StreamFieldAFP("Triplets", 1, 32760, "UNDF", True, '\x00', None,
                   ["FOCA triplets", "", ""]),
]

afp_fnc_fields = {}
for field in afp_fnc_fields_list:
    afp_fnc_fields[field.name] = field


class AFP_FNC:
    """ Font Control """

    def __init__(self, segment):
        self.segment = segment
        self.FontFlags = None
        self.Triplets = []

    def parse(self, data):
        self.FontFlags = unpack(">B", data[0:1])[0]

        offset = 1
        length = len(data)

        while offset < length:
            triplet = AFP_FOCA_Triplet()
            triplet.parse(data[offset:])
            self.Triplets.append(triplet)
            offset += triplet.length

    def format(self):
        data = pack(">B", self.FontFlags)
        for t in self.Triplets:
            data += pack(">B B", t.length, t.triplet_id)
            data += t.data
        return data
