# Processes

Each `<step name="...">` runs one process. Options come from the step's spec
(preferred) or inline attributes; see [process-utility.md](process-utility.md) for
resolution rules and [spec.md](spec.md) for the spec grammar. All examples are in
[examples/](../examples).

| Process | Purpose |
|---|---|
| [transform](#transform) | Convert one format to another |
| [analyze](#analyze) | Parse, report stats, optionally dump the model |
| [extract](#extract) | Identify documents and write index files of extracted data |
| [merge](#merge) | Rebuild output(s) from an index, in record order, with enhancement |
| [split](#split) | Split an index into multiple outputs by document or key field |
| [reorder](#reorder) | Reorder pages by an explicit list |
| [nup](#nup) | N-up imposition (flow or full per-cell layout) |
| [edit](#edit) | Extract / delete / modify / add elements in place |
| [compose](#compose) | Generate a stream + indexes from PSML markup |
| [labels](#labels) | Generate n-up label sheets from an index |

## transform
Parse inputs and write them to the output format(s). Inputs/outputs from spec or inline
`<file>`. Common options apply (`pages`, `level`, `threads`, …).
Example: [transform_process.xml](../examples/transform_process.xml).

## analyze
Report documents/pages/elements/resources; with `dump="model.json"` also serialize the
model. Bounded memory unless dumping. Example:
[analyze_process.xml](../examples/analyze_process.xml).

## extract
Identify documents and write a **page index** and **document index**. Identification and
fields come from the spec (`<identify>`, `<fields>`) or inline. Index target from
`<index>` (name/format/compress/level). Index formats: `text`, `csv`, `tab`, `xml`,
`json`. Example: [index_merge_process.xml](../examples/index_merge_process.xml) +
[statement_spec.xml](../examples/statement_spec.xml).

## merge
Read an index and assemble output(s) in **index-record order**. Pages may be enhanced
per the spec's `<enhancements>` (with `{field}` substitution from each index record),
transformed to a different output format, and **chunked** (`chunk_pages`).

## split
Read an index and write one output per **document** (default) or per **key field**
(`key="account"`). Output name pattern uses `{key}`.

## reorder
Reorder a single input's pages by `order="3,1,2,..."` into a new output.

## nup
N-up imposition. Two modes:
- **Flow** (inline attributes): `rows`, `cols`, `page-size`/`page-width`/`page-height`,
  `margin-top`, `margin-left`, `h-gap`, `v-gap`, `rotate`. Fills `rows*cols` pages per
  sheet in order. Example: [nup_process.xml](../examples/nup_process.xml).
- **Full layout** (spec `<imposition>` with `<cell>` children): total control of which
  input page lands in each cell — by absolute number or by `n`, `n-1`, … — plus per-cell
  `rotate`, `scale`, `halign`, `valign`, and `group-size`. Example:
  [booklet_spec.xml](../examples/booklet_spec.xml) +
  [booklet_process.xml](../examples/booklet_process.xml).

## edit
Apply operations to a parsed stream and write it out: `<extract>`, `<delete>`,
`<modify>`, `<add>` (inline and/or from a spec). `extract_to="file.json"` saves
captured values. Example: [edit_process.xml](../examples/edit_process.xml).

## compose
Generate a print stream (and page/document indexes) from a **PSML** markup file. One
model renders to several outputs at once (e.g. PDF + AFP). Example:
[compose_process.xml](../examples/compose_process.xml). See [markup.md](markup.md).

## labels
Generate n-up label sheets from an index file: each record fills one label of a stock
template (e.g. `avery-5160`) using a `<label>` PSML fragment with `{field}`
placeholders. Example: [labels_process.xml](../examples/labels_process.xml).
