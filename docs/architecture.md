# Architecture

PrintStreamer is layered so that format knowledge lives only in readers and writers;
every other capability operates on one normalized model.

```
                ┌──────────────────────── stream.py ────────────────────────┐
                │  parse <process.xml> -> run each <step> via process.runner │
                └────────────────────────────┬───────────────────────────────┘
                                              │
   readers (parse)                     process layer                    writers
 ┌──────────────────┐         ┌──────────────────────────────┐   ┌──────────────────┐
 │ stream_segment_* │         │ identify / index   (index)   │   │ writer/*_writer  │
 │  afp pdf ps pcl  │──model─▶ │ extract fields     (operations)│─▶│ afp pdf ps pcl   │
 │  metacode        │         │ edit add/del/mod   (operations)│   │ metacode         │
 └──────────────────┘         │ merge/split/reorder (merge)   │   └──────────────────┘
        ▲                      │ n-up imposition    (imposition)│           ▲
        │                      │ labels             (labels)   │           │
   markup/ (PSML)              │ compose            (markup)   │     writer/registry
   loader+layout ─────model───▶└──────────────────────────────┘
```

## Layers

- **Process driver** — [stream.py](../stream.py) parses a process XML file and runs
  each `<step>` through [process/runner.py](../process/runner.py), which maps a step
  name to a handler.
- **Readers** — `stream_segment_{afp,pdf,ps,pcl,metacode}.py` parse a source into the
  model. AFP parses by byte range (and in parallel); the rest parse by page.
  Format-specific record/order logic lives in [afp/](../afp), [postscript/](../postscript),
  [pcl/](../pcl), and [metacode/](../metacode).
- **Model** — [model/](../model) defines the normalized document model and the
  selection/edit visitor. See [model.md](model.md).
- **Process layer** — [process/](../process): `index` (identification + index files),
  `operations` (extract/delete/modify/add), `merge` (index-driven merge/split),
  `imposition` (n-up + rotation), `parallel` (threaded AFP), `stats`, `dump`, `spec`.
- **Composition** — [markup/](../markup) turns PSML into the model (loader + layout
  engine). See [markup.md](markup.md).
- **Writers** — [writer/](../writer) render the model to each format; selected via
  [writer/registry.py](../writer/registry.py).

## Key design rules

1. **One model, many formats.** Readers build a `StreamDocumentSet`; writers consume
   it. Nothing in the process/markup layers is format-aware.
2. **Points everywhere.** All geometry is in printer points (1/72") with a top-left
   origin; readers/writers convert at the boundary ([units.py](../units.py)).
3. **Preserve, don't drop.** Unmodeled constructs are kept (`RawResource`,
   `ContainerElement`) so transforms and merges never lose data.
4. **Bounded memory.** A `PageSink` lets pages stream to a consumer and be released;
   `merge` re-reads only the page spans the index references.

## Adding a format

1. Write `stream_segment_<fmt>.py` that builds model pages, and register it in
   [stream_file.py](../stream_file.py)'s `SEGMENT_CLASSES`.
2. Write `writer/<fmt>_writer.py` with `write(document_set, path)`, and register it in
   [writer/registry.py](../writer/registry.py).

No process, markup, or model code needs to change.
