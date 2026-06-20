""" Tests for declarative edit operations (Phase 3). """

import model as m
from process import operations as ops
from model.element import ElementKind


def _sample():
    ds = m.StreamDocumentSet()
    d = ds.add_document(m.Document(name="d"))
    pg = d.add_page(m.Page(number=1, size=m.Rect(0, 0, 612, 792)))
    pg.add_element(m.TextElement(text="DELETE me", position=m.Point(72, 100),
                                 bbox=m.Rect(72, 90, 60, 12), font_size=10))
    pg.add_element(m.TextElement(text="KEEP this", position=m.Point(72, 120),
                                 bbox=m.Rect(72, 110, 60, 12), font_size=10))
    pg.add_element(m.BarcodeElement(symbology="code128", data="X",
                                    bbox=m.Rect(400, 600, 100, 40),
                                    raw=bytes.fromhex("d3eeeb")))
    return ds, pg


def test_delete_modify_add_extract():
    ds, pg = _sample()
    extracted = ops.apply_operations(ds, [
        {"verb": "delete", "text": "DELETE"},
        {"verb": "modify", "text": "KEEP", "set-color": "#ff0000", "set-size": "14"},
        {"verb": "delete", "hex": "d3eeeb"},
        {"verb": "add", "kind": "barcode", "x": "100", "y": "700",
         "symbology": "code39", "data": "NEW123"},
        {"verb": "extract", "kind": "text", "field": "remaining"},
    ])
    kept = [e for e in pg.elements if e.kind == ElementKind.TEXT]
    assert len(kept) == 1 and kept[0].text == "KEEP this"
    assert kept[0].font_size == 14.0 and kept[0].color.to_rgb() == (1.0, 0.0, 0.0)
    bcs = [e for e in pg.elements if e.kind == ElementKind.BARCODE]
    assert len(bcs) == 1 and bcs[0].data == "NEW123"      # old deleted, new added
    assert extracted == [{"field": "remaining", "page": 1, "value": "KEEP this"}]


def test_window_delete():
    ds, pg = _sample()
    ops.apply_operations(ds, [{"verb": "delete", "window": "390,590,200,100"}])
    assert all(e.kind != ElementKind.BARCODE for e in pg.elements)


def test_extract_with_delete_flag():
    ds, pg = _sample()
    out = ops.apply_operations(ds, [
        {"verb": "extract", "kind": "barcode", "field": "code", "delete": "true"}])
    assert out and out[0]["value"] == "X"
    assert all(e.kind != ElementKind.BARCODE for e in pg.elements)
