# The process utility

`stream.py` runs a **process file**: an XML list of steps executed in order.

```bash
python stream.py <process.xml> [--start STEP] [--stop STEP] [--threads N] [--log LEVEL]
```

- `--start` / `--stop` — run only a slice of the steps (by step name).
- `--threads` — default parse worker count for AFP (a step may override).
- `--log` — `DEBUG | INFO | WARNING | ERROR` (default `WARNING`).

## Process files

A process file lists steps. Each step has a `name` (the process to run) and either
points at a **spec** or carries inline configuration:

```xml
<process>
  <step name="extract" spec="extract_spec.xml"/>
  <step name="merge"   spec="merge_spec.xml"/>
</process>
```

The recommended style is one spec per step (see [spec.md](spec.md)); the spec carries
the full definition — input/output/index files, identification, fields, enhancements,
and imposition. Inline attributes and child elements still work and **override** the
spec, which is handy for quick one-offs:

```xml
<process>
  <step name="transform">
    <file name="in.afp" file_type="afp" type="input"/>
    <file name="out.pdf" file_type="pdf" type="output"/>
  </step>
</process>
```

## Resolution order

For every option, a step resolves it as: **spec value → inline step value → default.**
Files come from the spec's `<inputs>`/`<outputs>` when present, otherwise from inline
`<file type="input|output">` children.

## Common options

These apply to most parsing processes (set as spec `<options .../>` attributes or
inline step attributes):

| Option | Meaning |
|---|---|
| `pages="A-B"`, `start_page`, `end_page`, `max_pages` | parse only part of the input |
| `level="structure\|elements\|full"` | parse depth (cost control) |
| `record_types="BPG,PTX,..."` | parse only these AFP record types |
| `threads="N"` | parallel AFP parse workers |

See [processes.md](processes.md) for each process's options and examples.
