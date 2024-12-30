""" stream:  Printstream/Document Utilities: Compose, Analyze, Enhance, Transform """

import sys
import argparse

from stream_parser import StreamParser


# Process command-line arguments.
parser = argparse.ArgumentParser(description="Printstream Utilities.")
parser.add_argument("input_files", metavar="input_filenames", type=str,
                    nargs="+", help="input printstream filename(s)")
parser.add_argument("-t", "--type", dest="type", default=None,
                    help="printstream type/language")
args = parser.parse_args()

# Set up for processing.
stream_parser = StreamParser()

# Add the input file(s) to the parser as segments.
for input_name in args.input_files:

    # Process an input file.
    print(f" processing input file:  {input_name}")
    stream_parser.add_file(stream_parser, input_name, file_type=args.type)

# Parse printstream segments.
stream_parser.parse()

#  End script.
sys.exit(0)
