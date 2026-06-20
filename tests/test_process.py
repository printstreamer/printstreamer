""" Tests for parse options, indexing, compression, and process steps. """

import gzip
import json

import compression
from parse_options import ParseLevel, ParseOptions
from process import index as index_mod
from process.index import FieldSpec, IndexRecord
from process.stats import StatsSink
from stream_parser import StreamParser
from model.geometry import Rect
from tests.conftest import AFP_SAMPLE


def _parse(options):
    parser = StreamParser(options=options)
    parser.add_file(parser, AFP_SAMPLE, file_type="afp", type="input")
    parser.input_files[-1].parse()
    return parser.document_set


def test_page_range_scopes_model():
    ds = _parse(ParseOptions(start_page=1, end_page=2))
    assert ds.page_count == 2


def test_structure_level_skips_elements():
    ds = _parse(ParseOptions(level=ParseLevel.STRUCTURE))
    assert ds.page_count == 3
    assert all(len(p.elements) == 0 for _, p in ds.iter_pages())


def test_stats_sink_bounded():
    stats = StatsSink()
    _parse(ParseOptions(page_sink=stats, retain_pages=False))
    assert stats.pages == 3
    assert stats.element_kinds["text"] > 100


def test_index_extract_windowed():
    from process.index import IndexSink
    sink = IndexSink(AFP_SAMPLE, specs=[FieldSpec("heading", window=Rect(0, 0, 612, 72))])
    _parse(ParseOptions(page_sink=sink, retain_pages=False))
    assert len(sink.records) == 3
    assert "Lesson" in sink.records[0].fields["heading"]
    assert sink.records[0].byte_offset is not None


def test_document_identification_by_element():
    from process.index import IndexSink, document_index_from_pages
    # Each page has a heading in the top window -> identify one document per page.
    sink = IndexSink(AFP_SAMPLE, boundary=FieldSpec("b", window=Rect(0, 0, 612, 72)))
    _parse(ParseOptions(page_sink=sink, retain_pages=False))
    assert [r.document_number for r in sink.records] == [1, 2, 3]
    docs = document_index_from_pages(sink.records)
    assert len(docs) == 3 and all(d.page_count == 1 for d in docs)


def test_document_identification_by_page_count():
    from process.index import IndexSink, document_index_from_pages
    sink = IndexSink(AFP_SAMPLE, pages_per_document=2)
    _parse(ParseOptions(page_sink=sink, retain_pages=False))
    docs = document_index_from_pages(sink.records)
    assert [d.page_count for d in docs] == [2, 1]      # 3 pages, 2 per doc


def test_index_serialize_formats():
    recs = [IndexRecord(source="x", document_number=1, page_number=1,
                        byte_offset=10, fields={"a": "1"})]
    for fmt in ("json", "xml", "csv", "tab", "text"):
        data = index_mod.serialize(recs, fmt)
        assert data and isinstance(data, bytes)
    # json round-trips
    loaded = index_mod.load(index_mod.serialize(recs, "json"), "json")
    assert loaded[0].page_number == 1


def test_compression_levels(tmp_path):
    raw = b"hello world " * 100
    assert compression.compress(raw, "gzip", 0) == raw          # level 0 = no-op
    packed = compression.compress(raw, "gzip", 9)
    assert gzip.decompress(packed) == raw
    out = compression.write_file(str(tmp_path / "f.json"), raw, codec="gzip", level=6)
    assert out.endswith(".gz")
    # read_file transparently decompresses what write_file produced.
    assert compression.read_file(out) == raw
    plain = compression.write_file(str(tmp_path / "p.json"), raw, codec="none", level=0)
    assert compression.read_file(plain) == raw
