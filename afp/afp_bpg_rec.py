""" AFP BPG Record """

from struct import pack, unpack

import stream_afp
from stream_field_afp import StreamFieldAFP
from stream_function_afp import StreamFunctionAFP


afp_bpg_fields_list = [
    StreamFieldAFP(name="PageName", offset=0, length=8, type="CHAR", optional=True, exception='\x02', range_values=['', ''], meaning=['Name of the page', '']),
    StreamFieldAFP(name="Triplets", offset=8, length=32753, type="", optional=True, exception='\x10', range_values=['', '', ''], meaning=['See "BPG Semantics" for', 'triplet applicability.', '']),
    ]
afp_bpg_fields = {}
for field in afp_bpg_fields_list:
    afp_bpg_fields[field.name] = field


class AFP_BPG:

    def __init__(self, segment):
        self.segment = segment
        self.page = self.segment.cur_page
        self.page_width = None
        self.page_height = None
        # Offset: Length: Type: Optional: Exception: Range:                Meaning:
        self.PageName = None            #      0       8  CHAR  y         X'02'                            Name of the page
        self.Triplets = None            #      8   32753        y         X'10'                            See "BPG Semantics" for
                                        #                                                                  triplet applicability.

    def parse(self, data):
        """ Parse the data from a record into the record class fields.

        :param str data: Record data
        """
        if len(data) > 0:
            self.PageName, self.Triplets = unpack(f">8s{len(data) - 8}s", data)
        else:
            self.PageName = ""
            self.Triplets = ""

        # data = self.Triplets
        # start = 0
        # length = len(data)
        # while start < length:
        #     cur_function = StreamFunctionAFP()
        #     value = ""
        #     if data[start:start + 1] == b"\x2B":
        #         cur_function.length = 2
        #         cur_function.type = "ESC"
        #     else:
        #         # cur_function.length = struct.unpack(">h", self.data[start:start + 1])
        #         # cur_function.length = int(self.data[start:start + 1], 2)
        #         cur_function.length = ord(data[start:start + 1])
        #         cur_function.type = stream_afp.afp_ptx_by_value[data[start + 1:start + 2]]["type"]
        #         seq_data = data[start + 2:start + 2 + cur_function.length - 2]
        #         if (cur_function.type == "TRN") or (cur_function.type == "TRN-C"):
        #             seq = AFP_PTX_TRN()
        #             seq.parse(seq_data)
        #             self.page.text.append({'text': seq.TRNDATA, 'font_name': None, 'font_typeface': None,
        #                                    'font_size': None, 'color': None, 'color_rgb': None, 'x': self.cur_x,
        #                                    'y': self.cur_y,
        #                                    'bbox': (self.cur_x, self.cur_y, None, None)})
        #             print(seq)
        #         elif (cur_function.type == "AMI") or (cur_function.type == "AMI-C"):
        #             seq = AFP_PTX_AMI()
        #             seq.parse(seq_data)
        #             self.cur_x = seq.DSPLCMNT[0]
        #         elif (cur_function.type == "AMB") or (cur_function.type == "AMB-C"):
        #             seq = AFP_PTX_AMB()
        #             seq.parse(seq_data)
        #             self.cur_y = seq.DSPLCMNT[0]
        #         elif (cur_function.type == "RMI") or (cur_function.type == "RMI-C"):
        #             seq = AFP_PTX_RMI()
        #             seq.parse(seq_data)
        #             self.cur_x += seq.INCRMENT[0]
        #         elif (cur_function.type == "RMB") or (cur_function.type == "RMB-C"):
        #             seq = AFP_PTX_RMB()
        #             seq.parse(seq_data)
        #             self.cur_y += seq.INCRMENT[0]
        #     print(f"  PTX function:  type={cur_function.type} start={start} length={cur_function.length} data=()")
        #     start += cur_function.length

        # Parse the triplets.
        data = self.Triplets
        i = 0
        while i < len(data):
            # Check for structured field identifier
            length = unpack('>H', data[i + 1:i + 3])[0]
            sf_type = data[i:i+2].decode('latin1')

            if sf_type == 'PG':  # Page Descriptor (PGD)
                x_units = unpack('>H', data[i+16:i+18])[0]
                y_units = unpack('>H', data[i+18:i+20])[0]

                # Convert from 1/1440 inch to inches
                width_in_inches = x_units / 1440.0
                height_in_inches = y_units / 1440.0

                #page_sizes.append((width_in_inches, height_in_inches))

            i += length

    def format(self):
        """ Format the data from the record class fields into a record.

        :returns: Record data
        """
        data = pack(f">8s{self.Triplets.len()}s", self.PageName, self.Triplets)
        return data
