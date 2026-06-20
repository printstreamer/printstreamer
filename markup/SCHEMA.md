# PSML — PrintStream Markup Language

A custom XML vocabulary inspired by XSL-FO for generating print streams. It keeps FO's
formatting model (automatic text flow, pagination, keeps, widow/orphan control) and adds
AFP-native concepts, while mapping directly onto the generic model so it renders to PDF or
AFP unchanged.

**Unit of measure: printer points (1/72").** Lengths accept a bare number (points) or a
suffix: `pt`, `px`, `in`, `mm`, `cm`, `pc`. Colours accept `#rrggbb`, `rgb(r,g,b)`,
`cmyk(c,m,y,k)`, or a named colour.

Status legend: ✅ implemented · ◐ partial · ○ planned.

## Structure

### `<document>` ✅
Root element. `units` (informational; points are canonical).

### `<master-page>` ✅
A page template referenced by `<page-sequence master="…">`.
| attribute | meaning |
|---|---|
| `name` | template id |
| `page-width`, `page-height` | page size |
| `margin`, `margin-top/right/bottom/left` | margins (shorthand + per-side) |
| `columns` | column count for the body region |
| `column-gap` | gap between columns |
| `header-extent`, `footer-extent` | height of the header/footer regions |
Children: `<header>` ✅, `<footer>` ✅ (block content drawn on every page).

### `<page-sequence>` ✅
A run of content flowed through pages built from a master.
`master` (template id), `name` (document name → model `Document.name`).
Children: `<flow>` ✅, `<bookmark>` ◐.

### `<flow>` ✅
Container of block-level content that is flowed and paginated automatically.

### `<style>` ✅
A named, reusable property bag. `name` + any block/inline properties; referenced by
`style="…"`. Inline attributes override the named style; text properties inherit to children.

## Block content

### `<paragraph>` / `<block>` / `<heading>` ✅
A flowed text block.
| attribute | meaning |
|---|---|
| `font`/`font-family`, `size`/`font-size`, `weight`, `style`(italic), `color` | text style (inherited) |
| `text-align` | `left` ✅ · `right` ✅ · `center` ✅ · `justify` ✅ |
| `line-height` | leading (default size × 1.2) |
| `space-before`, `space-after` | vertical spacing |
| `start-indent`, `end-indent`, `first-line-indent` | indents |
| `widows`, `orphans` | min lines kept after/before a break (default 2) ✅ |
| `keep-together` | hold the block intact if it fits a fresh frame ✅ |
| `keep-with-next` | reserve space so a heading isn't stranded at a column foot ✅ |

### `<span>` ✅
Inline run inside a paragraph; same text properties as paragraph. Nestable.

### `<table>` / `<row>` / `<cell>` ◐
Simple fixed grid: equal columns across the frame; `<row height="…">`; cells carry text
properties. Spanning, borders, and cell flow are ○.

## Graphics (points; absolute `x`/`y` unless flowed)

| element | status | attributes |
|---|---|---|
| `<image>` | ✅ | `src`, `x`, `y`, `width`, `height` (flows at the cursor if no `x`/`y`) |
| `<line>` | ✅ | `x1`,`y1`,`x2`,`y2`, `width`, `color` |
| `<rectangle>` | ✅ | `x`,`y`,`width`,`height`, `color`(stroke), `fill` |
| `<ellipse>` | ✅ | `x`,`y`,`width`,`height`, `color`, `fill` |
| `<polygon>` | ✅ | `points="x,y x,y …"`, `color`, `fill` |
| `<path>` | ◐ | `points="…"`, `color`, `fill` (line segments; full path ops ○) |
| `<barcode>` | ✅ | `x`,`y`,`width`,`height`, `symbology`, `data`, `color` |

## Page furniture

| element | status | notes |
|---|---|---|
| `<header>`, `<footer>` | ✅ | block content drawn in the master's margin regions on every page |
| `<page-number>` | ✅ | resolved to the current page number during layout |
| `<page-count>` | ✅ | resolved to the total in a post-pass |
| `<page-break>` | ✅ | force a new page |
| `<bookmark>` | ✅ | recorded as an index tag and emitted as a PDF outline entry |
| `<footnote>`, `<annotation>`, `<layer>` | ◐ | parsed and recorded as page index tags; rendering ○ |
| `<font>`, `<color>` | ◐ | resource declarations; collected, used as named references |

## AFP-specific (declared in PSML, emitted by the AFP writer)

| element | status | notes |
|---|---|---|
| `<overlay>` | ○ | named overlay resource + placement |
| `<medium-map>` | ○ | medium map / invoke medium map |
| `<page-segment>` | ○ | page segment resource + include |
| `<object-container>` | ○ | object container resource |
| `<structured-field>` | ○ | raw structured-field passthrough |

These map onto the generic model's `OverlayResource` / `PageSegmentResource` / `RawResource`
and are emitted by the AFP writer; they are accepted by the loader today and rendered as the
roadmap fills them in.

## Example

See `examples/letter.psml`: a two-column Letter page with header/footer, page-of-count,
styled headings, justified body text with widow/orphan control, a rule, a rectangle, and a
barcode — composed to PDF or AFP via the `compose` process.
