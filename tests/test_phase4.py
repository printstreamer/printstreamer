""" Tests for Phase 4: n-up imposition, reorder, and split. """

import model as m
from process.imposition import impose, transform_element
from model.element import ElementKind


def _doc_set(n_pages):
    ds = m.StreamDocumentSet()
    doc = ds.add_document(m.Document(name="d"))
    for i in range(1, n_pages + 1):
        pg = doc.add_page(m.Page(number=i, size=m.Rect(0, 0, 612, 792)))
        pg.add_element(m.TextElement(text=f"page{i}", position=m.Point(72, 72),
                                     font_size=12, bbox=m.Rect(72, 60, 40, 12)))
    return ds


def test_transform_element_scales_and_translates():
    el = m.TextElement(text="x", position=m.Point(100, 100), font_size=10,
                       bbox=m.Rect(100, 90, 20, 10))
    out = transform_element(el, 0.5, 0.5, 10, 20)
    assert (out.position.x, out.position.y) == (60.0, 70.0)
    assert out.font_size == 5.0
    assert out.bbox.width == 10.0


def test_nup_imposition():
    ds = _doc_set(4)
    out = impose(ds, 2, 2, m.Rect(0, 0, 612, 792))
    assert out.page_count == 1                       # 4 pages on one 2x2 sheet
    sheet = out.documents[0].pages[0]
    texts = [e for e in sheet.elements if e.kind == ElementKind.TEXT]
    assert len(texts) == 4
    assert all(t.font_size < 12 for t in texts)      # scaled to fit cells
    # four distinct cell origins
    origins = {(round(t.position.x), round(t.position.y)) for t in texts}
    assert len(origins) == 4


def test_nup_multiple_sheets():
    ds = _doc_set(9)
    out = impose(ds, 2, 2, m.Rect(0, 0, 612, 792))
    assert out.page_count == 3                        # ceil(9/4)


def test_reorder_via_model():
    ds = _doc_set(3)
    pages = {p.number: p for _, p in ds.iter_pages()}
    out = m.StreamDocumentSet()
    doc = out.add_document(m.Document(name="r"))
    for n in (3, 1, 2):
        doc.add_page(pages[n])
    order = [p.elements[0].text for p in out.documents[0].pages]
    assert order == ["page3", "page1", "page2"]
