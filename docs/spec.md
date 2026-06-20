# Specifications (spec.xml)

A **spec** is the single, reusable definition of everything a process does. A process
file points a step at a spec; the spec carries the files, identification, fields,
enhancements, and imposition. Loaded by [process/spec.py](../process/spec.py).

```xml
<process>
  <step name="extract" spec="my_extract.xml"/>
  <step name="merge"   spec="my_merge.xml"/>
</process>
```

## Top-level structure

```xml
<spec process="extract">
  <inputs>  <file name="in.afp" type="afp"/>  </inputs>
  <outputs> <file name="out.pdf" type="pdf"/> </outputs>
  <index name="out.idx" format="json" compress="gzip" level="6"/>
  <options pages="1-1000" level="elements" threads="4" chunk_pages="500"/>

  <identify by="text" value="STATEMENT"/>
  <fields> ... </fields>
  <enhancements> ... </enhancements>
  <imposition> ... </imposition>
</spec>
```

All sections are optional; include what the process needs. Inline step attributes
override the spec.

### Files
- `<inputs>` / `<outputs>` — `<file name="..." type="afp|pdf|ps|pcl|metacode|psml"/>`.
- `<index>` — `name`, `format` (`text|csv|tab|xml|json`), `compress`
  (`none|gzip|zlib`), `level` (0–10). Used as the output index (extract/compose) or the
  input index (merge/split).

### Options
`<options ... />` mirrors the common parse options: `pages`, `start_page`, `end_page`,
`max_pages`, `level`, `record_types`, `threads`, and process extras like `chunk_pages`,
`stock`, `key`, `order`, `dump`, `extract_to`.

**Output compression** has two independent levers:
- **File compression** of the index output — `<index compress="gzip" level="0-10"/>`.
- **Internal compression** of the output print stream — `internal-compress="1"` (PDF
  only today): zlib-compresses PDF content streams. `1`/`true` on, `0`/`false` off;
  omit to use the writer default. See [printstreams.md](printstreams.md#internal-compression).

## Document identification — `<identify>`

A new document begins on each page that matches. One of:

```xml
<identify by="page-count" pages="2"/>          <!-- fixed N pages per document -->
<identify by="text"   value="STATEMENT"/>      <!-- page contains this text -->
<identify by="hex"    value="d3eeeb"/>          <!-- page contains these bytes -->
<identify by="window" value="0,0,612,72"/>      <!-- any element in this window -->
```

## Extraction fields — `<fields>`

Named values located by window, text, or hex, written into the index and available for
`{field}` substitution in enhancements:

```xml
<fields>
  <field name="account" window="430,90,140,16"/>
  <field name="keyword" text="INVOICE"/>
  <field name="has_barcode" hex="d3eeeb"/>
</fields>
```

## Enhancements — `<enhancements>`

The same vocabulary you would use to compose from PSML. Selection for delete/modify is
by `kind`, `window`, `text`, or `hex`. `{field}` values are substituted from the index
record during merge.

```xml
<enhancements>
  <delete kind="barcode" window="400,40,170,40"/>
  <modify text="DRAFT" set-color="#cc0000" set-size="14"/>
  <add kind="text" x="72" y="60" size="9" color="#000000">Acct {account}</add>
  <add kind="barcode" symbology="code128" x="400" y="40" width="160" height="36" data="{account}"/>
  <add kind="barcode" symbology="qr" x="540" y="700" width="48" height="48" data="{account}"/>
  <add kind="omr" x="18" y="80" width="8" height="240" data="101101"/>
  <add kind="line" x1="72" y1="96" x2="540" y2="96" weight="1" color="#000000"/>
  <add kind="rectangle" x="72" y="110" width="200" height="40" color="#000000" fill="#eeeeee"/>
  <add kind="image" src="logo.png" x="72" y="700" width="120" height="48"/>
  <add kind="overlay" name="LETTERHD" x="0" y="0"/>
</enhancements>
```

Barcode symbologies: see [barcodes.md](barcodes.md).

## Imposition — `<imposition>`

Sheet geometry plus optional per-cell layout for total control of n-up.

```xml
<imposition page-width="792" page-height="612" rows="1" cols="2"
            group-size="4" margin-top="18" margin-left="18" h-gap="12"
            rotate="0" scale="true">
  <!-- Without <cell> children: pages flow row-major, rows*cols per sheet. -->
  <!-- With <cell> children: place specific input pages per cell. -->
  <cell row="0" col="0" page="n"   rotate="0" valign="center"/>
  <cell row="0" col="1" page="1"   rotate="0" valign="center"/>
</imposition>
```

Attributes:
- Sheet: `page-size` (named) or `page-width`/`page-height`; `rows`, `cols`;
  `margin-top`, `margin-left`, `h-gap`, `v-gap`; `rotate` (default for flowed cells);
  `scale` (fit-to-cell); `group-size` (input pages consumed per sheet, default
  `rows*cols`).
- `<cell>`: `row`, `col`; `page` — `auto` (flow position), an absolute number, or a
  reference to the end of the group: `n` (last), `n-1`, `n-2`, …; `rotate`
  (0/90/180/270); `scale` (explicit factor; omit to fit); `halign`
  (left/center/right); `valign` (top/center/bottom).

This expresses booklet/saddle-stitch and other commercial impositions — e.g. place the
**last** page (`n`) and **first** page (`1`) of each 4-page group side by side.
