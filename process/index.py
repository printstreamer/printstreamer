""" Index records, extraction fields, and multi-format index serialization.

An index file is the durable handoff between an ``extract`` pass and a later
``merge`` pass. Each record locates a page/document in the source stream (by byte,
page, document, and record offsets) and carries any user-requested extracted fields
(windowed text, hex/text matches, or page tags). It serializes to text, csv, tab,
xml, or json, optionally compressed.
"""

from __future__ import annotations

import csv
import io
import json
from dataclasses import asdict, dataclass, field
from xml.sax.saxutils import escape

from model.geometry import Rect
from model import visitor
from parse_options import PageSink


@dataclass
class FieldSpec:
    """ A user-requested extraction field. Exactly one selector is used per spec. """
    name: str
    window: Rect | None = None          # extract text within this window
    text: str | None = None             # presence/match of a text string
    hex: str | None = None              # presence of a hex byte sequence
    regex: bool = False


@dataclass
class IndexRecord:
    """ One index entry locating a page within the source stream. """
    source: str = ""                    # source file path
    document_number: int = 0
    document_name: str | None = None
    page_number: int = 0                # page number within the stream
    page_in_document: int = 0
    page_count: int | None = None       # document page count (on doc boundary)
    byte_offset: int | None = None
    record_number: int | None = None
    fields: dict = field(default_factory=dict)


def document_index_from_pages(page_records: list[IndexRecord]) -> list[IndexRecord]:
    """ Derive a document index (one record per document, with page count and the
    document's start offsets) from a list of page-index records. The page index
    enables page reorder/n-up; the document index enables document-level selection. """
    docs: dict = {}
    order: list = []
    for r in page_records:
        key = (r.source, r.document_number)
        if key not in docs:
            docs[key] = IndexRecord(
                source=r.source, document_number=r.document_number,
                document_name=r.document_name, page_number=r.page_number,
                byte_offset=r.byte_offset, record_number=r.record_number,
                page_count=0)
            order.append(key)
        docs[key].page_count += 1
    return [docs[k] for k in order]


def page_index_from_model(doc_set, source: str = "") -> list[IndexRecord]:
    """ Build a page index from an in-memory model (e.g. a composed document). """
    records = []
    page_no = 0
    for di, doc in enumerate(doc_set.documents, start=1):
        for pi, page in enumerate(doc.pages, start=1):
            page_no += 1
            records.append(IndexRecord(
                source=source, document_number=di, document_name=doc.name,
                page_number=page_no, page_in_document=pi,
                record_number=page.number))
    return records


def _page_matches(page, spec: FieldSpec) -> bool:
    """ True if a page satisfies a selector (used for document identification). """
    if spec.window is not None:
        return bool(visitor.select_in_window(page, spec.window, contained=False))
    if spec.text is not None:
        return bool(visitor.select_by_text(page, spec.text, regex=spec.regex))
    if spec.hex is not None:
        return bool(visitor.select_by_hex(page, spec.hex))
    return False


def extract_fields(page, specs: list[FieldSpec]) -> dict:
    """ Evaluate extraction specs against a page, returning name -> value. """
    out = {}
    for spec in specs:
        if spec.window is not None:
            hits = visitor.select_in_window(page, spec.window, contained=False)
            out[spec.name] = " ".join(getattr(h.element, "text", "") for h in hits).strip()
        elif spec.text is not None:
            hits = visitor.select_by_text(page, spec.text, regex=spec.regex)
            out[spec.name] = bool(hits)
        elif spec.hex is not None:
            hits = visitor.select_by_hex(page, spec.hex)
            out[spec.name] = bool(hits)
    return out


# --- serialization ---------------------------------------------------------

def serialize(records: list[IndexRecord], fmt: str = "json") -> bytes:
    fmt = (fmt or "json").lower()
    if fmt == "json":
        return _to_json(records)
    if fmt == "xml":
        return _to_xml(records)
    if fmt in ("csv", "tab", "text"):
        return _to_delimited(records, fmt)
    raise ValueError(f"Unknown index format: {fmt!r}")


def _to_json(records):
    return json.dumps([asdict(r) for r in records], indent=2).encode("utf-8")


def _to_xml(records):
    buf = io.StringIO()
    buf.write("<index>\n")
    for r in records:
        buf.write("  <record")
        for k, v in asdict(r).items():
            if k == "fields":
                continue
            if v is not None:
                buf.write(f' {k}="{escape(str(v))}"')
        buf.write(">\n")
        for fk, fv in r.fields.items():
            buf.write(f'    <field name="{escape(str(fk))}">{escape(str(fv))}</field>\n')
        buf.write("  </record>\n")
    buf.write("</index>\n")
    return buf.getvalue().encode("utf-8")


def _to_delimited(records, fmt):
    delim = {"csv": ",", "tab": "\t", "text": "\t"}[fmt]
    field_names = []
    for r in records:
        for k in r.fields:
            if k not in field_names:
                field_names.append(k)
    base_cols = ["source", "document_number", "document_name", "page_number",
                 "page_in_document", "page_count", "byte_offset", "record_number"]
    buf = io.StringIO()
    w = csv.writer(buf, delimiter=delim, lineterminator="\n")
    w.writerow(base_cols + field_names)
    for r in records:
        row = [getattr(r, c) for c in base_cols]
        row += [r.fields.get(fn, "") for fn in field_names]
        w.writerow(row)
    return buf.getvalue().encode("utf-8")


def load(data: bytes, fmt: str = "json") -> list[IndexRecord]:
    """ Load index records from serialized bytes (json or xml supported for merge). """
    fmt = (fmt or "json").lower()
    if fmt == "json":
        return [IndexRecord(**{k: v for k, v in d.items()})
                for d in json.loads(data.decode("utf-8"))]
    raise ValueError(f"Loading index format {fmt!r} is not supported yet")


# --- streaming sink --------------------------------------------------------

class IndexSink(PageSink):
    """ Builds index records as pages stream past, for bounded-memory extraction.

    Document identification (how pages group into documents) is user-defined:
    - ``boundary``: start a new document whenever a page matches a selector
      (text / hex / window) — identification by any page element;
    - ``pages_per_document``: a fixed page count per document;
    - otherwise the source stream's own document boundaries are used.
    """

    def __init__(self, source: str, specs: list[FieldSpec] | None = None,
                 pages_per_document: int | None = None,
                 boundary: FieldSpec | None = None):
        self.source = source
        self.specs = specs or []
        self.pages_per_document = pages_per_document
        self.boundary = boundary
        self.records: list[IndexRecord] = []
        self._doc_no = 0
        self._page_no = 0
        self._page_in_doc = 0

    def _custom_identification(self):
        return self.boundary is not None or self.pages_per_document is not None

    def on_document_start(self, document):
        # Source-driven identification: each source document starts a new document.
        if not self._custom_identification():
            self._doc_no += 1
            self._page_in_doc = 0

    def on_page(self, document, page):
        self._page_no += 1
        if self.boundary is not None:
            if self._doc_no == 0 or _page_matches(page, self.boundary):
                self._doc_no += 1
                self._page_in_doc = 0
        elif self.pages_per_document:
            if (self._page_no - 1) % self.pages_per_document == 0:
                self._doc_no += 1
                self._page_in_doc = 0
        self._page_in_doc += 1
        sref = page.source_ref
        self.records.append(IndexRecord(
            source=self.source,
            document_number=self._doc_no,
            document_name=document.name if document else None,
            page_number=self._page_no,
            page_in_document=self._page_in_doc,
            byte_offset=getattr(sref, "byte_offset", None),
            record_number=getattr(sref, "record_number", None),
            fields=extract_fields(page, self.specs),
        ))
