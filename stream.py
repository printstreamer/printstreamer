""" stream: Printstream/Document Processing: Compose, Analyze, Enhance, Transform. """

import argparse
import logging
import sys
from xml.dom import minidom

from process.runner import run_step

logger = logging.getLogger("stream")


def run_process(process_path, start=None, stop=None):
    """ Execute the steps of a process XML file between ``start`` and ``stop``. """
    document = minidom.parse(process_path)
    process_steps = document.documentElement.getElementsByTagName("step")
    started = start is None
    stopped = False
    stopping = False
    for process_step in process_steps:
        step_name = process_step.getAttribute("name")
        if stopping:
            stopped = True
        if (not started) and step_name == start:
            started = True
        if (not stopped) and step_name == stop:
            stopping = True
        if started and not stopped:
            print(f"Processing step:  {step_name}")
            run_step(process_step)


def main(argv=None):
    arg_parser = argparse.ArgumentParser(description="Printstream Utilities.")
    arg_parser.add_argument("process", type=str, help="Process file name (xml)")
    arg_parser.add_argument("--start", type=str, default=None,
                            help="First step of the process to execute. Defaults to first.")
    arg_parser.add_argument("--stop", type=str, default=None,
                            help="Last step of the process to execute. Defaults to last.")
    arg_parser.add_argument("--log", type=str, default="WARNING",
                            help="Logging level (DEBUG, INFO, WARNING, ERROR).")
    arg_parser.add_argument("--threads", type=int, default=1,
                            help="Default parse worker threads (steps may override).")
    args = arg_parser.parse_args(argv)
    logging.basicConfig(level=getattr(logging, args.log.upper(), logging.WARNING),
                        format="%(levelname)s %(name)s: %(message)s")
    from process import runner
    runner.DEFAULT_THREADS = args.threads
    run_process(args.process, start=args.start, stop=args.stop)
    return 0


if __name__ == "__main__":
    sys.exit(main())
