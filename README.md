# PrintStreamer

A universal print-stream engine. It parses AFP, PDF, PostScript, PCL, and Xerox
Metacode down to the element level, stores everything in one normalized in-memory
model, and lets you analyze, extract, identify, edit, transform, impose, and compose
print streams — driven by simple XML process files.

```
 readers                normalized model                writers
 ┌───────────┐        ┌────────────────────┐         ┌───────────┐
 │ afp  pdf  │        │ StreamDocumentSet   │         │ afp  pdf  │
 │ ps   pcl  │ ─────▶ │  Document ▸ Page ▸  │ ──────▶ │ ps   pcl  │
 │ metacode  │        │  Element ▸ Resource │         │ metacode  │
 └───────────┘        └────────────────────┘         └───────────┘
        ▲                    │        ▲                     │
   PSML markup ──────────────┘        └── spec.xml ─────────┘
   (compose)                              (identify / extract / enhance)
```

Everything operates on the model; parsers and writers are the only format-aware code.
Add a format by writing a reader + writer pair — no feature code changes.

## Quick start

```bash
pip install -r requirements.txt          # pillow, pymupdf, reportlab
pip install pytest                        # for the test suite
python stream.py examples/transform_process.xml
python -m pytest
```

A process is an XML file of steps; run it with `python stream.py <process.xml>`:

```xml
<process>
  <step name="transform">
    <file name="in.afp" file_type="afp" type="input"/>
    <file name="out.pdf" file_type="pdf" type="output"/>
  </step>
</process>
```

## Sample data

`data/` is the default working directory for all inputs, outputs, and index files.
Process files reference inputs/outputs by bare filename (e.g. `name="test_afp.afp"`),
and the runner resolves those against `data/` automatically — absolute paths and
explicit relative paths (e.g. `examples/letter.psml`) are left untouched. Override the
location with the `PRINTSTREAMER_DATA_DIR` environment variable.

To populate it with a representative corpus across every supported engine:

```bash
python scripts/sample_printstream_file_collection.py [--data-dir DIR]
```

This downloads real public-domain PDF, PostScript, PCL, and AFP samples, synthesizes a
Xerox Metacode sample, and writes `data/printstream_test_report.json` — a manifest that
classifies each file by magic-byte signature and size tier. The `data/` directory is
git-ignored, so collected and generated files are never committed.

Metacode/LCDS carries no self-describing geometry, so it is **JSL-driven**: a Job Source
Library in [config/](config) supplies the page size, fonts, and DJDE prefix. Any
process/spec step that reads a Metacode input must name one, e.g.
`<step name="transform" jsl="config/metacode.jsl">` (see
[examples/metacode_process.xml](examples/metacode_process.xml)).

## Documentation

| Document | Contents |
|---|---|
| [docs/architecture.md](docs/architecture.md) | Component map and data flow |
| [docs/process-utility.md](docs/process-utility.md) | `stream.py`, process-file structure, global options |
| [docs/processes.md](docs/processes.md) | Every process and all its options, with examples |
| [docs/model.md](docs/model.md) | The normalized memory model (documents, pages, elements, resources) |
| [docs/printstreams.md](docs/printstreams.md) | Supported formats and per-format feature matrix |
| [docs/spec.md](docs/spec.md) | `spec.xml`: identification, extraction fields, enhancements |
| [docs/index-format.md](docs/index-format.md) | Page/document index record layouts (flat + JSON) |
| [docs/markup.md](docs/markup.md) | PSML composition (overview; full grammar in [markup/SCHEMA.md](markup/SCHEMA.md)) |
| [docs/barcodes.md](docs/barcodes.md) | Supported barcode symbologies and OMR |

## Examples

Runnable process/spec/markup files are in [examples/](examples):

| File | Shows |
|---|---|
| [transform_process.xml](examples/transform_process.xml) | Format → format conversion |
| [analyze_process.xml](examples/analyze_process.xml) | Stats + model dump, with parse scope/level/threads |
| [index_merge_process.xml](examples/index_merge_process.xml) | Extract → index → merge, spec-driven |
| [statement_spec.xml](examples/statement_spec.xml) | A full spec: identify, fields, enhancements |
| [nup_process.xml](examples/nup_process.xml) | N-up imposition with page rotation |
| [booklet_process.xml](examples/booklet_process.xml) + [booklet_spec.xml](examples/booklet_spec.xml) | Fully spec-driven step; per-cell imposition with `n`/`n-1` page refs |
| [edit_process.xml](examples/edit_process.xml) | Inline extract/delete/modify/add |
| [labels_process.xml](examples/labels_process.xml) | Index-driven label sheets |
| [compose_process.xml](examples/compose_process.xml) | Generate a stream + indexes from PSML |
| [letter.psml](examples/letter.psml) | PSML markup document |

## At a glance

- **Processes:** `transform`, `analyze`, `extract`, `merge`, `split`, `reorder`,
  `nup`, `edit`, `compose`, `labels`.
- **Readers:** AFP (text with colour/orientation, fonts with per-character metrics, IOCA
  images, GOCA/BCOCA objects, overlays, page segments, tags, placement; every triplet
  decoded), PDF, PostScript, PCL, Metacode.
- **Writers:** PDF, AFP, PostScript, PCL, Metacode (fonts converted to each target).
- **Indexes:** flat fixed-length records (default) or JSON; an index-driven AFP→AFP
  `merge` streams pages straight from the input — see [docs/index-format.md](docs/index-format.md).
- **Selection:** by text, by hex id, or by window `(x, y, width, height)` — windows clip
  to exact characters using per-character widths.
- **Barcodes:** Code 39 (3of9), Code 128 (incl. 128C), Code 93, QR, DataMatrix,
  USPS 4-State, and OMR marks.
- **Cost controls:** page ranges, parse levels, record/resource/triplet/object filters,
  lazy model building, multi-threaded AFP parsing.
- **Fonts:** per-character metrics from embedded FOCA, an external font library
  (`font-path`), or a base-font fallback; source fonts converted to each target format.
- **Compression:** flat indexes are uncompressed (default); optional 0–10 index-file
  compression, plus PDF internal (content-stream) compression via `internal-compress`
  (custom AFP internal compression is on the roadmap).

## Development

```bash
python -m pytest          # 82 tests
python -m compileall .     # warning-free
```

To add a print-stream format: implement a reader segment (build the model) and a
writer (`write(document_set, path)`), then register them in
[stream_file.py](stream_file.py) and [writer/registry.py](writer/registry.py).
