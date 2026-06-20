""" Tests for the PostScript, PCL, and Metacode readers (Phase 5). """

from stream_parser import StreamParser
from model.element import ElementKind


def _parse(path, file_type):
    p = StreamParser()
    p.add_file(p, str(path), file_type=file_type, type="input")
    p.input_files[-1].parse()
    return p.document_set


def _texts(ds):
    return [e.text for _, pg in ds.iter_pages() for e in pg.elements
            if e.kind == ElementKind.TEXT]


def test_postscript(tmp_path):
    ps = tmp_path / "t.ps"
    ps.write_text(
        "%!PS-Adobe-3.0\n%%BoundingBox: 0 0 612 792\n"
        "/Helvetica findfont 24 scalefont setfont\n"
        "1 0 0 setrgbcolor 72 700 moveto (Hello PS) show\n"
        "2 setlinewidth 72 660 moveto 540 660 lineto stroke\n"
        "72 600 100 40 rectfill showpage\n"
        "72 700 moveto (Page Two) show showpage\n", encoding="latin-1")
    ds = _parse(ps, "ps")
    assert ds.page_count == 2
    assert "Hello PS" in _texts(ds)
    kinds = {e.kind for _, pg in ds.iter_pages() for e in pg.elements}
    assert ElementKind.LINE in kinds and ElementKind.GRAPHIC in kinds
    red = next(e for _, pg in ds.iter_pages() for e in pg.elements
               if getattr(e, "text", "") == "Hello PS")
    assert red.color.to_rgb() == (1.0, 0.0, 0.0)
    assert abs(red.position.y - (792 - 700)) < 1     # PS bottom-left -> model top-left


def test_pcl(tmp_path):
    ESC = b"\x1b"
    data = (ESC + b"E" + ESC + b"(s14V" + ESC + b"*p150x100Y" + b"Hello PCL"
            + b"\x0c" + ESC + b"*p150x150Y" + b"Page Two" + b"\x0c")
    pcl = tmp_path / "t.pcl"
    pcl.write_bytes(data)
    ds = _parse(pcl, "pcl")
    assert ds.page_count == 2
    assert "Hello PCL" in _texts(ds)
    el = next(e for _, pg in ds.iter_pages() for e in pg.elements
              if getattr(e, "text", "") == "Hello PCL")
    assert abs(el.position.x - 150 * 72 / 300) < 1   # 150 dots @300dpi -> 36pt


def test_metacode(tmp_path):
    def record(b):
        return bytes([len(b)]) + b

    def text(s):
        e = s.encode("cp500")
        return bytes([0xC3, len(e)]) + e

    body = (bytes([0xC2, 0x01]) + bytes([0xC1]) + (300).to_bytes(2, "big")
            + bytes([0xC0]) + (200).to_bytes(2, "big") + text("Hello Metacode") + bytes([0xFF]))
    met = tmp_path / "t.met"
    met.write_bytes(record(body))
    ds = _parse(met, "metacode")
    assert ds.page_count == 1
    assert "Hello Metacode" in _texts(ds)
    el = next(e for _, pg in ds.iter_pages() for e in pg.elements)
    assert abs(el.position.x - 72) < 1               # 300 dots @300dpi -> 72pt
