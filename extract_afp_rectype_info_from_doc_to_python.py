import sys
import re

#setup
foca_rec_type_data = """
    BCF                X'D3A88A'         Begin Coded Font
    BCP                X'D3A887'         Begin Code Page
    BFN                X'D3A889'         Begin Font
    CFC                X'D3A78A'         Coded Font Control
    CFI                X'D38C8A'         Coded Font Index
    CPC                X'D3A787'         Code Page Control
    CPD                X'D3A687'         Code Page Descriptor
    CPI                X'D38C87'         Code Page Index
    ECF                X'D3A98A'         End Coded Font
    ECP                X'D3A987'         End Code Page
    EFN                X'D3A989'         End Font
    FNC                X'D3A789'         Font Control
    FND                X'D3A689'         Font Descriptor
    FNG                X'D3EE89'         Font Patterns
    FNI                X'D38C89'         Font Index
    FNM                X'D3A289'         Font Patterns Map
    FNN                X'D3AB89'         Font Names
    FNO                X'D3AE89'         Font Orientation
    FNP                X'D3AC89'         Font Position
    """
types = []
#open input file      
input=open('afp_rec_types_modca_print.txt','r')
output=open('afp_rec_types_modca_c.txt','w')
rec_count = 0
#output.write("afp_record_types = [\n")
#process input file
for line in input:
    p = re.compile('\s\s\s\s(.+)\s\((\w\w\w)\)\s')
    m = p.match(line)
    if m:
        rec_desc = m.group(1)
        rec_type = m.group(2)
    p = re.compile('\s\s\s\s\s\s\s\w\w\w\s\(X\'(\w\w\w\w\w\w)\'\)\s')
    m = p.match(line)
    if m:
        rec_count += 1
        rec_code = m.group(1)
        print("(%s) (%s) (%s)" % (rec_code, rec_type, rec_desc))
        #output.write("    {'type': '%s', 'code': '%s', 'value': '\\x%s\\x%s\\x%s', 'architecture': 'modca', 'description': '%s'},\n" % 
        #    (rec_type, rec_code, rec_code[0:2], rec_code[2:4], rec_code[4:6], rec_desc))
        type_line = '    load_afp_rtype(0x%s, 0x%s, 0x%s, "%s", "%s", "MODCA", "%s");\n' % \
            (rec_code[0:2], rec_code[2:4], rec_code[4:6], rec_type, rec_code, rec_desc)
        type = {}
        type['type'] = rec_type
        type['line'] = type_line
        types.append(type)

#process foca data
#  sample:    NOP                X'D3EEEE'         No Operation
foca_lines = foca_rec_type_data.split('\n')
for line in foca_lines:
    p = re.compile('\s\s\s\s(.+)\s+X\'(.+)\'\s+(.+)')
    m = p.match(line)
    if m:
        rec_count += 1
        rec_type = m.group(1).strip()
        rec_code = m.group(2).strip()
        rec_desc = m.group(3).strip()
        print("(%s) (%s) (%s)" % (rec_code, rec_type, rec_desc))
        type_line = '    load_afp_rtype(0x%s, 0x%s, 0x%s, "%s", "%s", "FOCA",  "%s");\n' % \
            (rec_code[0:2], rec_code[2:4], rec_code[4:6], rec_type, rec_code, rec_desc)
        type = {}
        type['type'] = rec_type
        type['line'] = type_line
        types.append(type)

# Write types.
types_sorted = sorted(types, key=lambda k: k['type']) 
for type in types_sorted:
    output.write(type['line'])
#close output file
input.close()
#output.write("    ]\n")
output.close()
print("\nTotal record types:  %d" % rec_count)

sys.exit(0)
