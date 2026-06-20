""" Integration tests driving process steps through the runner (the CLI path). """

from xml.dom import minidom

import fitz

from process.runner import run_step
from tests.conftest import AFP_SAMPLE


def _step(xml):
    return minidom.parseString(xml).documentElement


def test_nup_process_runs(tmp_path):
    out = tmp_path / "n.pdf"
    step = _step(
        f'<step name="nup" rows="2" cols="2" page-size="letter" rotate="90" '
        f'margin-top="18" margin-left="18">'
        f'<file name="{AFP_SAMPLE}" file_type="afp" type="input"/>'
        f'<file name="{out.as_posix()}" file_type="pdf" type="output"/></step>')
    run_step(step)
    assert out.exists()
    doc = fitz.open(str(out))
    try:
        assert len(doc) == 1            # 3 pages, 2x2 -> 1 sheet
    finally:
        doc.close()


def test_edit_process_runs(tmp_path):
    out = tmp_path / "e.pdf"
    captured = tmp_path / "c.json"
    step = _step(
        f'<step name="edit" extract_to="{captured.as_posix()}">'
        f'<file name="{AFP_SAMPLE}" file_type="afp" type="input"/>'
        f'<file name="{out.as_posix()}" file_type="pdf" type="output"/>'
        f'<extract kind="text" window="0,0,612,72" field="heading"/>'
        f'<delete kind="image"/>'
        f'<add kind="barcode" symbology="code128" x="430" y="40" width="150" height="36" data="X1"/>'
        f'</step>')
    run_step(step)
    assert out.exists() and captured.exists()


def test_spec_driven_extract(tmp_path):
    # The step only names the process + a spec; the spec carries inputs/index/fields.
    spec = tmp_path / "ex.xml"
    idx = tmp_path / "out.idx"
    spec.write_text(
        f'<spec process="extract">'
        f'<inputs><file name="{AFP_SAMPLE}" type="afp"/></inputs>'
        f'<index name="{idx.as_posix()}" format="json"/>'
        f'<identify by="window" value="0,0,612,72"/>'
        f'<fields><field name="heading" window="0,0,612,72"/></fields></spec>',
        encoding="utf-8")
    run_step(_step(f'<step name="extract" spec="{spec.as_posix()}"/>'))
    assert idx.exists() and (tmp_path / "out.docs.idx").exists()


def test_spec_driven_nup_booklet(tmp_path):
    # Per-cell imposition with page references (n = last page, 1 = first page).
    spec = tmp_path / "bk.xml"
    out = tmp_path / "bk.pdf"
    spec.write_text(
        f'<spec process="nup">'
        f'<inputs><file name="{AFP_SAMPLE}" type="afp"/></inputs>'
        f'<outputs><file name="{out.as_posix()}" type="pdf"/></outputs>'
        f'<imposition page-width="792" page-height="612" rows="1" cols="2" group-size="4">'
        f'<cell row="0" col="0" page="n"/><cell row="0" col="1" page="1"/>'
        f'</imposition></spec>', encoding="utf-8")
    run_step(_step(f'<step name="nup" spec="{spec.as_posix()}"/>'))
    doc = fitz.open(str(out))
    try:
        assert round(doc[0].rect.width) == 792 and round(doc[0].rect.height) == 612
    finally:
        doc.close()


def test_extract_then_merge_with_spec(tmp_path):
    spec = tmp_path / "spec.xml"
    spec.write_text(
        '<spec><identify by="window" value="0,0,612,72"/>'
        '<fields><field name="heading" window="0,0,612,72"/></fields>'
        '<enhancements>'
        '<add kind="barcode" symbology="code128" x="400" y="40" width="160" height="36" data="{heading}"/>'
        '</enhancements></spec>', encoding="utf-8")
    idx = tmp_path / "s.idx"
    out = tmp_path / "m.pdf"
    run_step(_step(
        f'<step name="extract" spec="{spec.as_posix()}" index="{idx.as_posix()}">'
        f'<file name="{AFP_SAMPLE}" file_type="afp" type="input"/></step>'))
    assert idx.exists() and (tmp_path / "s.docs.idx").exists()
    run_step(_step(
        f'<step name="merge" spec="{spec.as_posix()}" index="{idx.as_posix()}">'
        f'<file name="{out.as_posix()}" file_type="pdf" type="output"/></step>'))
    assert out.exists()
    doc = fitz.open(str(out))
    try:
        assert len(doc) == 3            # one identified document per page
    finally:
        doc.close()
