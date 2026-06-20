""" Fidelity tests for the exhaustive AFP engine: triplet coverage, the flat
fixed-length index, the streaming non-transform merge, font code-page decode, and
100% information-faithful representation. """

import struct

import pytest

import stream_afp
from afp import structured_field as sf
from afp import triplets as tr
from afp import codepages
from model.element import ElementKind
from model.resource import ResourceKind
from parse_options import ParseLevel, ParseOptions
from process import index as ix
from process import runner
from stream_parser import StreamParser
from writer.afp_writer import AfpWriter
from tests.conftest import AFP_SAMPLE


def _parse(path, level=ParseLevel.ELEMENTS):
    p = StreamParser(options=ParseOptions(level=level))
    p.add_file(p, path, file_type="afp", type="input")
    for f in p.input_files:
        f.parse()
    return p.document_set


def _iter_sf(data):
    i, n = 0, len(data)
    while i + 6 <= n and data[i:i + 1] == b"\x5a":
        rl = struct.unpack(">H", data[i + 1:i + 3])[0] + 1
        rid = data[i + 3:i + 6]
        rec = stream_afp.afp_rec_type.get(rid)
        yield (rec["type"] if rec else None), data[i + 9:i + rl]
        i += rl


def _texts(ds):
    return [e.text for _, pg in ds.iter_pages()
            for e in pg.elements if e.kind == ElementKind.TEXT]


# --- triplet coverage ------------------------------------------------------

def test_no_unknown_triplets_in_sample():
    data = open(AFP_SAMPLE, "rb").read()
    unknown = []
    for rtype, body in _iter_sf(data):
        if rtype is None:
            continue
        view = sf.decode(rtype, body)
        for t in view.triplets:
            if t.unknown:
                unknown.append((rtype, t.tid))
        for g in view.groups:
            for t in g.get("triplets", []):
                if t.unknown:
                    unknown.append((rtype, t.tid))
    assert unknown == [], f"undecoded triplets: {unknown}"


def test_triplet_engine_decodes_known_fields():
    # Object Area Size (0x4C) round-trips through decode/build.
    content = bytes([0x00]) + (1000).to_bytes(3, "big") + (2000).to_bytes(3, "big")
    raw = bytes([len(content) + 2, 0x4C]) + content
    trips = tr.parse_triplets(raw)
    assert trips[0].name == "object_area_size"
    assert trips[0].fields["x_size"] == 1000 and trips[0].fields["y_size"] == 2000
    assert tr.build(trips) == raw


# --- flat fixed-length index ----------------------------------------------

def _build_indexes():
    sink = ix.IndexSink(AFP_SAMPLE)
    p = StreamParser(options=ParseOptions(page_sink=sink, retain_pages=False))
    p.add_file(p, AFP_SAMPLE, file_type="afp", type="input")
    p.input_files[-1].parse()
    recs = sink.records
    fields = ix._field_names(recs)
    page_bytes = ix.serialize(recs, "flat", kind="page")
    doc_recs = ix.document_index_from_pages(recs)
    doc_bytes = ix.serialize(doc_recs, "flat", kind="doc", page_field_names=fields)
    return recs, page_bytes, doc_bytes


def test_flat_index_fixed_width_and_join():
    recs, page_bytes, doc_bytes = _build_indexes()
    plines = [l for l in page_bytes.decode().splitlines() if not l.startswith("#")]
    assert len(set(len(l) for l in plines)) == 1            # constant width
    page = ix.load(page_bytes, "flat", kind="page")
    docs = ix.load(doc_bytes, "flat", kind="doc")
    doc_offsets = {d.document_offset for d in docs}
    assert all(p.document_offset in doc_offsets for p in page)   # join key valid
    assert page[0].document_offset == 0                          # zero-based


def test_doc_index_locates_page_records():
    recs, page_bytes, doc_bytes = _build_indexes()
    docs = ix.load(doc_bytes, "flat", kind="doc")
    d0 = docs[0]
    # pi_* fields slice the page index file to this document's page records.
    seg = page_bytes[d0.pi_byte_offset:d0.pi_byte_offset + d0.pi_byte_count]
    seg_lines = [l for l in seg.decode().splitlines() if l.strip()]
    assert len(seg_lines) == d0.pi_record_count == d0.page_count
    # input-printstream span: byte_count is the sum of the document's page spans.
    page = ix.load(page_bytes, "flat", kind="page")
    assert d0.byte_count == sum(p.byte_count for p in page if p.document_offset == 0)


def test_extract_spans_independent_of_parse_level():
    def spans(level):
        sink = ix.IndexSink(AFP_SAMPLE)
        p = StreamParser(options=ParseOptions(page_sink=sink, retain_pages=False, level=level))
        p.add_file(p, AFP_SAMPLE, file_type="afp", type="input")
        p.input_files[-1].parse()
        return [(r.byte_offset, r.byte_count, r.record_offset, r.record_count)
                for r in sink.records]
    assert spans(ParseLevel.STRUCTURE) == spans(ParseLevel.ELEMENTS)


# --- streaming merge -------------------------------------------------------

def test_streaming_merge_reproduces_pages(tmp_path):
    recs, page_bytes, _ = _build_indexes()
    loaded = ix.load(page_bytes, "flat", kind="page")
    out = tmp_path / "stream.afp"
    runner._merge_streaming(loaded, str(out), [])
    # Each original page byte span appears verbatim in the streamed output.
    src = open(AFP_SAMPLE, "rb").read()
    blob = out.read_bytes()
    for r in loaded:
        assert src[r.byte_offset:r.byte_offset + r.byte_count] in blob
    # And the streamed output re-parses to the same pages and text.
    ds_in = _parse(AFP_SAMPLE)
    ds_out = _parse(str(out))
    assert ds_out.page_count == ds_in.page_count
    assert _texts(ds_out) == _texts(ds_in)


def test_streaming_merge_delete_on_the_fly(tmp_path):
    recs, page_bytes, _ = _build_indexes()
    loaded = ix.load(page_bytes, "flat", kind="page")
    # Delete every PTX (presentation text) record by its structured-field id.
    ptx_hex = stream_afp.afp_rec_type_text["PTX"]["value"].hex()
    out = tmp_path / "deleted.afp"
    runner._merge_streaming(loaded, str(out), [ptx_hex])
    ds_out = _parse(str(out))
    assert _texts(ds_out) == []          # all text removed on the fly


# --- font / representation fidelity ----------------------------------------

def test_codepage_resolution():
    assert codepages.codec_name("T1001252") == "cp1252"
    assert codepages.codec_name("T1V10500") == "cp500"
    assert len(codepages.unicode_map("T1001252")) > 200


def test_fonts_have_encoding_map():
    ds = _parse(AFP_SAMPLE)
    fonts = [r for d in ds.documents for r in d.resource_library
             if r.kind == ResourceKind.FONT]
    assert fonts
    assert all(f.code_page for f in fonts)
    assert any(len(f.encoding_map) > 200 for f in fonts)


def test_doc_index_records_are_2000_bytes_lf(tmp_path):
    recs, _, doc_bytes = _build_indexes()
    docs = ix.document_index_from_pages(recs)
    n = len(docs)
    assert len(doc_bytes) == n * 2000           # each record exactly 2000 bytes
    assert all(doc_bytes[i * 2000 - 1] == 0x0A for i in range(1, n + 1))  # LF at 2000th
    assert b"\r" not in doc_bytes               # no CR
    loaded = ix.load(doc_bytes, "flat", kind="doc")
    assert len(loaded) == n and loaded[0].page_count == docs[0].page_count


def test_font_metrics_and_per_char_width():
    ds = _parse(AFP_SAMPLE)
    font = next(r for d in ds.documents for r in d.resource_library
               if r.kind == ResourceKind.FONT)
    assert font.metrics and font.size                       # name/size/widths captured
    # per-character advances sum to the run's bbox width
    run = next(e for _, pg in ds.iter_pages() for e in pg.elements
               if e.kind == ElementKind.TEXT and len(e.text) > 5)
    adv = run.attributes.get("char_advances")
    assert adv and abs(sum(adv) - run.bbox.width) < 0.5


def test_precise_window_capture():
    ds = _parse(AFP_SAMPLE)
    from model.geometry import Rect
    from model import visitor
    run = next(e for _, pg in ds.iter_pages() for e in pg.elements
               if e.kind == ElementKind.TEXT and len(e.text) > 8)
    adv = run.attributes["char_advances"]
    x0 = run.position.x
    win = Rect(x0 - 1, run.position.y - 12, sum(adv[:4]) + 0.5, 14)
    clip = visitor.text_in_window(run, win)
    assert clip == run.text[:4]                 # only the in-window characters


def test_ps_writer_resolves_real_font(tmp_path):
    ds = _parse(AFP_SAMPLE)
    from writer.ps_writer import PsWriter
    out = tmp_path / "t.ps"
    PsWriter().write(ds, str(out))
    ps = out.read_text(encoding="latin-1")
    assert "findfont" in ps and "/F01" not in ps    # real base font, not the local id


def test_pcl_bold_from_charset(tmp_path):
    from model.document import Document, StreamDocumentSet
    from model.page import Page
    from model.element import TextElement
    from model.resource import FontResource
    from model.geometry import Point
    from writer.pcl_writer import PclWriter
    ds = StreamDocumentSet()
    doc = ds.add_document(Document(name="d"))
    doc.resource_library.add(FontResource(name="F01", char_set="C0N400B0"))  # 'B0' = bold
    page = doc.add_page(Page(number=1))
    page.add_element(TextElement(text="Hi", position=Point(72, 72),
                                 font_ref="F01", font_size=10))
    out = tmp_path / "t.pcl"
    PclWriter().write(ds, str(out))
    assert b"(s3B" in out.read_bytes()          # bold weight selected from char-set


def test_fontlib_json_lookup(tmp_path):
    import json
    from model.resource import FontResource
    from afp import fontlib
    (tmp_path / "C0N400F0.json").write_text(json.dumps(
        {"size": 12.0, "widths": {"65": 700}, "encoding": {"65": "A"}}))
    font = FontResource(name="F01", char_set="C0N400F0")
    assert fontlib.apply(font, str(tmp_path))
    assert font.size == 12.0 and font.metrics[ord("A")] == 700.0


def test_embedded_foca_builder():
    from afp import fonts
    from model.resource import FontResource
    b = fonts.FontBuilder(name="C0TEST")
    b.unit_base = 1000
    b.set_descriptor(size=11.0)
    b.map_code(0x41, 0x41, "A")
    b.add_char_width(0x41, 600)
    b.finish()
    font = FontResource(name="F09", char_set="C0TEST")
    b.apply(font)
    assert font.size == 11.0 and font.metrics[ord("A")] == 600.0


def test_text_color_and_orientation_captured():
    # STC/SEC -> color, STO -> orientation, exercised through the PTOCA handler.
    from afp.ptoca.afp_ptx_rec import _stc_color, _sec_color
    assert _stc_color(b"\x00\x02").to_rgb() == (1.0, 0.0, 0.0)        # red
    sec = _sec_color(bytes([0x00, 0x01, 0, 0, 0, 0, 0, 0, 0, 255, 0]))  # RGB green
    assert sec.to_rgb() == (0.0, 1.0, 0.0)


def test_representation_is_faithful_and_roundtrips(tmp_path):
    ds1 = _parse(AFP_SAMPLE)
    # text, fonts and images are all represented
    assert len(_texts(ds1)) > 100
    fonts1 = {(r.name, r.code_page, r.char_set) for d in ds1.documents
              for r in d.resource_library if r.kind == ResourceKind.FONT}
    assert fonts1
    images = [e for _, pg in ds1.iter_pages() for e in pg.elements
              if e.kind == ElementKind.IMAGE]
    assert images
    # AFP writer preserves fonts (MCF) and text across a round trip
    out = tmp_path / "rt.afp"
    AfpWriter().write(ds1, str(out))
    ds2 = _parse(str(out))
    fonts2 = {(r.name, r.code_page, r.char_set) for d in ds2.documents
              for r in d.resource_library if r.kind == ResourceKind.FONT}
    assert fonts1 == fonts2
    assert _texts(ds2) == _texts(ds1)
