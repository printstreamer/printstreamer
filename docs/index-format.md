# Index file format

`extract` produces two index files that locate every page and logical document in the
input print stream, so a later `merge`/`split` can pull content back by byte range
without re-modeling it. There are two serializations: **flat** (the default — fixed-length
text records, uncompressed) and **json**. Select with `index_format="flat"` (default) or
`index_format="json"` on the step (or in a `spec.xml`).

Two files are written per extract:

- **page index** — one record per page (default name: the `index=` path, e.g. `out.idx`);
- **document index** — one record per *logical user document* (same path with `.docs`
  inserted, e.g. `out.docs.idx`).

Both lead with **`document_offset`**, the **zero-based** logical-document ordinal (the
count of documents before it). It is the join key between the two files. A logical
document is defined by the extract boundary rules (`start-on-text/hex/window` or
`pages_per_document`); `byte_offset`/`record_offset` point to the **first byte/record of
that logical document** in the input (not necessarily an AFP `BDT`).

The document index also indexes **into the page index file** via its `pi_*` fields, so a
document's fixed-length page records can be read directly (seek to `pi_byte_offset`, read
`pi_byte_count` bytes = `pi_record_count` page records).

The implementation lives in [process/index.py](../process/index.py)
(`PAGE_SCHEMA`, `DOC_SCHEMA`, `serialize`, `load`).

## Flat format — page index record

One record per line; each field is a fixed-width column (integers right-justified, space
padded; strings left-justified, space padded, truncated to width). Lines end in `LF`.
Record width is **190 bytes** + 40 per extraction field + 1 (`LF`).

| Field              | Offset | Width | Type   | Meaning |
|--------------------|-------:|------:|--------|---------|
| `document_offset`  | 0      | 8     | int    | zero-based logical-document ordinal (join key) |
| `page_number`      | 8      | 8     | int    | global page number (1-based) |
| `page_in_document` | 16     | 6     | int    | page number within its logical document |
| `byte_offset`      | 22     | 12    | int    | page start byte offset in the input |
| `byte_count`       | 34     | 10    | int    | page byte span |
| `record_offset`    | 44     | 10    | int    | page start record number |
| `record_count`     | 54     | 8     | int    | page record count |
| `input_path`       | 62     | 128   | string | input print-stream file path |
| *(extraction fields)* | 190 | 40 each | string | one column per spec `<field>`, in order |

If any extraction fields are present, a single leading schema line `#FIELDS name1 name2 …`
precedes the records (and is accounted for in the document index's `pi_byte_offset`).

## Flat format — document index record

**Each document record is padded to exactly `DOC_RECORD_SIZE` = 2000 bytes**: the schema
columns, then spaces, then a single `LF` as the 2000th byte (no `CR`). So document N is
read by seeking to `N * 2000`, and the reserved tail leaves room for future
document-level fields without changing the layout. Content occupies the first 294 bytes;
the rest is space padding.

| Field              | Offset | Width | Type   | Meaning |
|--------------------|-------:|------:|--------|---------|
| `document_offset`  | 0      | 8     | int    | zero-based logical-document ordinal (join key) |
| `byte_offset`      | 8      | 12    | int    | document start byte offset in the input |
| `byte_count`       | 20     | 12    | int    | document byte span in the input |
| `record_offset`    | 32     | 10    | int    | document start record number |
| `record_count`     | 42     | 10    | int    | document record count |
| `page_offset`      | 52     | 8     | int    | first global page number |
| `page_count`       | 60     | 8     | int    | document page count |
| `document_count`   | 68     | 6     | int    | documents represented (normally 1) |
| `pi_byte_offset`   | 74     | 12    | int    | byte offset of this doc's records in the **page index file** |
| `pi_byte_count`    | 86     | 12    | int    | byte span of this doc's page records |
| `pi_record_offset` | 98     | 10    | int    | first page-index record number for this doc |
| `pi_record_count`  | 108    | 10    | int    | number of page-index records (== `page_count`) |
| `pi_page_offset`   | 118    | 8     | int    | first global page number (page-index view) |
| `pi_page_count`    | 126    | 8     | int    | page count (page-index view) |
| `input_path`       | 134    | 128   | string | input print-stream file path |
| `document_name`    | 262    | 32    | string | logical document name (if any) |
| *(padding)*        | 294    | →1999 | spaces | reserved |
| `LF`               | 1999   | 1     | byte   | `0x0A`; the 2000th byte |

The first two blocks (`byte_*`/`record_*`/`page_*`/`document_*`) address the **input
print stream**; the `pi_*` block addresses the **page index file**.

## JSON format

Both indexes serialize as a JSON array of objects (one per page / per document), each a
direct dump of the [`IndexRecord`](../process/index.py) dataclass. The page index uses the
page fields and nests extraction values under `fields`; the document index uses the same
object with the `pi_*` and span fields populated. Field names match the flat-format column
names above, with `input_path` carried as `source` and the extraction values under
`fields`:

```json
// page index
[{ "source": "in.afp", "document_offset": 0, "page_number": 1, "page_in_document": 1,
   "byte_offset": 87, "byte_count": 8728, "record_offset": 3, "record_count": 21,
   "fields": { "acct": "12345" } }]

// document index
[{ "source": "in.afp", "document_offset": 0, "byte_offset": 87, "byte_count": 171366,
   "record_offset": 3, "record_count": 83, "page_offset": 1, "page_count": 3,
   "document_count": 1, "pi_byte_offset": 0, "pi_byte_count": 573,
   "pi_record_offset": 0, "pi_record_count": 3, "pi_page_offset": 1, "pi_page_count": 3,
   "document_name": null }]
```

## How `merge` uses the index

- **Streaming passthrough** (output format == source format, no transform/ops): the page
  records' `byte_offset`/`byte_count` are copied straight from the input in index order,
  grouped into documents by `document_offset`, with record-level deletions applied on the
  fly. Each logical document is wrapped in a fresh `BDT`/`EDT` envelope (logical documents
  need not align with the source `BDT`), so document-level records that fall *outside* any
  page span are not reproduced — page content is reproduced byte-for-byte.
- **Transform**: the referenced spans are re-parsed into the model and written via the
  target writer.
