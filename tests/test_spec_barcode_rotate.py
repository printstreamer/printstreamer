""" Tests for spec.xml, barcode rendering, and rotated n-up imposition. """

import io

import model as m
from process import operations
from process.spec import load_spec_string
from process.imposition import impose, rotate_point, rotated_size
from model.element import ElementKind


SPEC = """<spec>
  <identify by="window" value="0,0,612,72"/>
  <fields><field name="acct" window="0,0,300,20"/></fields>
  <enhancements>
    <delete kind="image"/>
    <add kind="text" x="72" y="60" size="9">Acct {acct}</add>
    <add kind="barcode" symbology="code128" x="400" y="40" width="160" height="36" data="{acct}"/>
    <add kind="omr" x="18" y="80" width="8" height="200" data="1011"/>
    <add kind="rectangle" x="72" y="100" width="200" height="2" fill="#000000"/>
  </enhancements>
</spec>"""


def _page_with(*elements):
    ds = m.StreamDocumentSet()
    d = ds.add_document(m.Document(name="d"))
    pg = d.add_page(m.Page(number=1, size=m.Rect(0, 0, 612, 792)))
    for e in elements:
        pg.add_element(e)
    return pg


def test_spec_parses_identify_fields_operations():
    spec = load_spec_string(SPEC)
    assert spec.boundary is not None and spec.boundary.window is not None
    assert [f.name for f in spec.fields] == ["acct"]
    verbs = [(o["verb"], o.get("kind")) for o in spec.operations]
    assert ("delete", "image") in verbs
    assert ("add", "barcode") in verbs and ("add", "omr") in verbs


def test_spec_enhancements_with_substitution():
    spec = load_spec_string(SPEC)
    pg = _page_with(
        m.ImageElement(bbox=m.Rect(0, 0, 612, 792)),
        m.TextElement(text="x", position=m.Point(0, 0), bbox=m.Rect(0, 0, 5, 5)))
    operations.apply_to_page(pg, spec.operations, context={"acct": "A-1009"})
    assert all(e.kind != ElementKind.IMAGE for e in pg.elements)        # deleted
    bcs = [e for e in pg.elements if e.kind == ElementKind.BARCODE]
    assert any(b.symbology == "code128" and b.data == "A-1009" for b in bcs)  # substituted
    assert any(b.symbology == "omr" for b in bcs)
    assert any("A-1009" in (getattr(e, "text", "") or "") for e in pg.elements)


def test_barcode_render_supported():
    from writer import barcodes
    sup = barcodes.supported()
    for s in ("3of9", "code39", "128c", "code128", "qr", "datamatrix", "omr"):
        assert s in sup


def test_barcodes_draw_to_pdf(tmp_path):
    import fitz
    from writer.pdf_writer import PdfWriter
    pg = _page_with(
        m.BarcodeElement(symbology="code39", data="ABC123", bbox=m.Rect(72, 700, 160, 40)),
        m.BarcodeElement(symbology="qr", data="hi", bbox=m.Rect(72, 600, 80, 80)),
        m.BarcodeElement(symbology="omr", data="10110", bbox=m.Rect(20, 400, 8, 200)))
    out = tmp_path / "bc.pdf"
    PdfWriter().write(_wrap_set(pg), str(out))
    doc = fitz.open(str(out))
    try:
        assert len(doc[0].get_drawings()) > 20            # real barcode vectors
    finally:
        doc.close()


def _wrap(pg):
    d = m.Document(name="d"); d.pages.append(pg); return d


def _wrap_set(pg):
    ds = m.StreamDocumentSet(); ds.documents.append(_wrap(pg)); return ds


def test_rotation_math():
    assert rotate_point(0, 0, 90, 100, 200) == (200, 0)
    assert rotated_size(100, 200, 90) == (200, 100)
    assert rotate_point(10, 20, 180, 100, 200) == (90, 180)


def test_rotated_nup():
    ds = m.StreamDocumentSet()
    d = ds.add_document(m.Document(name="d"))
    for i in (1, 2):
        pg = d.add_page(m.Page(number=i, size=m.Rect(0, 0, 612, 792)))
        pg.add_element(m.TextElement(text=f"P{i}", position=m.Point(72, 72),
                                     font_size=12, bbox=m.Rect(72, 60, 30, 12)))
    out = impose(ds, 1, 2, m.Rect(0, 0, 792, 612), rotate=90)
    sheet = out.documents[0].pages[0]
    texts = [e for e in sheet.elements if e.kind == ElementKind.TEXT]
    assert len(texts) == 2
    assert all(e.orientation == 90 for e in texts)        # pages rotated
