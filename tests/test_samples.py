""" Validate the collected sample corpus in the data directory.

These tests run every real sample produced by
``scripts/sample_printstream_file_collection.py`` through its reader, confirming the
parsers never crash and produce a sensible model. The data directory is git-ignored, so
each case skips gracefully when its sample is not present (e.g. a fresh clone that has
not run the collection script).
"""

import json
import os

import fitz
import pytest

import paths
from parse_options import ParseOptions
from stream_parser import StreamParser
from model.element import ElementKind
from writer.pdf_writer import PdfWriter

DATA = paths.data_dir()
JSL = os.path.join(paths.PROJECT_ROOT, "config", "metacode.jsl")

# The canonical corpus: downloaded targets + the generated Metacode sample + the
# pre-existing AFP/PDF inputs. (filename, file_type).
EXPECTED = [
    ("PDF_Small_Interactive.pdf", "pdf"),
    ("PDF_Medium_Payload.pdf", "pdf"),
    ("PostScript_Small_Vector.ps", "ps"),
    ("PostScript_Medium_Layout.ps", "ps"),
    ("PCL_Technical_Matrix.pcl", "pcl"),
    ("PCL_Macro_Overlay.pcl", "pcl"),
    ("AFP_Structured_Document.afp", "afp"),
    ("Metacode_Generated_Mock.met", "metacode"),
    ("test_afp.afp", "afp"),
    ("test_pdf.pdf", "pdf"),
]

FORMAT_FAMILY = {".pdf": "PDF", ".ps": "PostScript", ".afp": "AFP",
                 ".pcl": "PCL", ".met": "Metacode"}


def _parse(name, ftype):
    path = os.path.join(DATA, name)
    if not os.path.exists(path):
        pytest.skip(f"sample not collected: {name}")
    opts = ParseOptions()
    if ftype == "metacode":
        opts.jsl_path = JSL
    p = StreamParser(options=opts)
    p.add_file(p, path, file_type=ftype, type="input")
    for f in p.input_files:
        f.parse()
    return p


@pytest.mark.parametrize("name,ftype", EXPECTED)
def test_sample_parses(name, ftype):
    """ Every sample parses without crashing and yields something in the model. """
    p = _parse(name, ftype)
    ds = p.document_set
    read = p.input_files[0].records + p.input_files[0].pages
    # A document, a page, or at least structured records were read.
    assert ds.document_count >= 1 or ds.page_count >= 1 or read > 0


@pytest.mark.parametrize("name,ftype", [(n, t) for n, t in EXPECTED if t in ("pdf", "pcl")])
def test_renderable_sample_has_pages(name, ftype):
    """ PDF and (post-extension) PCL samples produce pages and transform to PDF. """
    p = _parse(name, ftype)
    ds = p.document_set
    assert ds.page_count >= 1
    out = os.path.join(DATA, f"_t_{name}.pdf")
    try:
        PdfWriter().write(ds, out)
        doc = fitz.open(out)
        try:
            assert len(doc) >= 1
        finally:
            doc.close()
    finally:
        if os.path.exists(out):
            os.remove(out)


def test_postscript_samples_parse_safely():
    """ Real CUPS/xpdf PostScript must parse without crashing or hanging (bounded).
    These specific samples use Type3 embedded fonts our best-effort interpreter does not
    fully render, so page output is not required - only that parsing is safe. """
    for name in ("PostScript_Small_Vector.ps", "PostScript_Medium_Layout.ps"):
        p = _parse(name, "ps")
        assert p.document_set.document_count >= 1


def test_metacode_sample_is_jsl_driven():
    """ The Metacode sample parses with the JSL, recognizes its DJDE record, and renders
    a text page. """
    p = _parse("Metacode_Generated_Mock.met", "metacode")
    ds = p.document_set
    assert ds.page_count >= 1
    kinds = [e.kind for _, pg in ds.iter_pages() for e in pg.elements]
    texts = [e.text for _, pg in ds.iter_pages() for e in pg.elements
             if e.kind == ElementKind.TEXT]
    assert ElementKind.CONTAINER in kinds          # the preserved DJDE record
    assert any("Metacode" in t for t in texts)


def test_afp_overlay_resource_parses():
    """ The AFP sample is an overlay resource (BMO..EMO): no pages, but its records are
    read without error. """
    p = _parse("AFP_Structured_Document.afp", "afp")
    assert p.input_files[0].records > 0


def test_manifest_covers_known_samples():
    """ The collection manifest lists every present known sample, flags it, and
    classifies it by the expected format family. """
    report = os.path.join(DATA, "printstream_test_report.json")
    if not os.path.exists(report):
        pytest.skip("manifest not generated")
    with open(report) as fh:
        registry = {r["file_name"]: r for r in json.load(fh)["test_suite_registry"]}
    checked = 0
    for name, _ftype in EXPECTED:
        if not os.path.exists(os.path.join(DATA, name)):
            continue
        checked += 1
        assert name in registry, f"{name} missing from manifest"
        entry = registry[name]
        assert entry.get("known") is True
        family = FORMAT_FAMILY[os.path.splitext(name)[1].lower()]
        assert family in entry["target_format_classification"]
    if checked == 0:
        pytest.skip("no known samples present")
