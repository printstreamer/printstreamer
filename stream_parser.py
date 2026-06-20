""" Parse one-to-many printstream files into the generic model, then write outputs. """

import logging

from stream_file import StreamFile
from model.document import StreamDocumentSet
from parse_options import DEFAULT_OPTIONS
from writer.registry import get_writer

logger = logging.getLogger(__name__)


class StreamParser:
    """ Manage parsing of input printstream files into a shared model and writing of
    output printstream files from that model. """

    def __init__(self, options=None):
        self.input_files = []
        self.output_files = []
        # Parse scope/level and optional streaming sink (bounded memory).
        self.options = options or DEFAULT_OPTIONS
        # Writer settings (e.g. PDF internal compression), passed to each writer.
        self.output_options = {}
        # The parsed model. All input files append their documents here, which makes
        # cross-file merging natural and lets every writer consume one model.
        self.document_set = StreamDocumentSet()

    def add_file(self, parser, name, file_type=None, type="input"):
        """ Add an input or output file to the parser.

        :param StreamParser parser: Stream parser object (kept for call-site compatibility)
        :param str name: File name
        :param str file_type: Printstream type: afp, pdf, ...
        :param str type: "input" or "output"
        :return: StreamFile object
        """
        file = StreamFile(self, name, file_type=file_type, type=type)
        if type == "input":
            self.input_files.append(file)
        elif type == "output":
            self.output_files.append(file)
        return file

    def parse(self, threads=None):
        """ Parse all input files into the model, then write all output files.

        When ``threads`` (or the options' thread count) exceeds 1 and an AFP input is
        parsed at full scope, parsing is split across worker threads. """
        n_threads = threads if threads is not None else self.options.threads
        for file in self.input_files:
            if (file.file_type == "afp" and n_threads and n_threads > 1
                    and self.options.is_full_scope()):
                from process.parallel import parse_afp_threaded
                used = parse_afp_threaded(file.name, self, n_threads)
                self._rollup_file(file)
                logger.info("Parsed %s with %d thread(s)", file.name, used)
            else:
                file.parse()
        self.write_outputs()

    def _rollup_file(self, file):
        file.documents = self.document_set.document_count
        file.pages = self.document_set.page_count

    def write_outputs(self):
        """ Render the parsed model to every configured output file. """
        for file in self.output_files:
            writer = get_writer(file.file_type, self.output_options)
            logger.info("Writing %s output: %s", file.file_type, file.name)
            writer.write(self.document_set, file.name)
