""" Parse one-to-many printstream files. """

from stream_file import StreamFile


class StreamParser:
    """ Manage the parsing of printstream files. """
    
    def __init__(self):
        self.input_files = []
        self.output_files = []

    def add_file(self, parser, name, file_type=None, type="input"):
        """ Add a file to the parser file list.

        :param StreamParser parser: Stream parser object
        :param str name: File name
        :param str file_type: File printstream type:  afp, pdf, etc.
        :param str type: input, output
        :return: StreamFile object
        """
        file = None
        # Instantiate file.
        file = StreamFile(self, name, file_type=file_type, type=type)
        if type == "input":
            # Append file to parser input list.
            self.input_files.append(file)
        elif type == "output":
            # Append file to parser output list.
            self.output_files.append(file)
        return file

    def parse(self, threads=1):
        """ Parse all files.

        :param threads:
        :return:
        """
        for file in self.input_files:
            file.parse()
        self.output_end()


    def output_document(self, document):
        """ Output document.

        :param document: Document to output
        """
        pass

    def output_page(self, page):
        """ Output page.

        :param page: Page to output
        """
        for file in self.output_files:
            if file.file_type == page.segment.file_type:
                # Output the same printstream type as the input.
                pass
            else:
                # Output a different printstream type than the input.
                file.cur_segment.output_page(page)

    def output_end(self):
        """ Finish up output files. """
        for file in self.output_files:
            if file.cur_segment.initialized:
                file.cur_segment.output_end()
