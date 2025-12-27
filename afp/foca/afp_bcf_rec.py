""" AFP BCF Record - Begin Coded Font """

from struct import pack
from afp_foca_triplet import AFP_FOCA_Triplet
from stream_field_afp import StreamFieldAFP


afp_bcf_fields_list = [
    StreamFieldAFP(
        name="Triplets",
        offset=0,
        length=32761,
        type="UNDF",
        optional=True,
        exception='\x00',
        range_values=['', '', ''],
        meaning=['FOCA triplets', '', '']
    ),
]

afp_bcf_fields = {}
for field in afp_bcf_fields_list:
    afp_bcf_fields[field.name] = field


class AFP_BCF:
    """ Begin Coded Font """

    def __init__(self, segment):
        self.segment = segment
        self.Triplets = []

    def parse(self, data):
        """ Parse BCF record data """
        offset = 0
        length = len(data)

        while offset < length:
            triplet = AFP_FOCA_Triplet()
            triplet.parse(data[offset:])
            self.Triplets.append(triplet)
            offset += triplet.length

    def format(self):
        data = b""
        for t in self.Triplets:
            data += pack(">B B", t.length, t.triplet_id)
            data += t.data
        return data
