""" AFP-specific literals and code. """

afp_record_types = [
    {"type": "BAG", "code": "D3A8C9", "value": b"\xd3\xa8\xc9", "architecture": "modca", "description": "Begin Active Environment Group"},
    {"type": "BBC", "code": "D3A8EB", "value": b"\xd3\xa8\xeb", "architecture": "modca", "description": "Begin Bar Code Object"},
    {"type": "BCA", "code": "D3A877", "value": b"\xd3\xa8\x77", "architecture": "modca", "description": "Begin Color Attribute Table"},
    {"type": "BDA", "code": "D3EEEB", "value": b"\xd3\xee\xeb", "architecture": "modca", "description": "Bar Code Data"},
    {"type": "BDD", "code": "D3A6EB", "value": b"\xd3\xa6\xeb", "architecture": "modca", "description": "Bar Code Data Descriptor"},
    {"type": "BDG", "code": "D3A8C4", "value": b"\xd3\xa8\xc4", "architecture": "modca", "description": "Begin Document Environment Group"},
    {"type": "BDI", "code": "D3A8A7", "value": b"\xd3\xa8\xa7", "architecture": "modca", "description": "Begin Document Index"},
    {"type": "BDT", "code": "D3A8A8", "value": b"\xd3\xa8\xa8", "architecture": "modca", "description": "Begin Document"},
    {"type": "BFM", "code": "D3A8CD", "value": b"\xd3\xa8\xcd", "architecture": "modca", "description": "Begin Form Map"},
    {"type": "BGR", "code": "D3A8BB", "value": b"\xd3\xa8\xbb", "architecture": "modca", "description": "Begin Graphics Object"},
    {"type": "BIM", "code": "D3A8FB", "value": b"\xd3\xa8\xfb", "architecture": "modca", "description": "Begin Image Object"},
    {"type": "BMM", "code": "D3A8CC", "value": b"\xd3\xa8\xcc", "architecture": "modca", "description": "Begin Medium Map"},
    {"type": "BMO", "code": "D3A8DF", "value": b"\xd3\xa8\xdf", "architecture": "modca", "description": "Begin Overlay"},
    {"type": "BNG", "code": "D3A8AD", "value": b"\xd3\xa8\xad", "architecture": "modca", "description": "Begin Named Page Group"},
    {"type": "BOC", "code": "D3A892", "value": b"\xd3\xa8\x92", "architecture": "modca", "description": "Begin Object Container"},
    {"type": "BOG", "code": "D3A8C7", "value": b"\xd3\xa8\xc7", "architecture": "modca", "description": "Begin Object Environment Group"},
    {"type": "BPG", "code": "D3A8AF", "value": b"\xd3\xa8\xaf", "architecture": "modca", "description": "Begin Page"},
    {"type": "BPS", "code": "D3A85F", "value": b"\xd3\xa8\x5f", "architecture": "modca", "description": "Begin Page Segment"},
    {"type": "BPT", "code": "D3A89B", "value": b"\xd3\xa8\x9b", "architecture": "modca", "description": "Begin Presentation Text Object"},
    {"type": "BRG", "code": "D3A8C6", "value": b"\xd3\xa8\xc6", "architecture": "modca", "description": "Begin Resource Group"},
    {"type": "BRS", "code": "D3A8CE", "value": b"\xd3\xa8\xce", "architecture": "modca", "description": "Begin Resource"},
    {"type": "BSG", "code": "D3A8D9", "value": b"\xd3\xa8\xd9", "architecture": "modca", "description": "Begin Resource Environment Group"},
    {"type": "CAT", "code": "D3B077", "value": b"\xd3\xb0\x77", "architecture": "modca", "description": "Color Attribute Table"},
    {"type": "CDD", "code": "D3A692", "value": b"\xd3\xa6\x92", "architecture": "modca", "description": "Container Data Descriptor"},
    {"type": "EAG", "code": "D3A9C9", "value": b"\xd3\xa9\xc9", "architecture": "modca", "description": "End Active Environment Group"},
    {"type": "EAG", "code": "D3A9EB", "value": b"\xd3\xa9\xeb", "architecture": "modca", "description": "End Active Environment Group"},
    {"type": "ECA", "code": "D3A977", "value": b"\xd3\xa9\x77", "architecture": "modca", "description": "End Color Attribute Table"},
    {"type": "EDG", "code": "D3A9C4", "value": b"\xd3\xa9\xc4", "architecture": "modca", "description": "End Document Environment Group"},
    {"type": "EDI", "code": "D3A9A7", "value": b"\xd3\xa9\xa7", "architecture": "modca", "description": "End Document Index"},
    {"type": "EDT", "code": "D3A9A8", "value": b"\xd3\xa9\xa8", "architecture": "modca", "description": "End Document"},
    {"type": "EFM", "code": "D3A9CD", "value": b"\xd3\xa9\xcd", "architecture": "modca", "description": "End Form Map"},
    {"type": "EGR", "code": "D3A9BB", "value": b"\xd3\xa9\xbb", "architecture": "modca", "description": "End Graphics Object"},
    {"type": "EIM", "code": "D3A9FB", "value": b"\xd3\xa9\xfb", "architecture": "modca", "description": "End Image Object"},
    {"type": "EMM", "code": "D3A9CC", "value": b"\xd3\xa9\xcc", "architecture": "modca", "description": "End Medium Map"},
    {"type": "EMO", "code": "D3A9DF", "value": b"\xd3\xa9\xdf", "architecture": "modca", "description": "End Overlay"},
    {"type": "ENG", "code": "D3A9AD", "value": b"\xd3\xa9\xad", "architecture": "modca", "description": "End Named Page Group"},
    {"type": "EOC", "code": "D3A992", "value": b"\xd3\xa9\x92", "architecture": "modca", "description": "End Object Container"},
    {"type": "EOG", "code": "D3A9C7", "value": b"\xd3\xa9\xc7", "architecture": "modca", "description": "End Object Environment Group"},
    {"type": "EPG", "code": "D3A9AF", "value": b"\xd3\xa9\xaf", "architecture": "modca", "description": "End Page"},
    {"type": "EPS", "code": "D3A95F", "value": b"\xd3\xa9\x5f", "architecture": "modca", "description": "End Page Segment"},
    {"type": "EPT", "code": "D3A99B", "value": b"\xd3\xa9\x9b", "architecture": "modca", "description": "End Presentation Text Object"},
    {"type": "EPT", "code": "D3A9C6", "value": b"\xd3\xa9\xc6", "architecture": "modca", "description": "End Presentation Text Object"},
    {"type": "ERS", "code": "D3A9CE", "value": b"\xd3\xa9\xce", "architecture": "modca", "description": "End Resource"},
    {"type": "ESG", "code": "D3A9D9", "value": b"\xd3\xa9\xd9", "architecture": "modca", "description": "End Resource Environment Group"},
    {"type": "ESG", "code": "D3EEBB", "value": b"\xd3\xee\xbb", "architecture": "modca", "description": "End Resource Environment Group"},
    {"type": "GDD", "code": "D3A6BB", "value": b"\xd3\xa6\xbb", "architecture": "modca", "description": "Graphics Data Descriptor"},
    {"type": "IDD", "code": "D3A6FB", "value": b"\xd3\xa6\xfb", "architecture": "modca", "description": "Image Data Descriptor"},
    {"type": "IEL", "code": "D3B2A7", "value": b"\xd3\xb2\xa7", "architecture": "modca", "description": "Index Element"},
    {"type": "IMM", "code": "D3ABCC", "value": b"\xd3\xab\xcc", "architecture": "modca", "description": "Invoke Medium Map"},
    {"type": "IOB", "code": "D3AFC3", "value": b"\xd3\xaf\xc3", "architecture": "modca", "description": "Include Object"},
    {"type": "IPD", "code": "D3EEFB", "value": b"\xd3\xee\xfb", "architecture": "modca", "description": "Image Picture Data"},
    {"type": "IPG", "code": "D3AFAF", "value": b"\xd3\xaf\xaf", "architecture": "modca", "description": "Include Page"},
    {"type": "IPO", "code": "D3AFD8", "value": b"\xd3\xaf\xd8", "architecture": "modca", "description": "Include Page Overlay"},
    {"type": "IPS", "code": "D3AF5F", "value": b"\xd3\xaf\x5f", "architecture": "modca", "description": "Include Page Segment"},
    {"type": "LLE", "code": "D3B490", "value": b"\xd3\xb4\x90", "architecture": "modca", "description": "Link Logical Element"},
    {"type": "MBC", "code": "D3ABEB", "value": b"\xd3\xab\xeb", "architecture": "modca", "description": "Map Bar Code Object"},
    {"type": "MCA", "code": "D3AB77", "value": b"\xd3\xab\x77", "architecture": "modca", "description": "Map Color Attribute Table"},
    {"type": "MCC", "code": "D3A288", "value": b"\xd3\xa2\x88", "architecture": "modca", "description": "Medium Copy Count"},
    {"type": "MCD", "code": "D3AB92", "value": b"\xd3\xab\x92", "architecture": "modca", "description": "Map Container Data"},
    {"type": "MCF", "code": "D3AB8A", "value": b"\xd3\xab\x8a", "architecture": "modca", "description": "Map Coded Font"},
    {"type": "MDD", "code": "D3A688", "value": b"\xd3\xa6\x88", "architecture": "modca", "description": "Medium Descriptor"},
    {"type": "MDR", "code": "D3ABC3", "value": b"\xd3\xab\xc3", "architecture": "modca", "description": "Map Data Resource"},
    {"type": "MFC", "code": "D3A088", "value": b"\xd3\xa0\x88", "architecture": "modca", "description": "Medium Finishing Control"},
    {"type": "MGO", "code": "D3ABBB", "value": b"\xd3\xab\xbb", "architecture": "modca", "description": "Map Graphics Object"},
    {"type": "MIO", "code": "D3ABFB", "value": b"\xd3\xab\xfb", "architecture": "modca", "description": "Map Image Object"},
    {"type": "MMC", "code": "D3A788", "value": b"\xd3\xa7\x88", "architecture": "modca", "description": "Medium Modification Control"},
    {"type": "MMO", "code": "D3B1DF", "value": b"\xd3\xb1\xdf", "architecture": "modca", "description": "Map Medium Overlay"},
    {"type": "MMT", "code": "D3AB88", "value": b"\xd3\xab\x88", "architecture": "modca", "description": "Map Media Type"},
    {"type": "MPG", "code": "D3ABAF", "value": b"\xd3\xab\xaf", "architecture": "modca", "description": "Map Page"},
    {"type": "MPO", "code": "D3ABD8", "value": b"\xd3\xab\xd8", "architecture": "modca", "description": "Map Page Overlay"},
    {"type": "MPS", "code": "D3B15F", "value": b"\xd3\xb1\x5f", "architecture": "modca", "description": "Map Page Segment"},
    {"type": "MPS", "code": "D3ABEA", "value": b"\xd3\xab\xea", "architecture": "modca", "description": "Map Page Segment"},
    {"type": "NOP", "code": "D3EEEE", "value": b"\xd3\xee\xee", "architecture": "modca", "description": "No Operation"},
    {"type": "OBD", "code": "D3A66B", "value": b"\xd3\xa6\x6b", "architecture": "modca", "description": "Object Area Descriptor"},
    {"type": "OBP", "code": "D3AC6B", "value": b"\xd3\xac\x6b", "architecture": "modca", "description": "Object Area Position"},
    {"type": "OCD", "code": "D3EE92", "value": b"\xd3\xee\x92", "architecture": "modca", "description": "Object Container Data"},
    {"type": "PFC", "code": "D3B288", "value": b"\xd3\xb2\x88", "architecture": "modca", "description": "Presentation Fidelity Control"},
    {"type": "PGD", "code": "D3A6AF", "value": b"\xd3\xa6\xaf", "architecture": "modca", "description": "Page Descriptor"},
    {"type": "PGP", "code": "D3B1AF", "value": b"\xd3\xb1\xaf", "architecture": "modca", "description": "Page Position"},
    {"type": "PMC", "code": "D3A7AF", "value": b"\xd3\xa7\xaf", "architecture": "modca", "description": "Page Modification Control"},
    {"type": "PPO", "code": "D3ADC3", "value": b"\xd3\xad\xc3", "architecture": "modca", "description": "Preprocess Presentation Object"},
    {"type": "PTD", "code": "D3B19B", "value": b"\xd3\xb1\x9b", "architecture": "modca", "description": "Presentation Text Data Descriptor"},
    {"type": "PTX", "code": "D3EE9B", "value": b"\xd3\xee\x9b", "architecture": "modca", "description": "Presentation Text Data"},
    {"type": "TLE", "code": "D3A090", "value": b"\xd3\xa0\x90", "architecture": "modca", "description": "Tag Logical Element"},
    {"type": "BCF", "code": "D3A88A", "value": b"\xd3\xa8\x8a", "architecture": "foca", "description": "Begin Coded Font"},
    {"type": "BCP", "code": "D3A887", "value": b"\xd3\xa8\x87", "architecture": "foca", "description": "Begin Code Page"},
    {"type": "BFN", "code": "D3A889", "value": b"\xd3\xa8\x89", "architecture": "foca", "description": "Begin Font"},
    {"type": "CFC", "code": "D3A78A", "value": b"\xd3\xa7\x8a", "architecture": "foca", "description": "Coded Font Control"},
    {"type": "CFI", "code": "D38C8A", "value": b"\xd3\x8C\x8a", "architecture": "foca", "description": "Coded Font Index"},
    {"type": "CPC", "code": "D3A787", "value": b"\xd3\xa7\x87", "architecture": "foca", "description": "Code Page Control"},
    {"type": "CPD", "code": "D3A687", "value": b"\xd3\xa6\x87", "architecture": "foca", "description": "Code Page Descriptor"},
    {"type": "CPI", "code": "D38C87", "value": b"\xd3\x8C\x87", "architecture": "foca", "description": "Code Page Index"},
    {"type": "ECF", "code": "D3A98A", "value": b"\xd3\xa9\x8a", "architecture": "foca", "description": "End Coded Font"},
    {"type": "ECP", "code": "D3A987", "value": b"\xd3\xa9\x87", "architecture": "foca", "description": "End Code Page"},
    {"type": "EFN", "code": "D3A989", "value": b"\xd3\xa9\x89", "architecture": "foca", "description": "End Font"},
    {"type": "FNC", "code": "D3A789", "value": b"\xd3\xa7\x89", "architecture": "foca", "description": "Font Control"},
    {"type": "FND", "code": "D3A689", "value": b"\xd3\xa6\x89", "architecture": "foca", "description": "Font Descriptor"},
    {"type": "FNG", "code": "D3EE89", "value": b"\xd3\xee\x89", "architecture": "foca", "description": "Font Patterns"},
    {"type": "FNI", "code": "D38C89", "value": b"\xd3\x8c\x89", "architecture": "foca", "description": "Font Index"},
    {"type": "FNM", "code": "D3A289", "value": b"\xd3\xa2\x89", "architecture": "foca", "description": "Font Patterns Map"},
    {"type": "FNN", "code": "D3AB89", "value": b"\xd3\xab\x89", "architecture": "foca", "description": "Font Name Map"},
    {"type": "FNO", "code": "D3AE89", "value": b"\xd3\xae\x89", "architecture": "foca", "description": "Font Orientation"},
    {"type": "FNP", "code": "D3AC89", "value": b"\xd3\xac\x89", "architecture": "foca", "description": "Font Position"},
    {"type": "GAD", "code": "D3EEBB", "value": b"\xd3\xee\xbb", "architecture": "goca", "description": "Graphics Data"},
    {"type": "GDD", "code": "D3A6BB", "value": b"\xd3\xa6\xbb", "architecture": "goca", "description": "Graphics Data Descriptor"},
    {"type": "IDD", "code": "D3A6FB", "value": b"\xd3\xa6\xfb", "architecture": "ioca", "description": "Image Data Descriptor"},
    {"type": "IPD", "code": "D3EEFB", "value": b"\xd3\xee\xfb", "architecture": "ioca", "description": "Image Picture Data"},
    {"type": "BDA", "code": "D3EEEB", "value": b"\xd3\xee\xeb", "architecture": "bcoca", "description": "Bar Code Data"},
    {"type": "BDD", "code": "D3A6EB", "value": b"\xd3\xa6\xeb", "architecture": "bcoca", "description": "Bar Code Data Descriptor"},
    ]

# Setup afp record type lookup.
#afp_rec_type = []
#for x in xrange(256):
#    afp_rec_type.append([])
#    for y in xrange(256):
#        afp_rec_type[x].append(None)
#for afp_record_type in afp_record_types:
#    #xint = int(afp_record_type["value"][1:2], 16)
#    #xint = chr(int(afp_record_type["value"][2:3], base=16)) + chr(int(afp_record_type["value"][2:3], base=16))
#    xint = afp_record_type["code"][2:4].decode("hex")
#    print
#    afp_rec_type[xint][yint] = afp_record_type
#    #afp_rec_type[afp_record_type["value"][1:2]][afp_record_type["value"][2:3]] = afp_record_type
#    #wrk_str.encode("hex") and wrk_str.decode("hex") 
afp_rec_type = {}
for afp_record_type in afp_record_types:
    #afp_rec_type[afp_record_type["code"]] = afp_record_type
    afp_rec_type[afp_record_type["value"]] = afp_record_type

afp_ptx_record_functions = [
    {"type": "AMB", "value": b"\xD2", "chained": False, "description": "Absolute Move Baseline"},
    {"type": "AMB-C", "value": b"\xd3", "chained": True, "description": "Absolute Move Baseline"},
    {"type": "AMI", "value": b"\xC6", "chained": False, "description": "Absolute Move Inline"},
    {"type": "AMI-C", "value": b"\xC7", "chained": True, "description": "Absolute Move Inline"},
    {"type": "BLN", "value": b"\xD8", "chained": False, "description": "Begin Line"},
    {"type": "BLN-C", "value": b"\xD9", "chained": True, "description": "Begin Line"},
    {"type": "BSU", "value": b"\xF2", "chained": False, "description": "Begin Suppression"},
    {"type": "BSU-C", "value": b"\xF3", "chained": True, "description": "Begin Suppression"},
    {"type": "DBR", "value": b"\xE6", "chained": False, "description": "Draw Baseline Rule"},
    {"type": "DBR-C", "value": b"\xE7", "chained": True, "description": "Draw Baseline Rule"},
    {"type": "DIR", "value": b"\xE4", "chained": False, "description": "Draw Inline Rule"},
    {"type": "DIR-C", "value": b"\xE5", "chained": True, "description": "Draw Inline Rule"},
    {"type": "ESU", "value": b"\xF4", "chained": False, "description": "End Suppression"},
    {"type": "ESU-C", "value": b"\xF5", "chained": True, "description": "End Suppression"},
    {"type": "NOP", "value": b"\xF8", "chained": False, "description": "No Operation"},
    {"type": "NOP-C", "value": b"\xF9", "chained": True, "description": "No Operation"},
    {"type": "OVS", "value": b"\x72", "chained": False, "description": "Overstrike"},
    {"type": "OVS-C", "value": b"\x73", "chained": True, "description": "Overstrike"},
    {"type": "RMB", "value": b"\xD4", "chained": False, "description": "Relative Move Baseline"},
    {"type": "RMB-C", "value": b"\xD5", "chained": True, "description": "Relative Move Baseline"},
    {"type": "RMI", "value": b"\xC8", "chained": False, "description": "Relative Move Inline"},
    {"type": "RMI-C", "value": b"\xC9", "chained": True, "description": "Relative Move Inline"},
    {"type": "RPS", "value": b"\xEE", "chained": False, "description": "Repeat String"},
    {"type": "RPS-C", "value": b"\xEF", "chained": True, "description": "Repeat String"},
    {"type": "SBI", "value": b"\xD0", "chained": False, "description": "Set Baseline Increment"},
    {"type": "SBI-C", "value": b"\xD1", "chained": True, "description": "Set Baseline Increment"},
    {"type": "SCF", "value": b"\xF0", "chained": False, "description": "Set Coded Font Local"},
    {"type": "SCF-C", "value": b"\xF1", "chained": True, "description": "Set Coded Font Local"},
    {"type": "SEC", "value": b"\x80", "chained": False, "description": "Set Extended Text Color"},
    {"type": "SEC-C", "value": b"\x81", "chained": True, "description": "Set Extended Text Color"},
    {"type": "SIA", "value": b"\xC2", "chained": False, "description": "Set Intercharacter Adjustment"},
    {"type": "SIA-C", "value": b"\xC3", "chained": True, "description": "Set Intercharacter Adjustment"},
    {"type": "SIM", "value": b"\xC0", "chained": False, "description": "Set Inline Margin"},
    {"type": "SIM-C", "value": b"\xC1", "chained": True, "description": "Set Inline Margin"},
    {"type": "STC", "value": b"\x74", "chained": False, "description": "Set Text Color"},
    {"type": "STC-C", "value": b"\x75", "chained": True, "description": "Set Text Color"},
    {"type": "STO", "value": b"\xF6", "chained": False, "description": "Set Text Orientation"},
    {"type": "STO-C", "value": b"\xF7", "chained": True, "description": "Set Text Orientation"},
    {"type": "SVI", "value": b"\xC4", "chained": False, "description": "Set Variable Space Character Increment"},
    {"type": "SVI-C", "value": b"\xC5", "chained": True, "description": "Set Variable Space Character Increment"},
    {"type": "TBM", "value": b"\x78", "chained": False, "description": "Temporary Baseline Move"},
    {"type": "TBM-C", "value": b"\x79", "chained": True, "description": "Temporary Baseline Move"},
    {"type": "TRN", "value": b"\xDA", "chained": False, "description": "Transparent Data"},
    {"type": "TRN-C", "value": b"\xDB", "chained": True, "description": "Transparent Data"},
    {"type": "USC", "value": b"\x76", "chained": False, "description": "Underscore"},
    {"type": "USC-C", "value": b"\x77", "chained": True, "description": "Underscore"},
    ]

# Initialize PTX function lookups.
afp_ptx_by_value = {}
for afp_ptx_record_function in afp_ptx_record_functions:
    _key = afp_ptx_record_function["value"]
    afp_ptx_by_value[_key] = afp_ptx_record_function
afp_ptx_by_type = {}
for afp_ptx_record_function in afp_ptx_record_functions:
    _key = afp_ptx_record_function["type"]
    afp_ptx_by_type[_key] = afp_ptx_record_function

        
class StreamAFP:
    """ Code functions of afp printstream files. """

    def __init__(self):
        pass
