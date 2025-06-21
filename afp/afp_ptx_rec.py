""" AFP PTX Record """

from struct import pack, unpack

import stream_afp
from afp_ptx_amb_seq import AFP_PTX_AMB
from afp_ptx_ami_seq import AFP_PTX_AMI
from afp_ptx_bln_seq import AFP_PTX_BLN
from afp_ptx_bsu_seq import AFP_PTX_BSU
from afp_ptx_dbr_seq import AFP_PTX_DBR
from afp_ptx_dir_seq import AFP_PTX_DIR
from afp_ptx_esu_seq import AFP_PTX_ESU
from afp_ptx_nop_seq import AFP_PTX_NOP
from afp_ptx_ovs_seq import AFP_PTX_OVS
from afp_ptx_rmb_seq import AFP_PTX_RMB
from afp_ptx_rmi_seq import AFP_PTX_RMI
from afp_ptx_rps_seq import AFP_PTX_RPS
from afp_ptx_sbi_seq import AFP_PTX_SBI
from afp_ptx_sec_seq import AFP_PTX_SEC
from afp_ptx_sia_seq import AFP_PTX_SIA
from afp_ptx_sim_seq import AFP_PTX_SIM
from afp_ptx_stc_seq import AFP_PTX_STC
from afp_ptx_sto_seq import AFP_PTX_STO
from afp_ptx_svi_seq import AFP_PTX_SVI
from afp_ptx_tbm_seq import AFP_PTX_TBM
from afp_ptx_trn_seq import AFP_PTX_TRN
from afp_ptx_usc_seq import AFP_PTX_USC
from stream_field_afp import StreamFieldAFP
from stream_function_afp import StreamFunctionAFP


afp_ptx_fields_list = [
    StreamFieldAFP(name="PTOCAdat", offset=0, length=32761, type="UNDF", optional=True, exception='\x00', range_values=['', '', ''], meaning=['Up to 32,759 bytes of', 'PTOCA-defined data', '']),
    ]
afp_ptx_fields = {}
for field in afp_ptx_fields_list:
    afp_ptx_fields[field.name] = field


class AFP_PTX:

    def __init__(self):
                                        # Offset: Length: Type: Optional: Exception: Range:                Meaning:
        self.PTOCAdat = None            #      0   32761  UNDF  y         X'00'                            Up to 32,759 bytes of
                                        #                                                                  PTOCA-defined data

    def parse(self, data):
        """ Parse the data from a record into the record class fields.

        :param bytes data: Record data
        """
        start = 0
        length = len(data)
        while start < length:
            cur_function = StreamFunctionAFP()
            value = ""
            if data[start:start + 1] == b"\x2B":
                cur_function.length = 2
                cur_function.type = "ESC"
            else:
                # cur_function.length = struct.unpack(">h", self.data[start:start + 1])
                # cur_function.length = int(self.data[start:start + 1], 2)
                cur_function.length = ord(data[start:start + 1])
                cur_function.type = stream_afp.afp_ptx_by_value[data[start + 1:start + 2]]["type"]
                seq_data = data[start + 2:start + 2 + cur_function.length - 2]
                if (cur_function.type == "TRN") or (cur_function.type == "TRN-C"):
                    seq = AFP_PTX_TRN()
                    seq.parse(seq_data)
                    print(seq)
            print(f"  PTX function:  type={cur_function.type} start={start} length={cur_function.length} data=()")
            start += cur_function.length

    def format(self):
        """ Format the data from the record class fields into a record.

        :returns: Record data
        """
        data = pack(f">{self.PTOCAdat.len()}s", self.PTOCAdat)
        return data
