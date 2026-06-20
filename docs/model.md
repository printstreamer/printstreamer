# The normalized memory model

Every format is parsed into one model ([model/](../model)). All geometry is in printer
points (1/72") with a top-left origin and y increasing downward.

```
StreamDocumentSet              # the whole parsed stream
└─ Document                    # a logical document (name, index_tags, resource_library)
   └─ Page                     # size, orientation, attributes, index_tags, source_ref
      └─ Element               # one of the typed elements below
   ResourceLibrary             # fonts, images, overlays, ... (ref-counted)
```

## Elements ([model/element.py](../model/element.py))

Common to every element: `kind`, `bbox` (the window: x, y, width, height),
`transform`, `z_order`, `attributes`, `source_ref` (originating record + byte offset),
and `raw` (preserved source bytes, used for hex selection).

| Element | Key fields |
|---|---|
| `TextElement` | `text`, `position`, `font_ref`, `font_size`, `color`, `orientation`, `raw_text_bytes`; `attributes["char_advances"]` holds per-character widths (points) for precise sub-run window extraction |
| `LineElement` | `start`, `end`, `weight`, `color` |
| `ImageElement` | `resource_ref` or inline `data`, `encoding`, `dpi`, `colorspace` |
| `GraphicElement` | `ops` (normalized `DrawOp`s: box/ellipse/polyline/path), `stroke`, `fill` |
| `BarcodeElement` | `symbology`, `data`, `params`, `color` |
| `FormElement` / `OverlayElement` | `resource_ref`, placement |
| `ContainerElement` | `children`, `preserved_type` (groups, or preserved-but-unmodeled constructs) |

## Resources ([model/resource.py](../model/resource.py))

`FontResource` (coded font ↔ code page, `size`, `encoding_map` code-point→Unicode, and
`metrics` code-point→advance in 1/1000 em — resolved from embedded FOCA, an external font
library, or the mapped base font; see [afp/fonts.py](../afp/fonts.py)), `ImageResource`,
`OverlayResource`, `PageSegmentResource`, `ColorTableResource`, and `RawResource`
(unknown resources kept byte-for-byte). The `ResourceLibrary` deduplicates by name and
ref-counts so writers emit only what is used.

## Geometry ([model/geometry.py](../model/geometry.py))

`Point`, `Rect` (the window shape used for selection), `Matrix` (affine, for
imposition), and `Color` (rgb / cmyk / gray / named).

## Selection & editing ([model/visitor.py](../model/visitor.py))

The format-agnostic engine behind extraction, deletion, and identification:

- `select_by_text(scope, pattern, regex=False)` — match a TextElement's text
- `select_by_hex(scope, hex)` — match an element's source/encoded bytes
- `select_in_window(scope, Rect)` — elements whose bbox falls in a window
- `text_in_window(element, Rect)` — clip a text run to exactly the in-window characters
  (using `char_advances`)
- `iter_elements`, `remove`, `replace`, `add`

A *scope* is a `Page`, `Document`, `StreamDocumentSet`, or list thereof.

## Why a normalized model

- **Transform** is "parse to model, write from model" — any reader to any writer.
- **Edit/identify/extract** operate on the model, so they work across all formats.
- **Fidelity:** unknown constructs are preserved (never dropped), and every element
  records its byte offset so the index can locate it exactly.

Dump the model for inspection with the `analyze` process (`dump="model.json"`) — see
[process/dump.py](../process/dump.py).
