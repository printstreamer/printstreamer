""" stream:  Printstream/Document Processing: Compose, Analyze, Enhance, Transform """

import argparse
import sys
from xml.dom import minidom

from stream_parser import StreamParser


def analyze(step):
    """ Analyze process.

    :param step: Process step
    """
    # Set up for processing.
    stream_parser = StreamParser()
    # Add the input file(s) to the parser as files.
    for file in step.getElementsByTagName("file"):
        if file.getAttribute("type") == "input":
            name = file.getAttribute('name')
            if file.hasAttribute('file_type'):
                file_type = file.getAttribute('file_type')
            else:
                file_type = None
            print(f"processing input file:  {name}")
            stream_parser.add_file(stream_parser, name, file_type=file_type)
    # Parse printstream files.
    stream_parser.parse()


if __name__ == "__main__":

    # Process command-line arguments.
    arg_parser = argparse.ArgumentParser(description="Printstream Utilities.")
    arg_parser.add_argument("process", type=str, default=None, help="Process file name (xml)")
    arg_parser.add_argument("--start", type=str, default=None, help="First step of the process file to execute. Defaults to first step.")
    arg_parser.add_argument("--stop", type=str, default=None, help="Last step of the process file to execute. Defaults to last step")
    args = arg_parser.parse_args()

    # Execute the process steps.
    document = minidom.parse(args.process)
    process = document.documentElement
    process_steps = process.getElementsByTagName("step")
    if args.start is None:
        started = True
    else:
        started = False
    stopping = False
    stopped = False
    for process_step in process_steps:
        step_name = process_step.getAttribute("name")
        if stopping:
            stopped = True
        if (not started) and (step_name == args.start):
            started = True
        if (not stopped) and (step_name == args.stop):
            stopping = True
        if started and not stopped:
            print(f"Processing step:  {step_name}")
            if step_name == "analyze":
                analyze(process_step)

    #  End script.
    sys.exit(0)
