""" Create python structures and code from a text version of the AFP documentation.

    Create input files using ghostscript and then deleting all but the key section of record types or ptx functions:
        ps2ascii MODCA.pdf > modca.txt
        ps2ascii PTOCA.pdf > ptoca.txt
        ps2ascii FOCA.pdf > foca.txt
        ps2ascii BCOCA.pdf > bcoca.txt
        ps2ascii GOCA.pdf > goca.txt
        ps2ascii IOCA.pdf > iooca.txt

"""

import os
import re
import sys


def parse_modca_doc():
    """ Parse afp documentation formatted text file: modca """
    types = []
    fields = []

    # Open files.
    input_file = open("C:\\Users\\print\\Documents\\stream\\modca_rec_structure_print.txt", "r")
    output_path = "C:\\Users\\print\\Documents\\stream\\printstreamer\\afp"
    rec_types = 0
    rec_type = ""
    class_def = False
    field_def = False

    # Process input file.
    for line in input_file:
        # Fix bad character.
        line = line.replace("\xad", "-").rstrip()

        # Skip the line.
        if ("Note:" in line[0:10]) or ("One repeating group in the following format:" in line) or (" repeating groups in the following format:" in line):
            pass
        else:
            # End field definition:
            if (len(line) == 0) or (line[0:10] != "          ") or ("Note:" in line[0:10]) or ("When keywords occur" in line):
                if field_def:
                    fields.append(field)
                    field_def = False

            # End class section:
            if len(line) == 0:
                class_def = False

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
                rec_types += 1
                rec_type = m.group(1)
                type = {}
                type['type'] = rec_type
                print(rec_type)
                if rec_type in ["BRS", "ERS", "PPO"]:
                    pause = True

            # Start field definition:
            if class_def:
                # Capture and parse offset field.
                if len(line) >= 10:
                    offset_string = line[offset_loc:type_loc].strip()
                    if offset_string != "":
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
                            field['offset'] = int(m.group(1))
                            if (m.group(2) is None) or (m.group(2) == ""):
                                field['end'] = field['offset']
                                field['length'] = 1
                            elif m.group(2) == "n":
                                field['end'] = 32760
                                field['length'] = 32760 - field['offset'] + 1
                            else:
                                field['end'] = int(m.group(2))
                                field['length'] = field['end'] - field['offset'] + 1
                    if field_def:
                        # Capture other fields.
                        field['type'] += line[type_loc:name_loc].strip()
                        if "Zero or more keywords" in line:
                            field['name'] = "Keywords"
                            field['exception'] = "None"
                        else:
                            field['name'] += line[name_loc:range_loc].strip()
                            if field['name'] == "":
                                field['name'] = "Constant"
                            field['range'] += line[range_loc:meaning_loc].strip() + "\t"
                            field['meaning'] += line[meaning_loc:optional_loc].strip() + "\t"
                            field['optional'] = line[optional_loc:exception_loc].strip()
                            if field['optional'] == "M":
                                field['optional'] = "n"
                            else:
                                field['optional'] = "y"
                            field['exception'] += line[exception_loc:].strip()

            # Start class section:
            #     Offset            Type       Name                Range              Meaning
            p = re.compile('\|?\s*?Offset\s+Type\s+Name\s+Range\s+Meaning\s+M\/O\s+Exc')
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
        # output.write("%s\n" % (type['type']))
        # fields_sorted = sorted(type['fields'], key=lambda l: l['offset'])
        fields_sorted = type['fields']
        for field in fields_sorted:
            # output.write("    offset=%s end=%s length=%s\n" % (field['offset'], field['end'], field['length']))
            pass

    # Close files.
    input_file.close()

    print("\nTotal record types:  %d" % rec_types)

    # Create afp_recs class files.
    for rec_type in types_sorted:
        # Open output file.
        classfile = open(os.path.join(output_path, f"afp_{rec_type['type'].lower()}_rec.py"), "w")
        fields_sorted = rec_type['fields']

        # Write detail.
        reserved_count = 0
        pack_parameter_list = ""
        unpack_parameter_list = ""
        format_string = ""
        rec_class = ""
        fields_class = ""
        for field in fields_sorted:
            if field['type'] == "":
                if ("triplet" in field['meaning']) or ("Triplet" in field['meaning']):
                    name = "Triplets"
                else:
                    reserved_count += 1
                    name = "Reserved_%i" % (reserved_count)
            else:
                name = field['name']
            name_formatted = f"self.{name} = None"
            if len(pack_parameter_list) > 0:
                pack_parameter_list += ", "
            pack_parameter_list += f"self.{name}"
            if len(unpack_parameter_list) > 0:
                unpack_parameter_list += ", "
            unpack_parameter_list += f"self.{name}"
            if ("triplets" in name.lower()) or (field["length"] > 32000):
                field_format = '{self.%s.len()}s' % name
            elif field["type"] in ["CHAR", "CODE", "BITS", "UNDF", "", None]:
                field_format = f'{field["length"]}s'
            elif field["type"] == "SBIN":
                if field["length"] == 1:
                    field_format = f'b'
                elif field["length"] == 2:
                    field_format = f'h'
                elif field["length"] == 3:
                    field_format = f'xh'
                else:
                    field_format = f''
                    msg = f'Unknown SBIN field length:  {field["length"]}\n{field}'
                    print(msg)
                    # raise Exception(msg)
            elif field["type"] == "UBIN":
                if field["length"] == 1:
                    field_format = f'B'
                elif field["length"] == 2:
                    field_format = f'H'
                elif field["length"] == 3:
                    field_format = f'xH'
                else:
                    field_format = f''
                    msg = f'Unknown UBIN field length:  {field["length"]}\n{field}'
                    print(msg)
                    # raise Exception(msg)
            else:
                field_format = f''
                msg = f'Unknown field format:  {field["type"]}\n{field}'
                print(msg)
                # raise Exception(msg)
            format_string += field_format
            range_value = field['range'].split("\t")
            meaning = field['meaning'].split("\t")
            exception = field["exception"].replace("X'", "'\\x")
            rec_class += "        %-30.30s  #  %5i   %5i  %-4.4s  %-1.1s         %-5.5s      %-20.20s  %s\n" \
                    % (name_formatted, field["offset"], field["length"], field["type"], field["optional"], field["exception"], range_value[0], meaning[0])
            fields_class += f'    StreamFieldAFP(name="{name}", offset={field["offset"]}, length={field["length"]}, type="{field["type"]}", ' \
                    f'optional={True if field["optional"] == "y" else False}, exception={exception}, range_values={range_value}, meaning={meaning}),\n'
            line_count = len(meaning)
            if len(range_value) > line_count:
                line_count = len(range_value)
            if line_count > 1:
                for line in range(1, line_count - 1):
                    rec_class += "        %-30.30s  #  %5.5s   %5.5s  %-4.4s  %-1.1s         %-5.5s      %-20.20s  %s\n" \
                            % ("", "", "", "", "", "", range_value[line], meaning[line])

        # Write class file.
        data = '''""" AFP %s Record """

from struct import pack, unpack

from stream_field_afp import StreamFieldAFP


afp_%s_fields_list = [
%s    ]
afp_%s_fields = {}
for field in afp_%s_fields_list:
    afp_%s_fields[field.name] = field


class AFP_%s:

    def __init__(self, segment):
        self.segment = segment
        self.document = self.segment.cur_document
        self.page = self.segment.cur_page
                                        # Offset: Length: Type: Optional: Exception: Range:                Meaning:
%s
    def parse(self, data):
        """ Parse the data from a record into the record class fields.

        :param bytes data: Record data
        """
        pass
        # %s = unpack(f">%s", data)

    def format(self):
        """ Format the data from the record class fields into a record.

        :returns: Record data
        """
        data = pack(f">%s", %s)
        return data
''' % (rec_type['type'], rec_type['type'].lower(), fields_class, rec_type['type'].lower(), rec_type['type'].lower(),
                         rec_type['type'].lower(), rec_type['type'], rec_class, unpack_parameter_list, format_string, format_string, pack_parameter_list)
        classfile.write(data)

        # Close output file.
        classfile.close()


def parse_ptoca_doc():
    """ Parse afp documentation formatted text file: ptoca """
    types = []
    fields = []
    offset_loc = None

    # Open files.
    input_file = open("C:\\Users\\print\\Documents\\stream\\ptoca.txt", "r")  # , encoding="utf-8")
    output_path = "C:\\Users\\print\\Documents\\stream\\printstreamer\\afp"
    rec_types = 0
    rec_type = ""
    class_def = False
    field_def = False

    # Process input file.
    lines = input_file.readlines()
    for line in lines:
        # Fix bad characters.
        line = line.replace("\xad", "-").replace("\xff", "").replace("\xfe", "").replace("\x00", "").replace("|", " ").rstrip()
        if len(line) == 0:
            continue

        # Skip the line.
        if ("Note:" in line[0:10]) or ("One repeating group in the following format:" in line) or (" repeating groups in the following format:" in line):
            pass
        else:
            # End field definition:
            if (len(line) == 0) or ((offset_loc is not None) and (len(line) >= offset_loc) and (line[offset_loc - 2:offset_loc - 1] != "    ")):
                if field_def:
                    fields.append(field)
                    field_def = False
                    #class_def = False

            # Get record type.
            m = re.search("([A-Z][A-Z][A-Z]) Control Sequence", line)
            if m:
                rec_type = m.group(1)
                if rec_type in ["BSU", "ESU", "SEC"]:
                    pause = True

            # Start record type.
            if "Syntax:" in line:
                if rec_types > 0:
                    # Save last rec type.
                    type['fields'] = fields
                    types.append(type)
                    fields = []
                rec_types += 1
                type = {}
                type['type'] = rec_type
                print(rec_type)
                if rec_type in ["AMB"]:
                    pause = True

            # End class_def.
            if "LID is a code with no units of measure" in line:
                class_def = False

            # Start field definition:
            if class_def:
                # Capture and parse offset field.
                if len(line) >= 10:
                    offset_string = line[offset_loc:type_loc].strip()
                    if offset_string != "":
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
                        field['default'] = ""
                        field['indicator'] = ""
                        # Parse offset.
                        p = re.compile('\s?\s?\s?\s?([0-9]+)\-?([0-9]+|n)?')
                        m = p.match(offset_string)
                        if m:
                            field_def = True
                            field['offset'] = int(m.group(1))
                            if (m.group(2) is None) or (m.group(2) == ""):
                                field['end'] = field['offset']
                                field['length'] = 1
                            elif m.group(2) == "n":
                                field['end'] = 32760
                                field['length'] = 32760 - field['offset'] + 1
                            else:
                                field['end'] = int(m.group(2))
                                field['length'] = field['end'] - field['offset'] + 1
                    if field_def:
                        # Capture other fields.
                        field['type'] += line[type_loc:name_loc].strip()
                        if "Zero or more keywords" in line:
                            field['name'] = "Keywords"
                            field['default'] = "None"
                        else:
                            field['name'] += line[name_loc:range_loc].strip()
                            if field['name'] == "":
                                field['name'] = "Constant"
                            field['range'] += line[range_loc:meaning_loc].strip() + "\t"
                            field['meaning'] += line[meaning_loc:optional_loc - 1].strip() + "\t"
                            field['optional'] = line[optional_loc:default_loc].strip()
                            if field['optional'] == "M":
                                field['optional'] = "n"
                            else:
                                field['optional'] = "y"
                            field['default'] += line[default_loc:indicator_loc].strip()
                            if field['default'] == "N":
                                field['default'] = "n"
                            else:
                                field['default'] = "y"
                            field['indicator'] += line[indicator_loc:].strip()
                            if field['indicator'] == "N":
                                field['indicator'] = "n"
                            else:
                                field['indicator'] = "y"

            # Start class section:
            #     Offset            Type       Name                Range              Meaning
            p = re.compile('\|?\s*?Offset\s+Type\s+Name\s+Range\s+Meaning\s+M\/O\s+Def\s+Ind')
            m = p.match(line)
            if m:
                class_def = True
                offset_loc = line.index("Offset")
                type_loc = line.index("Type")
                name_loc = line.index("Name")
                range_loc = line.index("Range")
                meaning_loc = line.index("Meaning")
                optional_loc = line.index("M/O") + 1
                default_loc = line.index("Def") + 1
                indicator_loc = line.index("Ind") + 1
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
        # output.write("%s\n" % (type['type']))
        # fields_sorted = sorted(type['fields'], key=lambda l: l['offset'])
        fields_sorted = type['fields']
        for field in fields_sorted:
            # output.write("    offset=%s end=%s length=%s\n" % (field['offset'], field['end'], field['length']))
            pass

    # Close files.
    input_file.close()

    print("\nTotal record types:  %d" % rec_types)

    # Create afp_recs class files.
    for rec_type in types_sorted:
        print(rec_type)
        # Open output file.
        classfile = open(os.path.join(output_path, f"afp_ptx_{rec_type['type'].lower()}_seq.py"), "w")
        fields_sorted = rec_type['fields']

        # Write detail.
        print(field)
        reserved_count = 0
        pack_parameter_list = ""
        unpack_parameter_list = ""
        format_string = ""
        rec_class = ""
        fields_class = ""
        for field in fields_sorted:
            print(field)
            if field['type'] == "":
                if ("triplet" in field['meaning']) or ("Triplet" in field['meaning']):
                    name = "Triplets"
                else:
                    reserved_count += 1
                    name = "Reserved_%i" % (reserved_count)
            else:
                name = field['name']
            name_formatted = f"self.{name} = None"
            if len(pack_parameter_list) > 0:
                pack_parameter_list += ", "
            pack_parameter_list += f"self.{name}"
            if len(unpack_parameter_list) > 0:
                unpack_parameter_list += ", "
            unpack_parameter_list += f"self.{name}"
            if ("triplets" in name.lower()) or (field["length"] > 32000):
                field_format = '{self.%s.len()}s' % name
            elif field["type"] in ["CHAR", "CODE", "BITS", "UNDF", "", None]:
                field_format = f'{field["length"]}s'
            elif field["type"] == "SBIN":
                if field["length"] == 1:
                    field_format = f'b'
                elif field["length"] == 2:
                    field_format = f'h'
                elif field["length"] == 3:
                    field_format = f'xh'
                else:
                    field_format = f''
                    msg = f'Unknown SBIN field length:  {field["length"]}\n{field}'
                    print(msg)
                    # raise Exception(msg)
            elif field["type"] == "UBIN":
                if field["length"] == 1:
                    field_format = f'B'
                elif field["length"] == 2:
                    field_format = f'H'
                elif field["length"] == 3:
                    field_format = f'xH'
                else:
                    field_format = f''
                    msg = f'Unknown UBIN field length:  {field["length"]}\n{field}'
                    print(msg)
                    # raise Exception(msg)
            else:
                field_format = f''
                msg = f'Unknown field format:  {field["type"]}\n{field}'
                print(msg)
                # raise Exception(msg)
            format_string += field_format
            range_value = field['range'].split("\t")
            meaning = field['meaning'].split("\t")
            rec_class += "        %-30.30s  #  %5i   %5i  %-4.4s  %-13.13s %-25.25s        %-1.1s    %-1.1s    %-1.1s\n" \
                    % (name_formatted, field["offset"], field["length"], field["type"], range_value[0], meaning[0], field["optional"], field["default"], field["indicator"])
            fields_class += f'    StreamFieldAFP(name="{name}", offset={field["offset"]}, length={field["length"]}, type="{field["type"]}", ' \
                    f'optional={True if field["optional"] == "y" else False}, range_values={range_value}, ' \
                    f'default={True if field["default"].lower() == "y" else False}, indicator={True if field["indicator"].lower() == "y" else False}, ' \
                    f'meaning={meaning}),\n'
            line_count = len(meaning)
            if len(range_value) > line_count:
                line_count = len(range_value)
            if line_count > 1:
                for line in range(1, line_count - 1):
                    rec_class += "        %-30.30s  #  %5.5s   %5.5s  %-4.4s  %-1.1s         %-5.5s      %-20.20s  %s\n" \
                            % ("", "", "", "", "", "", range_value[line], meaning[line])

        # Write class file.
        data = '''""" AFP PTX %s Sequence """

from struct import pack, unpack

from stream_field_afp import StreamFieldAFP


afp_ptx_%s_fields_list = [
%s    ]
afp_ptx_%s_fields = {}
for field in afp_ptx_%s_fields_list:
    afp_ptx_%s_fields[field.name] = field


class AFP_PTX_%s:

    def __init__(self):
                                        # Offset: Length: Type: Range:        Meaning:                  Optional: Def: Ind:
%s
    def parse(self, data):
        """ Parse the data from a record into the record class fields.

        :param bytes data: Record data
        """
        %s = unpack(f">%s", data)

    def format(self):
        """ Format the data from the record class fields into a record.

        :returns: Record data
        """
        data = pack(f">%s", %s)
        return data
''' % (rec_type['type'], rec_type['type'].lower(), fields_class, rec_type['type'].lower(), rec_type['type'].lower(),
                         rec_type['type'].lower(), rec_type['type'], rec_class, unpack_parameter_list, format_string, format_string, pack_parameter_list)
        classfile.write(data)

        # Close output file.
        classfile.close()

    # Create afp_ptx seq import list.
    for rec_type in types_sorted:
        print(f"from afp_ptx_{rec_type['type'].lower()}_seq import AFP_PTX_{rec_type['type'].upper()}")


def parse_foca_doc():
    """ Parse afp documentation formatted text file: foca """
    types = []
    fields = []

    # Open files.
    input_file = open("C:\\Users\\print\\Documents\\stream\\foca.txt", "r")
    output_path = "C:\\Users\\print\\Documents\\stream\\printstreamer\\afp"
    rec_types = 0
    rec_type = ""
    class_def = False
    field_def = False

    # Process input file.
    for line in input_file:
        # Fix bad character.
        line = line.replace("\xad", "-").rstrip()

        # Skip the line.
        if ("Note:" in line[0:10]) or ("One repeating group in the following format:" in line) or (" repeating groups in the following format:" in line):
            pass
        else:
            # End field definition:
            if (len(line) == 0) or (line[0:10] != "          ") or ("Note:" in line[0:10]) or ("When keywords occur" in line):
                if field_def:
                    fields.append(field)
                    field_def = False

            # End class section:
            if len(line) == 0:
                class_def = False

            # Start record type:
            # BAG (X'D3A8C9') Syntax
            p = re.compile('([A-Z][A-Z][A-Z]) - (D3[A-Z0-9][A-Z0-9][A-Z0-9][A-Z0-9]) - ')
            m = p.match(line)
            if m:
                if rec_types > 0:
                    # Save last rec type.
                    type['fields'] = fields
                    types.append(type)
                    fields = []
                rec_types += 1
                rec_type = m.group(1)
                type = {}
                type['type'] = rec_type
                print(rec_type)
                if rec_type in ["BRS", "ERS", "PPO"]:
                    pause = True

            # Start field definition:
            if class_def:
                # Capture and parse offset field.
                if len(line) >= 10:
                    offset_string = line[offset_loc:type_loc].strip()
                    if offset_string != "":
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
                            field['offset'] = int(m.group(1))
                            if (m.group(2) is None) or (m.group(2) == ""):
                                field['end'] = field['offset']
                                field['length'] = 1
                            elif m.group(2) == "n":
                                field['end'] = 32760
                                field['length'] = 32760 - field['offset'] + 1
                            else:
                                field['end'] = int(m.group(2))
                                field['length'] = field['end'] - field['offset'] + 1
                    if field_def:
                        # Capture other fields.
                        field['type'] += line[type_loc:name_loc].strip()
                        if "Zero or more keywords" in line:
                            field['name'] = "Keywords"
                            field['exception'] = "None"
                        else:
                            field['name'] += line[name_loc:range_loc].strip()
                            if field['name'] == "":
                                field['name'] = "Constant"
                            field['range'] += line[range_loc:meaning_loc].strip() + "\t"
                            field['meaning'] += line[meaning_loc:optional_loc].strip() + "\t"
                            field['optional'] = line[optional_loc:exception_loc].strip()
                            if field['optional'] == "M":
                                field['optional'] = "n"
                            else:
                                field['optional'] = "y"
                            field['exception'] += line[exception_loc:].strip()

            # Start class section:
            #     Offset            Type       Name                Range              Meaning
            p = re.compile('\|?\s*?Offset\s+Type\s+Name\s+Range\s+Meaning\s+M\/O')
            m = p.match(line)
            if m:
                class_def = True
                offset_loc = line.index("Offset")
                type_loc = line.index("Type")
                name_loc = line.index("Name")
                range_loc = line.index("Range")
                meaning_loc = line.index("Meaning")
                optional_loc = line.index("M/O")
                exception_loc = None
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
        # output.write("%s\n" % (type['type']))
        # fields_sorted = sorted(type['fields'], key=lambda l: l['offset'])
        fields_sorted = type['fields']
        for field in fields_sorted:
            # output.write("    offset=%s end=%s length=%s\n" % (field['offset'], field['end'], field['length']))
            pass

    # Close files.
    input_file.close()

    print("\nTotal record types:  %d" % rec_types)

    # Create afp_recs class files.
    for rec_type in types_sorted:
        # Open output file.
        classfile = open(os.path.join(output_path, f"afp_{rec_type['type'].lower()}_rec.py"), "w")
        fields_sorted = rec_type['fields']

        # Write detail.
        reserved_count = 0
        pack_parameter_list = ""
        unpack_parameter_list = ""
        format_string = ""
        rec_class = ""
        fields_class = ""
        for field in fields_sorted:
            if field['type'] == "":
                if ("triplet" in field['meaning']) or ("Triplet" in field['meaning']):
                    name = "Triplets"
                else:
                    reserved_count += 1
                    name = "Reserved_%i" % (reserved_count)
            else:
                name = field['name']
            name_formatted = f"self.{name} = None"
            if len(pack_parameter_list) > 0:
                pack_parameter_list += ", "
            pack_parameter_list += f"self.{name}"
            if len(unpack_parameter_list) > 0:
                unpack_parameter_list += ", "
            unpack_parameter_list += f"self.{name}"
            if ("triplets" in name.lower()) or (field["length"] > 32000):
                field_format = '{self.%s.len()}s' % name
            elif field["type"] in ["CHAR", "CODE", "BITS", "UNDF", "", None]:
                field_format = f'{field["length"]}s'
            elif field["type"] == "SBIN":
                if field["length"] == 1:
                    field_format = f'b'
                elif field["length"] == 2:
                    field_format = f'h'
                elif field["length"] == 3:
                    field_format = f'xh'
                else:
                    field_format = f''
                    msg = f'Unknown SBIN field length:  {field["length"]}\n{field}'
                    print(msg)
                    # raise Exception(msg)
            elif field["type"] == "UBIN":
                if field["length"] == 1:
                    field_format = f'B'
                elif field["length"] == 2:
                    field_format = f'H'
                elif field["length"] == 3:
                    field_format = f'xH'
                else:
                    field_format = f''
                    msg = f'Unknown UBIN field length:  {field["length"]}\n{field}'
                    print(msg)
                    # raise Exception(msg)
            else:
                field_format = f''
                msg = f'Unknown field format:  {field["type"]}\n{field}'
                print(msg)
                # raise Exception(msg)
            format_string += field_format
            range_value = field['range'].split("\t")
            meaning = field['meaning'].split("\t")
            exception = field["exception"].replace("X'", "'\\x")
            rec_class += "        %-30.30s  #  %5i   %5i  %-4.4s  %-1.1s         %-5.5s      %-20.20s  %s\n" \
                    % (name_formatted, field["offset"], field["length"], field["type"], field["optional"], field["exception"], range_value[0], meaning[0])
            fields_class += f'    StreamFieldAFP(name="{name}", offset={field["offset"]}, length={field["length"]}, type="{field["type"]}", ' \
                    f'optional={True if field["optional"] == "y" else False}, exception={exception}, range_values={range_value}, meaning={meaning}),\n'
            line_count = len(meaning)
            if len(range_value) > line_count:
                line_count = len(range_value)
            if line_count > 1:
                for line in range(1, line_count - 1):
                    rec_class += "        %-30.30s  #  %5.5s   %5.5s  %-4.4s  %-1.1s         %-5.5s      %-20.20s  %s\n" \
                            % ("", "", "", "", "", "", range_value[line], meaning[line])

        # Write class file.
        data = '''""" AFP %s Record """

from struct import pack, unpack

from stream_field_afp import StreamFieldAFP


afp_%s_fields_list = [
%s    ]
afp_%s_fields = {}
for field in afp_%s_fields_list:
    afp_%s_fields[field.name] = field


class AFP_%s:

    def __init__(self, segment):
        self.segment = segment
        self.document = self.segment.cur_document
        self.page = self.segment.cur_page
                                        # Offset: Length: Type: Optional: Exception: Range:                Meaning:
%s
    def parse(self, data):
        """ Parse the data from a record into the record class fields.

        :param bytes data: Record data
        """
        pass
        # %s = unpack(f">%s", data)

    def format(self):
        """ Format the data from the record class fields into a record.

        :returns: Record data
        """
        data = pack(f">%s", %s)
        return data
''' % (rec_type['type'], rec_type['type'].lower(), fields_class, rec_type['type'].lower(), rec_type['type'].lower(),
                         rec_type['type'].lower(), rec_type['type'], rec_class, unpack_parameter_list, format_string, format_string, pack_parameter_list)
        classfile.write(data)

        # Close output file.
        classfile.close()


# parse_modca_doc()
# parse_ptoca_doc()
parse_foca_doc()
# parse_goca_doc()
# parse_ioca_doc()
# parse_bcoca_doc()
