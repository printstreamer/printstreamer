# PSML — composing print streams from markup

PSML (PrintStream Markup Language) is a custom XML vocabulary inspired by XSL-FO for
**generating** original print streams. The `compose` process loads PSML into the model
and writes it to any format(s), plus page/document indexes.

```xml
<process>
  <step name="compose" spec="letter_compose.xml"/>
</process>
```

…where the spec provides the input PSML and the outputs:

```xml
<spec process="compose">
  <inputs>  <file name="letter.psml" type="psml"/> </inputs>
  <outputs> <file name="letter.pdf" type="pdf"/>
            <file name="letter.afp" type="afp"/> </outputs>
  <index name="letter.idx" format="json"/>
</spec>
```

## What PSML does

- **Page masters** with margins, multiple **columns**, and **header/footer** regions.
- **Automatic text flow**: wrapping, column and page breaks, justified text, indents.
- **Widow/orphan** control and **keep-together** / **keep-with-next**.
- **Fields**: `<page-number/>`, `<page-count/>`.
- **Block primitives**: image, line, rectangle, ellipse, polygon, path, barcode, and
  **tables** (column widths, colspan, borders, multi-line cells).
- **Styles** (`<style>`) and per-element overrides; all measurements in points.
- **AFP-native** constructs: `<overlay>`, `<page-segment>`, `<medium-map>`,
  `<object-container>`, `<structured-field>` (emitted by the AFP writer).
- **Bookmarks** → PDF outline.

## Example

A two-column letter with header/footer, page-of-count, justified body, a rule, a
rectangle, and a barcode: [examples/letter.psml](../examples/letter.psml).

## Full grammar

Every tag and parameter (with implemented/partial/planned status) is documented in
[markup/SCHEMA.md](../markup/SCHEMA.md). The loader and flow engine are in
[markup/loader.py](../markup/loader.py) and [markup/layout.py](../markup/layout.py).

## Relationship to specs

PSML composes an **original** stream from markup. A **spec** enhances an **existing**
stream — but both share the same element vocabulary (text, barcodes, lines, rectangles,
images, overlays), so what you can compose you can also add as an enhancement.
