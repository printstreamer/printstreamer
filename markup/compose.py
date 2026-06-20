""" Compose: generate a print stream (and its indexes) from a PSML markup file. """

from __future__ import annotations

import logging

import compression
from markup import loader
from markup.layout import LayoutEngine
from process import index as index_mod
from writer.registry import get_writer

logger = logging.getLogger(__name__)


def compose(markup_path, outputs, index_path=None, index_format="json",
            compress="none", compress_level=0, output_options=None):
    """ Load PSML, lay it out, write the output print stream(s), and emit indexes.

    :param markup_path: path to the PSML file
    :param outputs: list of (path, file_type) output targets
    :param index_path: if set, write page and document index files
    :param output_options: optional writer settings (e.g. PDF internal compression)
    :returns: the composed StreamDocumentSet
    """
    markup = loader.load(markup_path)
    doc_set = LayoutEngine(markup).run()

    for name, ftype in outputs:
        get_writer(ftype, output_options).write(doc_set, name)
        logger.info("Composed %s -> %s", ftype, name)

    if index_path:
        _write_indexes(doc_set, markup_path, index_path, index_format,
                       compress, compress_level)
    return doc_set


def _write_indexes(doc_set, source, index_path, fmt, codec, level):
    page_records = index_mod.page_index_from_model(doc_set, source)
    doc_records = index_mod.document_index_from_pages(page_records)
    compression.write_file(index_path, index_mod.serialize(page_records, fmt),
                           codec=codec, level=level)
    base, dot, ext = index_path.rpartition(".")
    doc_index_path = f"{base}.docs.{ext}" if dot else f"{index_path}.docs"
    compression.write_file(doc_index_path, index_mod.serialize(doc_records, fmt),
                           codec=codec, level=level)
    logger.info("Wrote indexes: %s (%d pages), %s (%d docs)",
                index_path, len(page_records), doc_index_path, len(doc_records))
