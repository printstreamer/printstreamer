# Barcodes and OMR

Barcodes are model elements (`BarcodeElement`: `symbology`, `data`, `params`) created by
parsers, by `<add kind="barcode">` in a spec/edit/PSML, or by label templates. The PDF
writer renders them as real symbols ([writer/barcodes.py](../writer/barcodes.py)).

## Supported symbologies

| `symbology` value(s) | Type |
|---|---|
| `code39`, `3of9`, `39` | Code 39 |
| `code128`, `128`, `128a`, `128b`, `128c` | Code 128 (auto/A/B/C) |
| `code93`, `93` | Code 93 |
| `qr`, `qrcode` | QR Code (2D) |
| `datamatrix`, `ecc200`, `2d` | Data Matrix ECC200 (2D) |
| `usps`, `imb` | USPS Intelligent Mail (4-State) |
| `omr` | OMR timing marks (see below) |

Unknown symbologies render as a framed human-readable value. (PDF417 needs an external
library and is not bundled.)

## Usage

```xml
<add kind="barcode" symbology="code128" x="400" y="40" width="160" height="36" data="{account}"/>
<add kind="barcode" symbology="3of9"    x="72"  y="700" width="160" height="40" data="DOC-0001"/>
<add kind="barcode" symbology="qr"      x="540" y="700" width="48"  height="48" data="{url}"/>
```

`params` (via element attributes) include `hri` (human-readable text, default on) for
1D symbologies.

## OMR marks

OMR (Optical Mark Recognition) timing marks drive inserters/folders. `data` is a bit
string; each `1` draws a horizontal mark down the box.

```xml
<add kind="omr" x="18" y="80" width="8" height="240" data="101101"
     mark_height="2" pitch="12"/>
```

- `mark_height` — bar thickness in points (default 2).
- `pitch` — top-to-top spacing in points (default fits the marks in the box height).
