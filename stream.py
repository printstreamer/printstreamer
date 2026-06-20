""" stream: Printstream/Document Processing: Compose, Analyze, Enhance, Transform. """

import argparse
import logging
import os
import sys
from xml.dom import minidom

from paths import PROJECT_ROOT
from process.runner import run_step

logger = logging.getLogger("stream")


def _resolve_process_path(process_path):
    """ Locate the process file: as given (relative to the current directory), else
    relative to the project root. This lets ``stream.py <name>.xml`` work regardless of
    the working directory it is launched from (e.g. an IDE run configuration). """
    if os.path.isfile(process_path):
        return process_path
    candidate = os.path.join(PROJECT_ROOT, process_path)
    if os.path.isfile(candidate):
        return candidate
    return process_path                       # let the caller raise a clear OSError


def run_process(process_path, start=None, stop=None):
    """ Execute the steps of a process XML file between ``start`` and ``stop``. """
    document = minidom.parse(_resolve_process_path(process_path))
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
    try:
        run_process(args.process, start=args.start, stop=args.stop)
    except PermissionError as exc:
        name = exc.filename or "the output file"
        print(f"\nError: cannot write '{name}' - permission denied.\n"
              f"  It is most likely open in another application (e.g. a PDF viewer) or "
              f"read-only.\n  Close any app holding it open, or choose a different output "
              f"name, and re-run.", file=sys.stderr)
        return 1
    except OSError as exc:
        name = getattr(exc, "filename", None) or "a file"
        print(f"\nError: I/O failure on '{name}': {exc.strerror or exc}.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
