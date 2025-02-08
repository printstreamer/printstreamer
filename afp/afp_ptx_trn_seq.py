""" AFP PTX TRN Sequence """

from struct import pack, unpack

from stream_field_afp import StreamFieldAFP


afp_ptx_trn_fields_list = [
    StreamFieldAFP(name="TRNDATA", offset=0, length=253, type="CHAR", optional=True, range_values=['Not', ''], default=False, indicator=False, meaning=['Transparent data', '']),
    ]
afp_ptx_trn_fields = {}
for field in afp_ptx_trn_fields_list:
    afp_ptx_trn_fields[field.name] = field


class AFP_PTX_TRN:

    def __init__(self):
                                        # Offset: Length: Type: Range:        Meaning:                  Optional: Def: Ind:
        self.TRNDATA = None             #      0     253  CHAR  Not           Transparent data                 y    n    n

    def parse(self, data):
        """ Parse the data from a record into the record class fields.

        :param bytes data: Record data
        """
        self.TRNDATA = unpack(f">253s", data)

    def format(self):
        """ Format the data from the record class fields into a record.

        :returns: Record data
        """
        data = pack(f">253s", self.TRNDATA)
        return data
