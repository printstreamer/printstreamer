""" Parse one-to-many printstream files. """

from stream_file import StreamFile


class StreamParser:
    """ Manage the parsing of printstream files. """
    
    def __init__(self):
        self.files = []

    def add_file(self, parser, name, file_type=None):
        """ Add a file to the parser file list.

        :param StreamParser parser: Stream parser object
        :param str name: File name
        :param str file_type: File type
        :return: StreamFile object
        """
        # Instantiate file.
        file = StreamFile(self, name, file_type=file_type)
        # Append file to parser list.
        self.files.append(file)
        return file

    def parse(self, threads=1):
        """ Parse all files.

        :param threads:
        :return:
        """
        for file in self.files:
            file.parse()
