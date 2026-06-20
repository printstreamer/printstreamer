""" Tests for AFP object parsing: images, fonts, precise text widths, doc index. """

import fontmetrics
from parse_options import ParseLevel, ParseOptions
from process import index as index_mod
from process.index import IndexSink
from stream_parser import StreamParser
from model.element import ElementKind
from tests.conftest import AFP_SAMPLE


def _parse(level=ParseLevel.FULL):
    parser = StreamParser(options=ParseOptions(level=level))
    parser.add_file(parser, AFP_SAMPLE, file_type="afp", type="input")
    parser.input_files[-1].parse()
    return parser.document_set


def test_images_have_windows():
    ds = _parse()
    images = [e for _, pg in ds.iter_pages() for e in pg.elements
              if e.kind == ElementKind.IMAGE]
    assert len(images) == 3
    for img in images:
        assert img.bbox is not None
        assert img.bbox.width > 500 and img.bbox.height > 700   # full-page scan
        assert img.encoding and img.encoding.startswith("ioca")


def test_fonts_mapped_from_mcf():
    ds = _parse()
    fonts = [r for r in ds.documents[0].resource_library if r.kind.value == "font"]
    assert len(fonts) >= 1
    names = {f.name for f in fonts}
    assert "F01" in names
    f01 = next(f for f in fonts if f.name == "F01")
    assert f01.char_set and f01.char_set.startswith("C0")     # no stray leading byte


def test_precise_text_width_uses_metrics():
    # Real glyph metrics: 'WWWW' is wider than 'iiii' at the same size.
    wide = fontmetrics.text_width("WWWW", 10)
    narrow = fontmetrics.text_width("iiii", 10)
    assert wide > narrow
    # Every text element gets a positive, content-dependent width.
    ds = _parse()
    texts = [e for _, pg in ds.iter_pages() for e in pg.elements
             if e.kind == ElementKind.TEXT]
    assert all(t.bbox.width > 0 for t in texts)


def test_document_index_page_count():
    sink = IndexSink(AFP_SAMPLE)
    StreamParser  # noqa: keep import used
    p = StreamParser(options=ParseOptions(page_sink=sink, retain_pages=False))
    p.add_file(p, AFP_SAMPLE, file_type="afp", type="input")
    p.input_files[-1].parse()
    docs = index_mod.document_index_from_pages(sink.records)
    assert len(docs) == 1
    assert docs[0].page_count == 3
    assert docs[0].byte_offset is not None
