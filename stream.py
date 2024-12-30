""" stream:  Printstream Parser """

import sys
import argparse

from stream_parser import StreamParser


# Process command-line arguments.
parser = argparse.ArgumentParser(description='Parse printstreams.')
parser.add_argument('input_files', metavar='input_filenames', type=str,
                    nargs='+', help='input printstream filename(s)')
parser.add_argument('-t', '--type', dest='type', default='afp',
                    help='printstream type/language')
args = parser.parse_args()

# Set up for processing.
stream_parser = StreamParser()
# Add the input file(s) to the parser as segments.
for input_name in args.input_files:
    # Process an input file.
    print(f" processing input file:  {input_name}")
    stream_parser.add_segment(input_name=input_name, start_offset="0", end_offset="-0", output_name=None)
# Parse printstream segments.
stream_parser.parse_segments()
#  End script.
sys.exit(0)
