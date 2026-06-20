""" Map a print-stream file type to its writer.

To add output support for a new format, implement a writer with a
``write(document_set, path)`` method and register it here.
"""

from writer.afp_writer import AfpWriter
from writer.pdf_writer import PdfWriter
from writer.ps_writer import PsWriter
from writer.pcl_writer import PclWriter
from writer.metacode_writer import MetacodeWriter

_WRITERS = {
    "afp": AfpWriter,
    "pdf": PdfWriter,
    "ps": PsWriter,
    "postscript": PsWriter,
    "pcl": PclWriter,
    "metacode": MetacodeWriter,
}


def get_writer(file_type, options=None):
    """ Return a writer instance for ``file_type`` (e.g. "afp", "pdf").

    ``options`` is an optional dict of writer settings (e.g. internal compression for
    PDF); writers that do not use it simply ignore it. """
    try:
        writer = _WRITERS[file_type]()
    except KeyError:
        raise ValueError(f"No writer registered for file type {file_type!r}")
    writer.options = options or {}
    return writer


def register_writer(file_type, writer_cls):
    _WRITERS[file_type] = writer_cls
