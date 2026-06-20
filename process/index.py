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
    """ One index entry locating a page or a logical document within the source stream.

    ``document_offset`` is the zero-based logical-document ordinal (the count of
    documents before it) and is the join key shared by the page and document indexes.
    For a page record, the byte/record span (``byte_offset``/``byte_count``,
    ``record_offset``/``record_count``) locates the page in the input. For a document
    record, the span locates the whole logical document, and the ``pi_*`` fields locate
    the document's fixed-length page records inside the page index file.
    """
    source: str = ""                    # input printstream file path
    document_offset: int = 0            # zero-based logical-document ordinal (join key)
    document_number: int = 0           # 1-based, retained for back-compat
    document_name: str | None = None
    page_number: int = 0                # page number within the stream
    page_in_document: int = 0
    page_count: int | None = None       # document page count (on doc boundary)
    page_offset: int | None = None      # first global page number of the document
    document_count: int = 1
    # span in the input printstream
    byte_offset: int | None = None
    byte_count: int | None = None
    record_number: int | None = None    # == record_offset (kept name for back-compat)
    record_offset: int | None = None
    record_count: int | None = None
    # (doc index only) span of this document's records inside the page index file
    pi_byte_offset: int | None = None
    pi_byte_count: int | None = None
    pi_record_offset: int | None = None
    pi_record_count: int | None = None
    pi_page_offset: int | None = None
    pi_page_count: int | None = None
    fields: dict = field(default_factory=dict)


def document_index_from_pages(page_records: list[IndexRecord]) -> list[IndexRecord]:
    """ Derive a document index (one record per logical document) from the page index.

    Each doc record gets two offset/count blocks: the document's span in the input
    printstream (byte/record/page/document), and the span of its page records inside
    the page index file (``pi_record_offset``/``pi_record_count`` = position and count
    of its fixed-length page records, plus the matching page span). The byte offsets
    into the page index file are filled at serialization time, when the record width is
    known. """
    docs: dict = {}
    order: list = []
    for pos, r in enumerate(page_records):
        key = (r.source, r.document_offset)
        d = docs.get(key)
        if d is None:
            d = IndexRecord(
                source=r.source, document_offset=r.document_offset,
                document_number=r.document_number, document_name=r.document_name,
                page_number=r.page_number, page_offset=r.page_number,
                byte_offset=r.byte_offset, byte_count=0,
                record_number=r.record_offset, record_offset=r.record_offset,
                record_count=0, page_count=0, document_count=1,
                pi_record_offset=pos, pi_record_count=0,
                pi_page_offset=r.page_number, pi_page_count=0)
            docs[key] = d
            order.append(key)
        d.page_count += 1
        d.pi_record_count += 1
        d.pi_page_count += 1
        if r.byte_count:
            d.byte_count += r.byte_count
        if r.record_count:
            d.record_count += r.record_count
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
            # Clip each run to the window using per-character advances for precision.
            out[spec.name] = " ".join(
                visitor.text_in_window(h.element, spec.window) for h in hits).strip()
        elif spec.text is not None:
            hits = visitor.select_by_text(page, spec.text, regex=spec.regex)
            out[spec.name] = bool(hits)
        elif spec.hex is not None:
            hits = visitor.select_by_hex(page, spec.hex)
            out[spec.name] = bool(hits)
    return out


# --- serialization ---------------------------------------------------------
#
# Default index format: flat, uncompressed, fixed-length-field records (one per line).
# Integer fields are right-justified zero-padded; string fields are left-justified
# space-padded and truncated to width. The page and document indexes have distinct,
# fixed schemas; spec extraction fields are appended to page records as fixed-width
# columns, with their names recorded in a single leading ``#FIELDS`` schema line.

PATH_WIDTH = 128
NAME_WIDTH = 32
FIELD_WIDTH = 40

# Each flat document-index record is padded to a fixed 2000 bytes (incl. its trailing
# newline) regardless of content, so a document's record can be read by seeking to
# ``document_offset * DOC_RECORD_SIZE`` and the reserved tail leaves room for future
# document-level fields without changing the layout.
DOC_RECORD_SIZE = 2000

# (name, width, kind) — kind "i" int (zero-padded), "s" string (space-padded).
PAGE_SCHEMA = [
    ("document_offset", 8, "i"), ("page_number", 8, "i"),
    ("page_in_document", 6, "i"), ("byte_offset", 12, "i"),
    ("byte_count", 10, "i"), ("record_offset", 10, "i"),
    ("record_count", 8, "i"), ("input_path", PATH_WIDTH, "s"),
]
DOC_SCHEMA = [
    ("document_offset", 8, "i"),
    ("byte_offset", 12, "i"), ("byte_count", 12, "i"),
    ("record_offset", 10, "i"), ("record_count", 10, "i"),
    ("page_offset", 8, "i"), ("page_count", 8, "i"),
    ("document_count", 6, "i"),
    ("pi_byte_offset", 12, "i"), ("pi_byte_count", 12, "i"),
    ("pi_record_offset", 10, "i"), ("pi_record_count", 10, "i"),
    ("pi_page_offset", 8, "i"), ("pi_page_count", 8, "i"),
    ("input_path", PATH_WIDTH, "s"), ("document_name", NAME_WIDTH, "s"),
]


# Schema column name -> IndexRecord attribute (where they differ).
_ALIAS = {"input_path": "source"}


def _fmt_field(value, width, kind):
    if kind == "i":
        return str(int(value or 0)).rjust(width)[:width]
    s = "" if value is None else str(value)
    return s.ljust(width)[:width]


def _flat_line(record, schema, extra_fields=None):
    cells = [_fmt_field(getattr(record, _ALIAS.get(n, n)), w, k) for n, w, k in schema]
    if extra_fields:
        for fn in extra_fields:
            cells.append(_fmt_field(record.fields.get(fn, ""), FIELD_WIDTH, "s"))
    return "".join(cells)


def _field_names(records):
    names = []
    for r in records:
        for k in r.fields:
            if k not in names:
                names.append(k)
    return names


def page_record_width(field_names) -> int:
    """ Byte width of one page index line incl. its trailing newline. """
    return sum(w for _, w, _ in PAGE_SCHEMA) + FIELD_WIDTH * len(field_names) + 1


def _to_flat_page(records):
    field_names = _field_names(records)
    out = []
    if field_names:
        out.append("#FIELDS " + " ".join(field_names))
    for r in records:
        out.append(_flat_line(r, PAGE_SCHEMA, field_names))
    return ("\n".join(out) + "\n").encode("utf-8")


def _to_flat_doc(records, page_field_names=None):
    """ Serialize the document index. Each record is padded to exactly
    ``DOC_RECORD_SIZE`` (2000) bytes — schema cells, then spaces, then a single LF as the
    2000th byte (no CR) — so document N is read by seeking to ``N * DOC_RECORD_SIZE`` and
    there is reserved room for future document-level fields. Each doc's byte span into the
    page index file is filled from the page-record width and the ``#FIELDS`` header. """
    width = page_record_width(page_field_names or [])
    header_len = 0
    if page_field_names:
        header_len = len("#FIELDS " + " ".join(page_field_names)) + 1
    out = bytearray()
    for r in records:
        r.pi_byte_offset = header_len + (r.pi_record_offset or 0) * width
        r.pi_byte_count = (r.pi_record_count or 0) * width
        line = _flat_line(r, DOC_SCHEMA).encode("utf-8")[:DOC_RECORD_SIZE - 1]
        out += line.ljust(DOC_RECORD_SIZE - 1, b" ") + b"\n"
    return bytes(out)


def serialize(records: list[IndexRecord], fmt: str = "flat",
              kind: str = "page", page_field_names=None) -> bytes:
    fmt = (fmt or "flat").lower()
    if fmt == "flat":
        return _to_flat_doc(records, page_field_names) if kind == "doc" \
            else _to_flat_page(records)
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


def load(data: bytes, fmt: str = "flat", kind: str = "page") -> list[IndexRecord]:
    """ Load index records from serialized bytes (flat default, or json). """
    fmt = (fmt or "flat").lower()
    if fmt == "flat":
        return _load_flat(data, kind)
    if fmt == "json":
        return [IndexRecord(**{k: v for k, v in d.items()})
                for d in json.loads(data.decode("utf-8"))]
    raise ValueError(f"Loading index format {fmt!r} is not supported yet")


def _load_flat(data: bytes, kind: str) -> list[IndexRecord]:
    schema = DOC_SCHEMA if kind == "doc" else PAGE_SCHEMA
    lines = data.decode("utf-8").splitlines()
    field_names = []
    records = []
    for line in lines:
        if line.startswith("#FIELDS"):
            field_names = line[len("#FIELDS"):].split()
            continue
        if not line.strip():
            continue
        rec = IndexRecord()
        off = 0
        for name, width, fkind in schema:
            cell = line[off:off + width]
            off += width
            attr = _ALIAS.get(name, name)
            if fkind == "i":
                setattr(rec, attr, int(cell) if cell.strip() else 0)
            else:
                setattr(rec, attr, cell.rstrip() or None)
        # extraction-field columns follow the fixed schema (page index only)
        for fn in field_names:
            cell = line[off:off + FIELD_WIDTH]
            off += FIELD_WIDTH
            rec.fields[fn] = cell.rstrip()
        # back-compat / convenience derived values
        rec.document_number = rec.document_number or (rec.document_offset + 1)
        rec.record_number = rec.record_offset if rec.record_offset is not None \
            else rec.record_number
        records.append(rec)
    return records


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
        rec_off = page.attributes.get("record_offset",
                                      getattr(sref, "record_number", None))
        self.records.append(IndexRecord(
            source=self.source,
            document_offset=self._doc_no - 1,           # zero-based join key
            document_number=self._doc_no,
            document_name=document.name if document else None,
            page_number=self._page_no,
            page_in_document=self._page_in_doc,
            byte_offset=getattr(sref, "byte_offset", None),
            byte_count=page.attributes.get("byte_count"),
            record_number=rec_off,
            record_offset=rec_off,
            record_count=page.attributes.get("record_count"),
            fields=extract_fields(page, self.specs),
        ))
