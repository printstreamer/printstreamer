""" Tests for label generation and AFP object/AFP-specific round-trips. """

from labels.generate import generate_labels
from markup import loader
from markup.layout import LayoutEngine
from parse_options import ParseLevel, ParseOptions
from process.index import IndexRecord
from stream_parser import StreamParser
from writer.afp_writer import AfpWriter
from model.element import ElementKind
from tests.conftest import AFP_SAMPLE


def _parse_afp(path):
    p = StreamParser(options=ParseOptions(level=ParseLevel.FULL))
    p.add_file(p, path, file_type="afp", type="input")
    p.input_files[-1].parse()
    return p.document_set


def _kinds(ds):
    from collections import Counter
    return Counter(e.kind.value for _, pg in ds.iter_pages() for e in pg.elements)


def test_labels_grid_and_fields():
    recs = [IndexRecord(fields={"name": f"C{i}", "code": f"SKU{i:04d}"}) for i in range(1, 8)]
    template = ('<paragraph size="9">{name}</paragraph>'
                '<barcode x="4" y="40" width="100" height="18" symbology="code128" data="{code}"/>')
    ds = generate_labels(recs, template, "avery-5160")
    assert ds.page_count == 1                       # 7 labels, 30/sheet
    page = ds.documents[0].pages[0]
    bcs = [e for e in page.elements if e.kind == ElementKind.BARCODE]
    assert len(bcs) == 7
    assert bcs[0].data == "SKU0001"
    # second label sits one h-pitch to the right of the first
    xs = sorted({round(b.bbox.x) for b in bcs})
    assert len(xs) >= 3


def test_afp_image_roundtrip(tmp_path):
    ds1 = _parse_afp(AFP_SAMPLE)
    out = tmp_path / "rt.afp"
    AfpWriter().write(ds1, str(out))
    ds2 = _parse_afp(str(out))
    assert _kinds(ds2)["image"] == _kinds(ds1)["image"] == 3
    assert _kinds(ds2)["text"] == _kinds(ds1)["text"]


def test_composed_afp_specific_roundtrip(tmp_path):
    psml = """<document><master-page name="m"/><page-sequence master="m"><flow>
    <paragraph size="10">Hello</paragraph>
    <barcode x="72" y="100" width="144" height="36" symbology="bcoca-01" data="ABC123"/>
    <overlay name="OVL1" x="0" y="0"/>
    <page-segment name="SEG1" x="72" y="200"/>
    <structured-field hex="5a0010d3eeee0000000000000000"/>
    </flow></page-sequence></document>"""
    ds = LayoutEngine(loader.load_string(psml)).run()
    out = tmp_path / "c.afp"
    AfpWriter().write(ds, str(out))
    ds2 = _parse_afp(str(out))
    bcs = [e for _, pg in ds2.iter_pages() for e in pg.elements if e.kind == ElementKind.BARCODE]
    assert len(bcs) == 1
    assert bcs[0].data == "ABC123"          # barcode data round-trips cleanly
