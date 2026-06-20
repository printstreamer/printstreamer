""" Tests for multi-threaded AFP parsing: results must match a serial parse. """

from parse_options import ParseOptions
from process.parallel import max_threads, scan_afp_boundaries
from stream_parser import StreamParser
from tests.conftest import AFP_SAMPLE


def _texts(threads):
    p = StreamParser(options=ParseOptions(threads=threads))
    p.add_file(p, AFP_SAMPLE, file_type="afp", type="input")
    p.parse()
    ds = p.document_set
    return (ds.document_count, ds.page_count,
            [e.text for _, pg in ds.iter_pages() for e in pg.elements
             if getattr(e, "text", "")])


def test_scan_finds_pages_and_docs():
    pages, docs, total = scan_afp_boundaries(AFP_SAMPLE)
    assert len(pages) == 3
    assert len(docs) == 1
    assert total > 0


def test_threaded_matches_serial():
    serial = _texts(1)
    for threads in (2, 3, 4):
        assert _texts(threads) == serial


def test_max_threads_clamped():
    import os
    cpu = os.cpu_count() or 1
    assert max_threads(0) == cpu
    assert max_threads(1) == 1
    assert max_threads(10_000) == cpu
