import re
import sys


#setup
types = []
fields = []
#open input file
output_path = "C:\\Users\\print\\Documents\\stream\\printstreamer"
input = open("C:\\Users\\print\\Documents\\stream\\modca_rec_structure_print.txt", "r")
output = open("C:\\Users\\print\\Documents\\stream\\printstreamer\\modca_rec_structure_c.txt", "w")
rec_types = 0
rec_type = ""
class_def = False
field_def = False
#process input file
for line in input:
    # Fix bad character.
    line = line.replace("\xad", "-").rstrip()
    #if rec_type == "IOB":
    #    print line

    # Skip the line.
    if ("Note:" in line[0:10]):
        pass
    else:
        # End field definition:
        #
        if (len(line) == 0) \
            or (line[0:10] != "          ") \
            or ("Note:" in line[0:10]):
            if field_def:
                fields.append(field)
                field_def = False
                if rec_type == "IOB":
                    print(field)
                    print("end field")

        # End class section:
        #
        if (len(line) == 0):
            class_def = False
            if rec_type == "IOB":
                print("end class")
        
        # Start record type:
        # BAG (X'D3A8C9') Syntax
        p = re.compile('\s+([A-Z][A-Z][A-Z])\s\(.+\)\sSyntax')
        m = p.match(line)
        if m:
            if rec_types > 0:
                # Save last rec type.
                type['fields'] = fields
                types.append(type)
                fields = []
                #if rec_type == "IOB":
                #    sys.exit(0)
            rec_types += 1
            rec_type = m.group(1)
            type = {}
            type['type'] = rec_type
            print(rec_type)

        # Start field definition:
        if class_def:
            # Capture and parse offset field.
            if len(line) >= 10:
                offset_string = line[offset_loc:type_loc].strip()
                if offset_string != "":
                    if rec_type == "IOB":
                        print("offset_string=(%s)" % offset_string)
                    # Init values.
                    field = {}
                    field['offset'] = ""
                    field['length'] = ""
                    field['end'] = ""
                    field['type'] = ""
                    field['name'] = ""
                    field['range'] = ""
                    field['meaning'] = ""
                    field['optional'] = ""
                    field['exception'] = ""
                    # Parse offset.
                    p = re.compile('\s?\s?\s?\s?([0-9]+)\-?([0-9]+|n)?')
                    m = p.match(offset_string)
                    if m:
                        field_def = True
                        if rec_type == "IOB":
                            print("field begin")
                        field['offset'] = int(m.group(1))
                        if (m.group(2) is None) or (m.group(2) == ""):
                            field['end'] = field['offset']
                            field['length'] = 1
                        elif (m.group(2) == "n"):
                            field['end'] = 32760
                            field['length'] = 32760 - field['offset'] + 1
                        else:
                            field['end'] = int(m.group(2))
                            field['length'] = field['end'] - field['offset'] + 1
                if field_def:
                    # Capture other fields.
                    field['type'] += line[type_loc:name_loc].strip()
                    field['name'] += line[name_loc:range_loc].strip()
                    field['range'] += line[range_loc:meaning_loc].strip() + "\t"
                    field['meaning'] += line[meaning_loc:optional_loc].strip() + "\t"
                    field['optional'] = line[optional_loc:exception_loc].strip()
                    if field['optional'] == "M":
                        field['optional'] = "n"
                    else:
                        field['optional'] = "y"
                    field['exception'] += line[exception_loc:].strip()
                if rec_type == "IOB":
                    print(field)

        # Start class section:
        #     Offset            Type       Name                Range              Meaning
        p = re.compile('\s*?Offset\s+Type\s+Name\s+Range\s+Meaning\s+M\/O\s+Exc')
        m = p.match(line)
        if m:
            class_def = True
            offset_loc = line.index("Offset")
            type_loc = line.index("Type")
            name_loc = line.index("Name")
            range_loc = line.index("Range")
            meaning_loc = line.index("Meaning")
            optional_loc = line.index("M/O")
            exception_loc = line.index("Exc")
            print("offset_loc=%i" % offset_loc)
            print("type_loc=%i" % type_loc)

# Save last class.
if rec_types > 0:
    # Save last rec type.
    type['fields'] = fields
    types.append(type)
    fields = []
# Write types.
types_sorted = sorted(types, key=lambda k: k['type']) 
for type in types_sorted:
    output.write("%s\n" % (type['type']))
    #fields_sorted = sorted(type['fields'], key=lambda l: l['offset']) 
    fields_sorted = type['fields']
    for field in fields_sorted:
        output.write("    offset=%s end=%s length=%s\n" % (field['offset'], field['end'], field['length']))
#close output file
input.close()
output.close()

print("\nTotal record types:  %d" % rec_types)

# Create afp_recs class files.
for type in types_sorted:
    ### Open output files.
    hdrfile = open("%s\\afp_%s_rec_class.h" % (output_path, type['type'].lower()), "w")
    classfile = open("%s\\afp_%s_rec_class.cpp" % (output_path, type['type'].lower()), "w")
    fields_sorted = type['fields']

    
    ### Write header file.
    # Write header.
    data = """#include <stdio.h>

#pragma once
class afp_%s_rec_class
{
public:
                                //Offset: Length: Type: Optional: Exception: Range:                Meaning:\n""" % type['type'].lower()
    hdrfile.write(data)

    # Write detail.
    reserved_count = 0
    for field in fields_sorted:
        if field['type'] == "":
            if ("triplet" in field['meaning']) or ("Triplet" in field['meaning']):
                name = "Triplets"
            else:
                reserved_count += 1
                name = "Reserved_%i" % (reserved_count)
        else:
            name = field['name']
        if field['length'] > 1:
            data = "    char %s[%i];" % (name, field['length'])
        else:
            data = "    char %s;" % (name)
        #if field['type'] == "CHAR":
        #    if field['length'] == 1:
        #        data = "    char %s[%i];" % (field['name'], field['length'])
        #    else:
        #        data = "    char %s;" % (field['name'])
        #elif field['type'] == "UNDF":
        #    data = "    char %s[%i];" % (field['name'], field['length'])
        #elif field['type'] == "":
        #    if ("triplet" in field['meaning']) or ("Triplet" in field['meaning']):
        #        data = "    char Triplets[%i];" % (field['length'])
        #    else:
        #        reserved_count += 1
        #        data = "    char reserved_%i[%i];" % (reserved_count, field['length'])
        #elif field['type'] == "CODE":
        #    data = "    char %s;" % (field['name'])
        #elif field['type'] == "BITS":
        #    data = "    char %s;" % (field['name'])
        #elif field['type'] == "SBIN":
        #    data = "    char %s[%i];" % (field['name'], field['length'])
        #elif field['type'] == "UBIN":
        #    data = "    char %s[%i];" % (field['name'], field['length'])
        #else:
        #    print("Error:  Unknown field type ->(%s)" % field['type']
        #    sys.exit(1)
        range_value = field['range'].split("\t")
        meaning = field['meaning'].split("\t")
        data = "%-30.30s  // %5i   %5i  %-4.4s  %-1.1s         %-5.5s      %-20.20s  %s\n" % (data, field['offset'], field['length'], field['type'], field['optional'], field['exception'], range[0], meaning[0])
        hdrfile.write(data)
        line_count = len(meaning)
        if len(range_value) > line_count:
            line_count = len(range_value)
        if line_count > 1:
            for line in range(1, line_count - 1):
                data = "%-30.30s  // %5.5s   %5.5s  %-4.4s  %-1.1s         %-5.5s      %-20.20s  %s\n" % ("", "", "", "", "", "", range_value[line], meaning[line])
                hdrfile.write(data)

    # Write footer.
    data = """

    afp_%s_rec_class(void);
    ~afp_%s_rec_class(void);

private:

};\n""" % (type['type'].lower(), type['type'].lower())
    hdrfile.write(data)

    
    ### Write class file.
    # Write body.
    data = """#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

#include "afp_%s_rec_class.h"

afp_%s_rec_class::afp_%s_rec_class(void)
{
}


afp_%s_rec_class::~afp_%s_rec_class(void)
{
}
\n""" % (type['type'].lower(), type['type'].lower(), type['type'].lower(), type['type'].lower(), type['type'].lower())
    classfile.write(data)

    
    ### Close output files.
    hdrfile.close()
    classfile.close()

sys.exit(0)
