""" Unit tests for the generic model and its selectors/edit operations. """

import model as m
from model import visitor


def _sample_set():
    ds = m.StreamDocumentSet()
    doc = ds.add_document(m.Document(name="DOC1"))
    pg = doc.add_page(m.Page(number=1, size=m.Rect(0, 0, 612, 792)))
    pg.add_element(m.TextElement(text="Hello World", position=m.Point(72, 100),
                                 bbox=m.Rect(72, 88, 60, 12), font_ref="F1"))
    pg.add_element(m.BarcodeElement(symbology="code128", data="12345",
                                    bbox=m.Rect(400, 600, 120, 40),
                                    raw=bytes.fromhex("d3eeeb")))
    pg.add_element(m.LineElement(start=m.Point(0, 0), end=m.Point(100, 0),
                                 bbox=m.Rect(0, 0, 100, 1)))
    return ds, doc, pg


def test_counts():
    ds, _, _ = _sample_set()
    assert ds.document_count == 1
    assert ds.page_count == 1


def test_select_by_text():
    ds, _, _ = _sample_set()
    hits = visitor.select_by_text(ds, "World")
    assert [h.element.text for h in hits] == ["Hello World"]


def test_select_by_hex():
    ds, _, _ = _sample_set()
    hits = visitor.select_by_hex(ds, "d3eeeb")
    assert len(hits) == 1
    assert hits[0].element.symbology == "code128"


def test_select_in_window():
    ds, _, _ = _sample_set()
    window = m.Rect(390, 590, 200, 100)
    hits = visitor.select_in_window(ds, window)
    assert [h.element.kind for h in hits] == [m.ElementKind.BARCODE]


def test_remove():
    ds, _, pg = _sample_set()
    removed = visitor.remove(visitor.iter_elements(ds, m.ElementKind.BARCODE))
    assert removed == 1
    assert all(e.kind != m.ElementKind.BARCODE for e in pg.elements)


def test_matrix_and_color():
    p = m.Matrix.translate(10, 20).multiply(m.Matrix.scale(0.5)).apply(m.Point(100, 100))
    assert (p.x, p.y) == (60.0, 70.0)
    assert m.Color.cmyk(0, 1, 1, 0).to_rgb() == (1, 0, 0)
