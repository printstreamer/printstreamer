""" Tests for PCL/Metacode writers, IOCA decode, GOCA parse, deeper PostScript. """

import io

from markup import loader
from markup.layout import LayoutEngine
from stream_parser import StreamParser
from model.element import ElementKind


def _compose(psml):
    return LayoutEngine(loader.load_string(psml)).run()


def _reparse(path, ftype):
    p = StreamParser()
    p.add_file(p, str(path), file_type=ftype, type="input")
    p.input_files[-1].parse()
    return p.document_set


def _texts(ds):
    return [e.text for _, pg in ds.iter_pages() for e in pg.elements
            if e.kind == ElementKind.TEXT]


_DOC = ('<document><master-page name="m"/><page-sequence master="m"><flow>'
        '<paragraph size="12">First Line</paragraph>'
        '<paragraph size="10">Second Line</paragraph>'
        '</flow></page-sequence></document>')


def test_pcl_writer_roundtrip(tmp_path):
    from writer.pcl_writer import PclWriter
    ds = _compose(_DOC)
    out = tmp_path / "o.pcl"
    PclWriter().write(ds, str(out))
    ds2 = _reparse(out, "pcl")
    assert ds2.page_count == 1
    assert _texts(ds2) == ["First Line", "Second Line"]


def test_metacode_writer_roundtrip(tmp_path):
    from writer.metacode_writer import MetacodeWriter
    ds = _compose(_DOC)
    out = tmp_path / "o.met"
    MetacodeWriter().write(ds, str(out))
    ds2 = _reparse(out, "metacode")
    assert ds2.page_count == 1
    assert _texts(ds2) == ["First Line", "Second Line"]


def test_ioca_decoder_standard_g4():
    from PIL import Image
    from afp.ioca_image import ioca_to_png
    img = Image.new("1", (48, 24), 1)
    for x in range(8, 40):
        for y in range(6, 18):
            img.putpixel((x, y), 0)
    buf = io.BytesIO()
    img.save(buf, format="TIFF", compression="group4")
    buf.seek(0)
    t = Image.open(buf); t.load()
    off = t.tag_v2[273][0]; cnt = t.tag_v2[279][0]
    buf.seek(off); strip = buf.read(cnt)
    png = ioca_to_png(strip, 48, 24, "ioca-06")          # 0x06 = CCITT G4
    assert png is not None
    assert Image.open(io.BytesIO(png)).size == (48, 24)


def test_goca_orders_parse():
    from afp.afp_objects import AfpObjectContext
    from model.geometry import Rect
    ctx = AfpObjectContext(segment=None)
    # GLINE (0xC1) with one (x,y); GBOX (0xC0) with two corners.
    gline = bytes([0xC1, 4]) + (10).to_bytes(2, "big") + (20).to_bytes(2, "big")
    gbox = bytes([0xC0, 8]) + b"".join(v.to_bytes(2, "big") for v in (0, 0, 30, 40))
    ops = ctx._parse_goca(gline + gbox, Rect(0, 0, 100, 100))
    kinds = [o.op for o in ops]
    assert "polyline" in kinds and "box" in kinds


def test_pdf_internal_compression(tmp_path):
    import os
    from writer.registry import get_writer
    ds = _compose(_DOC)
    off = tmp_path / "off.pdf"
    on = tmp_path / "on.pdf"
    get_writer("pdf", {"internal_compress": "0"}).write(ds, str(off))
    get_writer("pdf", {"internal_compress": "1"}).write(ds, str(on))
    assert os.path.getsize(str(on)) < os.path.getsize(str(off))


def test_postscript_loops_and_arithmetic(tmp_path):
    ps = tmp_path / "d.ps"
    ps.write_text(
        "%!PS-Adobe-3.0\n%%BoundingBox: 0 0 612 792\n"
        "/Helvetica findfont 10 scalefont setfont 0 0 0 setrgbcolor\n"
        "0 1 4 { /i exch def 72 700 i 20 mul sub moveto (Row) show } for\n"
        "72 500 moveto 72 550 200 550 200 500 curveto stroke showpage\n",
        encoding="latin-1")
    ds = _reparse(ps, "ps")
    rows = [e for _, pg in ds.iter_pages() for e in pg.elements
            if getattr(e, "text", "") == "Row"]
    ys = sorted(round(e.position.y) for e in rows)
    assert ys == [92, 112, 132, 152, 172]                # loop + arithmetic positions
    lines = [e for _, pg in ds.iter_pages() for e in pg.elements
             if e.kind == ElementKind.LINE]
    assert len(lines) >= 8                                 # bezier flattened to segments
