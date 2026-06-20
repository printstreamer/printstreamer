""" Tests for PSML compose: flow, pagination, headers/footers, primitives, index. """

import os
from xml.dom import minidom

from markup import loader
from markup.layout import LayoutEngine
from model.element import ElementKind
from process.runner import run_step

TINY = """<document>
<master-page name="m" page-width="200" page-height="150" margin-top="10"
   margin-bottom="20" margin-left="10" margin-right="10" columns="1" footer-extent="14">
  <footer><paragraph size="8" text-align="center">p <page-number/>/<page-count/></paragraph></footer>
</master-page>
<page-sequence master="m"><flow>
<paragraph size="10" line-height="12">%s</paragraph>
</flow></page-sequence></document>"""


def _compose_string(psml):
    return LayoutEngine(loader.load_string(psml)).run()


def test_flow_paginates():
    ds = _compose_string(TINY % " ".join(f"word{i}" for i in range(120)))
    assert ds.page_count > 1


def test_footer_page_of_count_filled():
    ds = _compose_string(TINY % " ".join(f"word{i}" for i in range(120)))
    total = ds.page_count
    assert total > 1
    for pg in ds.documents[0].pages:
        footers = [e.text for e in pg.elements if e.text.startswith("p ")]
        # Footer carries the resolved "page-number / page-count" field values.
        assert footers and footers[0].split() == ["p", str(pg.number), "/", str(total)]


def test_wrapping_produces_multiple_lines():
    ds = _compose_string(TINY % " ".join(["alpha"] * 40))
    page = ds.documents[0].pages[0]
    ys = {round(e.position.y) for e in page.elements
          if e.kind == ElementKind.TEXT and e.text.startswith("alpha")}
    assert len(ys) > 1            # wrapped onto multiple baselines


def test_styles_and_color():
    psml = """<document><master-page name="m"/>
    <style name="red" color="#ff0000" size="18"/>
    <page-sequence master="m"><flow>
    <paragraph style="red">Hello</paragraph></flow></page-sequence></document>"""
    ds = _compose_string(psml)
    el = next(e for _, pg in ds.iter_pages() for e in pg.elements
              if e.kind == ElementKind.TEXT and e.text == "Hello")
    assert el.font_size == 18
    assert el.color.to_rgb() == (1.0, 0.0, 0.0)


def test_primitives_present():
    psml = """<document><master-page name="m"/><page-sequence master="m"><flow>
    <line x1="10" y1="10" x2="100" y2="10" color="#000000"/>
    <rectangle x="10" y="20" width="50" height="30" color="#0000ff"/>
    <barcode x="10" y="60" width="120" height="36" symbology="code128" data="ABC"/>
    </flow></page-sequence></document>"""
    ds = _compose_string(psml)
    kinds = {e.kind for _, pg in ds.iter_pages() for e in pg.elements}
    assert ElementKind.LINE in kinds
    assert ElementKind.GRAPHIC in kinds
    assert ElementKind.BARCODE in kinds


def test_inline_adjacency_preserved():
    psml = ('<document><master-page name="m"/><page-sequence master="m"><flow>'
            '<paragraph size="10">ref#<page-number/>.</paragraph>'
            '</flow></page-sequence></document>')
    ds = _compose_string(psml)
    runs = [e.text for pg in ds.documents[0].pages for e in pg.elements]
    # "ref#", the page-number field, and "." are separate runs with no spurious spaces.
    assert "ref#" in runs and "." in runs
    assert not any(r.startswith(" ") or r.endswith(" ") for r in runs if r.strip())


def test_pdf_bookmarks(tmp_path):
    import fitz
    psml = ('<document><master-page name="m"/>'
            '<page-sequence master="m"><bookmark name="b" title="Chapter 1"/>'
            '<flow><paragraph size="10">hi</paragraph></flow></page-sequence></document>')
    ds = _compose_string(psml)
    from writer.pdf_writer import PdfWriter
    out = tmp_path / "bm.pdf"
    PdfWriter().write(ds, str(out))
    doc = fitz.open(str(out))
    try:
        toc = doc.get_toc()
        assert any("Chapter 1" in entry[1] for entry in toc)
    finally:
        doc.close()


def test_table_columns_colspan_borders_wrapping():
    psml = ('<document><master-page name="m" page-width="400" page-height="300" '
            'margin-top="20" margin-bottom="20" margin-left="20" margin-right="20"/>'
            '<page-sequence master="m"><flow>'
            '<table border="0.5" cellpadding="4">'
            '<column width="100"/><column width="240"/>'
            '<row><cell>Item</cell><cell>Desc</cell></row>'
            '<row><cell>SKU-1</cell>'
            '<cell>A long description that should wrap onto multiple lines in the cell</cell></row>'
            '<row><cell colspan="2"><paragraph text-align="center">end</paragraph></cell></row>'
            '</flow></table></page-sequence></document>')
    # note: table closed inside flow
    psml = psml.replace("</flow></table>", "</table></flow>")
    ds = _compose_string(psml)
    page = ds.documents[0].pages[0]
    graphics = [e for e in page.elements if e.kind == ElementKind.GRAPHIC]
    texts = [e for e in page.elements if e.kind == ElementKind.TEXT]
    assert len(graphics) == 5                         # one border box per cell
    # the wrapping cell produced more than one line at the same x
    wrap_xs = [round(t.position.x) for t in texts if t.position.x > 100]
    assert wrap_xs.count(wrap_xs[0]) >= 2 if wrap_xs else False


def test_compose_process_emits_indexes(tmp_path):
    psml = tmp_path / "d.psml"
    psml.write_text(TINY % "hello world", encoding="utf-8")
    out = tmp_path / "d.pdf"
    idx = tmp_path / "d.idx"
    doc = minidom.parseString(
        f'<step name="compose" index="{idx.as_posix()}" index_format="json">'
        f'<file name="{psml.as_posix()}" type="input"/>'
        f'<file name="{out.as_posix()}" file_type="pdf" type="output"/></step>').documentElement
    run_step(doc)
    assert out.exists()
    assert idx.exists()
    assert (tmp_path / "d.docs.idx").exists()
