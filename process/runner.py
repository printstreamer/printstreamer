""" Execute stream.py process steps: analyze, extract, transform, merge.

A step is an XML element with a ``name`` (the process) plus attributes controlling
scope/level/output, ``<file>`` children (inputs/outputs), and optional ``<field>``
(extraction) and enhancement children.
"""

from __future__ import annotations

import logging

import compression
from model.document import Document, StreamDocumentSet
from model.geometry import Rect
from model import visitor
from parse_options import ParseLevel, ParseOptions
from paths import in_data
from process import dump as dump_mod
from process import index as index_mod
from process.index import FieldSpec, IndexSink
from process.stats import StatsSink
from stream_parser import StreamParser
from units import parse_length
from writer.registry import get_writer

logger = logging.getLogger(__name__)

# Default parse thread count; overridden per-step by a threads="" attribute, or
# globally by the CLI --threads flag (stream.py sets this).
DEFAULT_THREADS = 1


# --- step config parsing ---------------------------------------------------

def _attr(step, name, default=None):
    return step.getAttribute(name) if step.hasAttribute(name) else default


def _files(step, type_):
    out = []
    for f in step.getElementsByTagName("file"):
        if (f.getAttribute("type") or "input") == type_:
            out.append((f.getAttribute("name"), f.getAttribute("file_type") or None))
    return out


def _rect(spec: str) -> Rect:
    x, y, w, h = (float(v) for v in spec.split(","))
    return Rect(x, y, w, h)


def parse_options_from(cfg, **overrides) -> ParseOptions:
    """ Build ParseOptions from a StepConfig (spec options, then inline attributes). """
    opts = ParseOptions()
    pages = cfg.opt("pages")
    if pages and "-" in pages:
        lo, hi = pages.split("-", 1)
        opts.start_page = int(lo) if lo else 1
        opts.end_page = int(hi) if hi else None
    if cfg.opt("start_page"):
        opts.start_page = int(cfg.opt("start_page"))
    if cfg.opt("end_page"):
        opts.end_page = int(cfg.opt("end_page"))
    if cfg.opt("max_pages"):
        opts.max_pages = int(cfg.opt("max_pages"))
    level = (cfg.opt("level") or "elements").upper()
    opts.level = ParseLevel[level] if level in ParseLevel.__members__ else ParseLevel.ELEMENTS
    if cfg.opt("record_types"):
        opts.record_types = set(cfg.opt("record_types").split(","))
    font_path = cfg.opt("font-path") or cfg.opt("font_path")
    if font_path:
        opts.font_path = font_path
    jsl = cfg.opt("jsl")
    if jsl:
        opts.jsl_path = jsl
    opts.threads = int(cfg.opt("threads", str(DEFAULT_THREADS)))
    for k, v in overrides.items():
        setattr(opts, k, v)
    return opts


def _load_spec(step):
    """ Load the spec.xml referenced by a step's spec= attribute, if any. """
    path = _attr(step, "spec")
    if not path:
        return None
    from process.spec import load_spec
    return load_spec(path)


class StepConfig:
    """ Resolves a step's configuration, preferring its spec.xml and falling back to
    inline step attributes/children. A spec carries the full process definition. """

    def __init__(self, step):
        self.step = step
        self.spec = _load_spec(step)

    def inputs(self):
        if self.spec and self.spec.inputs:
            files = [(f.name, f.type) for f in self.spec.inputs]
        else:
            files = _files(self.step, "input")
        return [(in_data(name), ftype) for name, ftype in files]

    def outputs(self):
        if self.spec and self.spec.outputs:
            files = [(f.name, f.type) for f in self.spec.outputs]
        else:
            files = _files(self.step, "output")
        return [(in_data(name), ftype) for name, ftype in files]

    def index(self):
        if self.spec and self.spec.index:
            i = self.spec.index
            return {"name": in_data(i.name), "format": i.format,
                    "compress": i.compress, "level": i.level}
        return {"name": in_data(_attr(self.step, "index")),
                "format": _attr(self.step, "index_format", "flat"),
                "compress": _attr(self.step, "compress", "none"),
                "level": int(_attr(self.step, "compress_level", "0"))}

    def opt(self, name, default=None):
        if self.spec and name in self.spec.options:
            return self.spec.options[name]
        return _attr(self.step, name, default)

    @property
    def fields(self):
        return list(self.spec.fields) if self.spec else []

    @property
    def operations(self):
        return list(self.spec.operations) if self.spec else []

    @property
    def boundary(self):
        return self.spec.boundary if self.spec else None

    @property
    def pages_per_document(self):
        return self.spec.pages_per_document if self.spec else None

    @property
    def imposition(self):
        return self.spec.imposition if self.spec else None

    def output_options(self):
        """ Writer settings, e.g. PDF internal (content-stream) compression. """
        val = self.opt("internal-compress")
        if val is None:
            val = self.opt("internal_compress")
        return {"internal_compress": val} if val is not None else {}


def _boundary_spec(step):
    """ A document-identification boundary: a <boundary> child or start-on-* attrs.
    A new document begins on each page that matches the selector. """
    node = step.getElementsByTagName("boundary")
    src = node[0] if node else step
    get = src.getAttribute
    if (node and src.hasAttribute("window")) or step.hasAttribute("start-on-window"):
        spec = get("window") or _attr(step, "start-on-window")
        return FieldSpec("boundary", window=_rect(spec))
    if (node and src.hasAttribute("text")) or step.hasAttribute("start-on-text"):
        return FieldSpec("boundary", text=get("text") or _attr(step, "start-on-text"))
    if (node and src.hasAttribute("hex")) or step.hasAttribute("start-on-hex"):
        return FieldSpec("boundary", hex=get("hex") or _attr(step, "start-on-hex"))
    return None


def field_specs(step) -> list[FieldSpec]:
    specs = []
    for f in step.getElementsByTagName("field"):
        name = f.getAttribute("name")
        if f.hasAttribute("window"):
            specs.append(FieldSpec(name, window=_rect(f.getAttribute("window"))))
        elif f.hasAttribute("text"):
            specs.append(FieldSpec(name, text=f.getAttribute("text")))
        elif f.hasAttribute("hex"):
            specs.append(FieldSpec(name, hex=f.getAttribute("hex")))
    return specs


# --- processes -------------------------------------------------------------

def analyze(step):
    """ Parse and report stats (bounded memory); optionally dump the model. """
    cfg = StepConfig(step)
    dump_path = in_data(cfg.opt("dump"))
    stats = StatsSink()
    retain = bool(dump_path)            # only retain pages if we must dump them
    opts = parse_options_from(cfg, page_sink=stats, retain_pages=retain)
    parser = StreamParser(options=opts)
    for name, ftype in cfg.inputs():
        parser.add_file(parser, name, file_type=ftype, type="input")
        parser.input_files[-1].parse()
    print(stats.report())
    if dump_path:
        dump_mod.dump_model(parser.document_set, dump_path)
        print(f"  Model dumped to: {dump_path}")
    return parser


def extract(step):
    """ Parse and write an index file of extracted data + offsets (bounded memory). """
    cfg = StepConfig(step)
    index = cfg.index()
    fmt = index["format"]
    index_path = index["name"] or in_data("index." + fmt)
    codec, level = index["compress"], index["level"]
    specs = field_specs(step) + cfg.fields
    pages_per_doc = cfg.pages_per_document
    if cfg.opt("pages_per_document"):
        pages_per_doc = int(cfg.opt("pages_per_document"))
    boundary = _boundary_spec(step) or cfg.boundary

    # Lazy model: when no field/boundary needs element content, build the index by
    # structural offset scan only (no element model) — far cheaper on huge streams.
    needs_elements = bool(specs) or (boundary is not None and boundary.window is not None) \
        or (boundary is not None and (boundary.text is not None or boundary.hex is not None))
    extra = {} if (needs_elements or cfg.opt("level")) else {"level": ParseLevel.STRUCTURE}

    all_records = []
    for name, ftype in cfg.inputs():
        sink = IndexSink(name, specs=specs, pages_per_document=pages_per_doc,
                         boundary=boundary)
        opts = parse_options_from(cfg, page_sink=sink, retain_pages=False, **extra)
        parser = StreamParser(options=opts)
        parser.add_file(parser, name, file_type=ftype, type="input")
        parser.input_files[-1].parse()
        all_records.extend(sink.records)

    # Page index (one record per page) and document index (one per document). The doc
    # index needs the page field names to size the page index file for its pi_* offsets.
    page_field_names = index_mod._field_names(all_records)
    page_data = index_mod.serialize(all_records, fmt, kind="page")
    page_out = compression.write_file(index_path, page_data, codec=codec, level=level)
    doc_records = index_mod.document_index_from_pages(all_records)
    doc_path = _doc_index_path(index_path)
    doc_out = compression.write_file(
        doc_path, index_mod.serialize(doc_records, fmt, kind="doc",
                                      page_field_names=page_field_names),
        codec=codec, level=level)
    print(f"  Extracted {len(all_records)} page records -> {page_out}")
    print(f"  Extracted {len(doc_records)} document records -> {doc_out}")
    return all_records


def _doc_index_path(index_path):
    base, dot, ext = index_path.rpartition(".")
    return f"{base}.docs.{ext}" if dot else f"{index_path}.docs"


def transform(step):
    """ Parse inputs into the model and write them to the output format. """
    cfg = StepConfig(step)
    parser = StreamParser(options=parse_options_from(cfg))
    parser.output_options = cfg.output_options()
    for name, ftype in cfg.inputs():
        parser.add_file(parser, name, file_type=ftype, type="input")
    for name, ftype in cfg.outputs():
        parser.add_file(parser, name, file_type=ftype, type="output")
    parser.parse()
    return parser


def merge(step):
    """ Build output(s) from an index file: content/order driven by index records,
    with optional chunking, transform (output format), and enhancement.

    Two paths (see plan §4):
      * **Streaming passthrough** when the output format equals the source format and
        no model-level work is requested (no transform, no spec ops, no chunking, no
        element-level enhancements). Records are copied straight from the input by
        byte span; record-level deletions are applied on the fly. No model is built.
      * **Model path** otherwise: re-parse only the referenced spans into the model,
        apply enhancements/ops, and write via the target writer.
    """
    cfg = StepConfig(step)
    index = cfg.index()
    fmt = index["format"]
    index_path = index["name"] or in_data("index." + fmt)
    records = index_mod.load(compression.read_file(index_path), fmt, kind="page")
    outputs = cfg.outputs()
    if not outputs:
        raise ValueError("merge step requires an output file")
    out_name, out_type = outputs[0]
    chunk_pages = int(cfg.opt("chunk_pages")) if cfg.opt("chunk_pages") else None
    enhancements = _enhancements(step)
    spec_ops = cfg.operations

    # Streaming passthrough: same format, no model work needed. Only whole-record
    # (hex) deletions can be honoured without a model; richer edits use the model.
    hex_deletes = [arg for kind, arg in enhancements if kind == "delete_hex"]
    complex_enh = any(kind != "delete_hex" for kind, _ in enhancements)
    same_format = all(_source_type(r.source) == out_type for r in records) and records
    if same_format and not spec_ops and not complex_enh and not chunk_pages:
        written = _merge_streaming(records, out_name, hex_deletes)
        print(f"  Merged {len(records)} records (streaming passthrough) -> {written[0]}")
        return written

    # Model path: re-parse each source only over the page span the index needs.
    page_index = _build_page_index(records)
    from process import operations
    out_set = StreamDocumentSet()
    cur_doc = None
    cur_docno = None
    for r in records:
        page = page_index.get((r.source, r.page_number))
        if page is None:
            continue
        if r.document_number != cur_docno:
            cur_doc = out_set.add_document(
                Document(name=r.document_name or f"DOC{r.document_number:05d}"))
            cur_docno = r.document_number
        _apply_enhancements(page, enhancements)
        if spec_ops:
            operations.apply_to_page(page, spec_ops, context=r.fields or {})
        cur_doc.add_page(page)

    written = _write_chunks(out_set, out_name, out_type, chunk_pages, cfg.output_options())
    print(f"  Merged {len(records)} records into {len(written)} file(s): {', '.join(written)}")
    return written


# --- merge helpers ---------------------------------------------------------

_EXT_TYPE = {".pdf": "pdf", ".ps": "ps", ".eps": "ps", ".pcl": "pcl",
             ".met": "metacode", ".metacode": "metacode", ".afp": "afp"}


def _source_type(path):
    import os
    return _EXT_TYPE.get(os.path.splitext(path)[1].lower(), "afp")


def _merge_streaming(records, out_name, hex_deletes):
    """ Stream output by copying each page's byte span straight from its source file,
    grouped into documents in index order. Record-level (hex) deletions are applied on
    the fly. The document envelope (BDT/EDT) is emitted around each document's pages.
    No model is built — O(referenced bytes) memory. """
    from writer.afp_writer import _sf, _name8

    sources = {}

    def src(path):
        if path not in sources:
            with open(path, "rb") as fh:
                sources[path] = fh.read()
        return sources[path]

    out = bytearray()
    cur_key = None
    cur_name = None
    open_doc = False
    for r in records:
        key = (r.source, r.document_offset)
        if key != cur_key:
            if open_doc:
                out += _sf("EDT", _name8(cur_name))
            cur_key = key
            cur_name = r.document_name or f"DOC{(r.document_offset or 0) + 1:05d}"
            out += _sf("BDT", _name8(cur_name))
            open_doc = True
        data = src(r.source)
        if r.byte_offset is None or r.byte_count is None:
            continue
        span = data[r.byte_offset:r.byte_offset + r.byte_count]
        if hex_deletes:
            span = _delete_records_by_hex(span, hex_deletes)
        out += span
    if open_doc:
        out += _sf("EDT", _name8(cur_name))
    with open(out_name, "wb") as fh:
        fh.write(out)
    return [out_name]


def _iter_afp_records(data):
    """ Yield (offset, length) for each AFP structured field in ``data``. """
    import struct
    i, n = 0, len(data)
    while i + 6 <= n and data[i:i + 1] == b"\x5a":
        length = struct.unpack(">H", data[i + 1:i + 3])[0] + 1
        if length <= 0 or i + length > n:
            break
        yield i, length
        i += length


def _delete_records_by_hex(span, hex_patterns):
    """ Drop any structured field whose bytes contain one of the hex patterns. """
    pats = [bytes.fromhex(h.replace(" ", "")) for h in hex_patterns if h]
    out = bytearray()
    for off, length in _iter_afp_records(span):
        rec = span[off:off + length]
        if any(p in rec for p in pats):
            continue
        out += rec
    return bytes(out)


def _enhancements(step):
    ops = []
    for d in step.getElementsByTagName("delete"):
        if d.hasAttribute("window"):
            ops.append(("delete_window", _rect(d.getAttribute("window"))))
        elif d.hasAttribute("hex"):
            ops.append(("delete_hex", d.getAttribute("hex")))
        elif d.hasAttribute("text"):
            ops.append(("delete_text", d.getAttribute("text")))
    return ops


def _apply_enhancements(page, ops):
    for kind, arg in ops:
        if kind == "delete_window":
            visitor.remove(visitor.select_in_window(page, arg, contained=False))
        elif kind == "delete_hex":
            visitor.remove(visitor.select_by_hex(page, arg))
        elif kind == "delete_text":
            visitor.remove(visitor.select_by_text(page, arg))


def _write_chunks(out_set, out_name, out_type, chunk_pages, output_options=None):
    writer = get_writer(out_type, output_options)
    if not chunk_pages:
        writer.write(out_set, out_name)
        return [out_name]
    written = []
    base, _, ext = out_name.rpartition(".")
    pages = out_set.all_pages()
    for i in range(0, len(pages), chunk_pages):
        chunk = StreamDocumentSet()
        doc = chunk.add_document(Document(name=f"chunk{i // chunk_pages + 1:03d}"))
        for p in pages[i:i + chunk_pages]:
            doc.add_page(p)
        name = f"{base}_{i // chunk_pages + 1:03d}.{ext}" if ext else f"{out_name}_{i // chunk_pages + 1:03d}"
        writer.write(chunk, name)
        written.append(name)
    return written


def compose(step):
    """ Generate a print stream and its indexes from a PSML markup input file. """
    from markup.compose import compose as compose_markup
    cfg = StepConfig(step)
    inputs = cfg.inputs()
    if not inputs:
        raise ValueError("compose step requires a markup input file")
    markup_path = inputs[0][0]
    outputs = cfg.outputs()
    index = cfg.index()
    doc_set = compose_markup(markup_path, outputs, index_path=index["name"],
                             index_format=index["format"], compress=index["compress"],
                             compress_level=index["level"],
                             output_options=cfg.output_options())
    print(f"  Composed {doc_set.document_count} document(s), {doc_set.page_count} page(s)"
          f" -> {', '.join(n for n, _ in outputs)}")
    return doc_set


def _page_size(cfg):
    from process.imposition import resolve_page_size
    w = parse_length(cfg.opt("page-width")) if cfg.opt("page-width") else None
    h = parse_length(cfg.opt("page-height")) if cfg.opt("page-height") else None
    return resolve_page_size(cfg.opt("page-size") or "letter", w, h)


def nup(step):
    """ N-up imposition. With an <imposition> spec, honour full per-cell layout
    (page references n/n-1, rotation, scale, alignment); otherwise flow rows*cols
    source pages per sheet using inline attributes. """
    from process.imposition import impose, impose_spec
    cfg = StepConfig(step)
    parser = StreamParser(options=parse_options_from(cfg))
    for name, ftype in cfg.inputs():
        parser.add_file(parser, name, file_type=ftype, type="input")
        parser.input_files[-1].parse()
    imp = cfg.imposition
    if imp is not None:
        out_set = impose_spec(parser.document_set, imp)
        desc = f"{imp.rows}x{imp.cols}" + (" (custom cells)" if imp.cells else "")
    else:
        rows = int(cfg.opt("rows", "2"))
        cols = int(cfg.opt("cols", "2"))
        out_set = impose(parser.document_set, rows, cols, _page_size(cfg),
                         margin_top=parse_length(cfg.opt("margin-top", "0")),
                         margin_left=parse_length(cfg.opt("margin-left", "0")),
                         h_gap=parse_length(cfg.opt("h-gap", "0")),
                         v_gap=parse_length(cfg.opt("v-gap", "0")),
                         rotate=int(cfg.opt("rotate", "0")))
        desc = f"{rows}x{cols}"
    for name, ftype in cfg.outputs():
        get_writer(ftype, cfg.output_options()).write(out_set, name)
    print(f"  Imposed {parser.document_set.page_count} page(s) {desc} -> "
          f"{out_set.page_count} sheet(s)")
    return out_set


def reorder(step):
    """ Reorder pages of an input into a new output by an explicit order list. """
    cfg = StepConfig(step)
    parser = StreamParser(options=parse_options_from(cfg))
    inputs = cfg.inputs()
    parser.add_file(parser, inputs[0][0], file_type=inputs[0][1], type="input")
    parser.input_files[-1].parse()
    pages = {p.number: p for _, p in parser.document_set.iter_pages()}
    order = [int(n) for n in (cfg.opt("order") or "").split(",") if n.strip()]
    out_set = StreamDocumentSet()
    doc = out_set.add_document(Document(name="reordered"))
    for n in order or sorted(pages):
        if n in pages:
            doc.add_page(pages[n])
    outputs = cfg.outputs()
    for name, ftype in outputs:
        get_writer(ftype, cfg.output_options()).write(out_set, name)
    print(f"  Reordered {len(order)} page(s) -> {', '.join(n for n, _ in outputs)}")
    return out_set


def split(step):
    """ Split an index into multiple outputs, one per document (or key field). """
    cfg = StepConfig(step)
    index = cfg.index()
    fmt = index["format"]
    records = index_mod.load(compression.read_file(index["name"]), fmt, kind="page")
    key_field = cfg.opt("key")
    pattern = (cfg.outputs()[0][0] if cfg.outputs() else None) or in_data(cfg.opt("output", "split_{key}.pdf"))
    out_type = (cfg.outputs()[0][1] if cfg.outputs() else None) or cfg.opt("output_type", "pdf")
    page_index = _build_page_index(records)
    groups = {}
    order = []
    for r in records:
        key = (r.fields or {}).get(key_field) if key_field else r.document_number
        if key not in groups:
            groups[key] = []
            order.append(key)
        groups[key].append(r)
    written = []
    for key in order:
        out_set = StreamDocumentSet()
        doc = out_set.add_document(Document(name=str(key)))
        for r in groups[key]:
            page = page_index.get((r.source, r.page_number))
            if page is not None:
                doc.add_page(page)
        name = pattern.replace("{key}", str(key))
        get_writer(out_type, cfg.output_options()).write(out_set, name)
        written.append(name)
    print(f"  Split into {len(written)} file(s): {', '.join(written)}")
    return written


def _build_page_index(records):
    page_index = {}
    by_source = {}
    for r in records:
        by_source.setdefault(r.source, []).append(r)
    for source, recs in by_source.items():
        nums = [r.page_number for r in recs]
        parser = StreamParser(options=ParseOptions(start_page=min(nums), end_page=max(nums)))
        parser.add_file(parser, source, file_type=_source_type(source), type="input")
        parser.input_files[-1].parse()
        for _doc, page in parser.document_set.iter_pages():
            page_index[(source, page.number)] = page
    return page_index


def edit(step):
    """ Parse input(s), apply declarative edit operations, write output(s). """
    from process import operations
    cfg = StepConfig(step)
    parser = StreamParser(options=parse_options_from(cfg))
    parser.output_options = cfg.output_options()
    for name, ftype in cfg.inputs():
        parser.add_file(parser, name, file_type=ftype, type="input")
    for name, ftype in cfg.outputs():
        parser.add_file(parser, name, file_type=ftype, type="output")
    for file in parser.input_files:
        file.parse()
    ops = operations.parse_operations(step) + cfg.operations
    extracted = operations.apply_operations(parser.document_set, ops)
    parser.write_outputs()
    if extracted and cfg.opt("extract_to"):
        import json
        with open(in_data(cfg.opt("extract_to")), "w", encoding="utf-8") as fh:
            json.dump(extracted, fh, indent=2)
    counts = {}
    for op in ops:
        counts[op["verb"]] = counts.get(op["verb"], 0) + 1
    print(f"  Applied edits {counts}; extracted {len(extracted)} value(s)")
    return parser


def labels(step):
    """ Generate n-up label sheets from an index file and a PSML label template. """
    from labels.generate import generate_labels
    cfg = StepConfig(step)
    index = cfg.index()
    index_path = index["name"]
    if not index_path:
        raise ValueError("labels step requires an index file with the label data")
    records = index_mod.load(compression.read_file(index_path), index["format"], kind="page")
    stock = cfg.opt("stock", "avery-5160")
    template_node = step.getElementsByTagName("label")
    if template_node:
        template = _inner_xml(template_node[0])
    elif cfg.opt("template"):
        with open(in_data(cfg.opt("template")), "r", encoding="utf-8") as fh:
            template = fh.read()
    else:
        raise ValueError("labels step requires a <label> template or template= file")
    doc_set = generate_labels(records, template, stock)
    outputs = cfg.outputs()
    for name, ftype in outputs:
        get_writer(ftype, cfg.output_options()).write(doc_set, name)
    print(f"  Generated {doc_set.page_count} label sheet(s) on {stock}"
          f" -> {', '.join(n for n, _ in outputs)}")
    return doc_set


def _inner_xml(node):
    return "".join(c.toxml() for c in node.childNodes)


PROCESSES = {
    "analyze": analyze,
    "extract": extract,
    "transform": transform,
    "merge": merge,
    "compose": compose,
    "labels": labels,
    "nup": nup,
    "reorder": reorder,
    "split": split,
    "edit": edit,
}


_METACODE_EXTS = (".met", ".metacode")


def _require_jsl_for_metacode(step):
    """ Metacode is meaningless without its JSL (page geometry, fonts, DJDE prefix), so
    a process/spec step that reads a Metacode input must name one via ``jsl=``. """
    import os
    cfg = StepConfig(step)
    has_metacode = any(
        (ftype == "metacode") or os.path.splitext(name)[1].lower() in _METACODE_EXTS
        for name, ftype in cfg.inputs())
    if has_metacode and not cfg.opt("jsl"):
        raise ValueError(
            "Metacode processing requires a JSL: add jsl=\"config/metacode.jsl\" "
            "(or your own JSL) to the step or its spec.")


def run_step(step):
    name = step.getAttribute("name")
    handler = PROCESSES.get(name)
    if handler is None:
        logger.warning("No handler for process step %r; skipping", name)
        return None
    _require_jsl_for_metacode(step)
    return handler(step)
