# Supported print streams

`file_type` / spec `type` values and the reader/writer behind each.

| Format | type | Reader | Writer |
|---|---|---|---|
| AFP (MO:DCA) | `afp` | [stream_segment_afp.py](../stream_segment_afp.py) | [writer/afp_writer.py](../writer/afp_writer.py) |
| PDF | `pdf` | [stream_segment_pdf.py](../stream_segment_pdf.py) (PyMuPDF) | [writer/pdf_writer.py](../writer/pdf_writer.py) (ReportLab) |
| PostScript / EPS | `ps`, `postscript` | [stream_segment_ps.py](../stream_segment_ps.py) | [writer/ps_writer.py](../writer/ps_writer.py) |
| PCL5 | `pcl` | [stream_segment_pcl.py](../stream_segment_pcl.py) | [writer/pcl_writer.py](../writer/pcl_writer.py) |
| Xerox Metacode | `metacode` | [stream_segment_metacode.py](../stream_segment_metacode.py) | [writer/metacode_writer.py](../writer/metacode_writer.py) |
| PSML (markup, input only) | `psml` | [markup/](../markup) | — (compose output is another format) |

Any reader can be transformed to any writer (5×5 matrix, all verified).

## Per-format feature notes

### AFP (most complete)
- **Text/PTOCA** with inline/baseline positioning; fonts mapped from **MCF**, decoded
  via code page; **precise run widths** from font metrics.
- **Images/IOCA**: object area placement (OBD/OBP) → window; content captured; bilevel
  G3/G4 decoded to pixels for PDF (the legacy IBM-MMR variant falls back to an
  outline). See [afp/ioca_image.py](../afp/ioca_image.py).
- **Graphics/GOCA**: drawing orders decoded to vector ops (line/box).
- **Barcodes/BCOCA**: symbology + data captured.
- **Overlays (IPO), page segments (IPS), medium maps (IMM)**: parsed and re-emitted.
- **Structured fields**: anything unmodeled is preserved and round-trips.
- **Parallel parsing**: AFP can be parsed across worker threads (`threads=`).

### PDF
Text (with font, size, colour, position) and images via PyMuPDF; ReportLab output
embeds standard fonts and draws text/lines/images/graphics/barcodes.

### PostScript
A restricted interpreter covering the common print subset: paths (moveto/lineto/
curveto/arc), stroke/fill, rectangles, text/fonts/colour, the graphics-state stack,
arithmetic, stack operators, and control flow (if/ifelse/for/repeat). Turing-complete
constructs outside this subset are skipped rather than failing.

### PCL5
Escape-sequence state machine: cursor positioning (dots and decipoints), font height/
weight selection, CR/LF/FF, and text placement. HP-GL/2 and raster are partial.

### Metacode
An order-driven framework parser/writer (length-prefixed records of position/font/text
orders). Because Metacode encodings are printer/JSL-specific, the order map is a
documented, overridable baseline — calibrate it to your variant.

## Internal compression

Separate from compressing the whole output file, a writer can compress *inside* the
print stream. Set `internal-compress="1"` on a step (or `<options internal-compress=
"1"/>` in a spec).

- **PDF** — zlib-compresses content streams (ReportLab `pageCompression`). Typically a
  large reduction for text/vector pages. `0` disables, `1` enables, omit for the
  writer default.

```xml
<step name="transform" internal-compress="1">
  <file name="in.afp" file_type="afp" type="input"/>
  <file name="out.pdf" file_type="pdf" type="output"/>
</step>
```

### Roadmap: custom AFP internal compression
A custom AFP compression method, internal to the file (compressing structured-field
payloads / object data and decompressing on read), is planned. It will be exposed
through the same `internal-compress` option so existing process/spec files gain it
transparently once implemented.
