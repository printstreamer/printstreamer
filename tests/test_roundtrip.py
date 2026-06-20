""" End-to-end parse/transform/round-trip tests on the sample files. """

import os

import fitz
import pytest

from stream_parser import StreamParser
from writer.afp_writer import AfpWriter
from model.element import ElementKind
from tests.conftest import AFP_SAMPLE, PDF_SAMPLE


def _parse(path, file_type):
    parser = StreamParser()
    parser.add_file(parser, path, file_type=file_type, type="input")
    for f in parser.input_files:
        f.parse()
    return parser.document_set


def _texts(document_set):
    return [e.text for _, pg in document_set.iter_pages()
            for e in pg.elements if e.kind == ElementKind.TEXT]


def test_afp_parses_into_model():
    ds = _parse(AFP_SAMPLE, "afp")
    assert ds.document_count >= 1
    assert ds.page_count == 3
    assert len(_texts(ds)) > 100


def test_afp_roundtrip_preserves_text(tmp_path):
    ds1 = _parse(AFP_SAMPLE, "afp")
    out = tmp_path / "roundtrip.afp"
    AfpWriter().write(ds1, str(out))
    ds2 = _parse(str(out), "afp")
    assert ds2.page_count == ds1.page_count
    assert _texts(ds2) == _texts(ds1)


def test_afp_to_pdf_transform(tmp_path):
    ds = _parse(AFP_SAMPLE, "afp")
    from writer.pdf_writer import PdfWriter
    out = tmp_path / "out.pdf"
    PdfWriter().write(ds, str(out))
    doc = fitz.open(str(out))
    try:
        assert len(doc) == 3
        assert any(pg.get_text().strip() for pg in doc)
    finally:
        doc.close()


def test_pdf_parses_into_model():
    ds = _parse(PDF_SAMPLE, "pdf")
    assert ds.page_count > 1
    assert len(_texts(ds)) > 100
