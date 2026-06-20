""" Multi-threaded AFP parsing (R12).

A cheap boundary scan reads only record introducers (6 bytes each) to locate every
document and page offset. Pages are partitioned into contiguous spans; worker threads
each parse their own byte range — seeded at a real record boundary — into a private
model. The workers' results are then concatenated and reconciled into the original
document structure using the scan, so the threaded result equals the serial one.

Python's GIL limits CPU speedup for pure-Python parsing; the design also supports a
process pool for true parallelism, but threads match the requested model and overlap
the file I/O. Thread count is caller-controlled, capped at the system maximum.
"""

from __future__ import annotations

import logging
import os
import struct
from concurrent.futures import ThreadPoolExecutor

import stream_afp
from model.document import Document
from parse_options import ParseOptions
from stream_file import StreamFile
from stream_segment_afp import StreamSegmentAFP

logger = logging.getLogger(__name__)


def max_threads(requested=None):
    """ Resolve a thread count: caller request clamped to [1, cpu_count]. """
    cpu = os.cpu_count() or 1
    if not requested or requested <= 0:
        return cpu
    return max(1, min(int(requested), cpu))


def scan_afp_boundaries(path):
    """ Return (pages, docs, total_bytes).

    pages: list of (byte_offset, doc_index) for each BPG, in file order.
    docs:  list of (byte_offset, name) for each document (BDT, or an implicit one).
    """
    with open(path, "rb") as fh:
        data = fh.read()
    pages = []
    docs = []
    doc_index = -1
    i = 0
    n = len(data)
    while i + 6 <= n and data[i:i + 1] == b"\x5a":
        length = struct.unpack(">H", data[i + 1:i + 3])[0] + 1
        rid = data[i + 3:i + 6]
        rec = stream_afp.afp_rec_type.get(rid)
        t = rec["type"] if rec else None
        if t == "BDT":
            doc_index += 1
            name = data[i + 9:i + 17].decode("cp500", "replace").strip()
            docs.append((i, name or None))
        elif t == "BPG":
            if doc_index < 0:                # page before any BDT: implicit document
                doc_index = 0
                docs.append((i, None))
            pages.append((i, doc_index))
        i += length
    return pages, docs, n


def _partition(count, parts):
    """ Split range(count) into ``parts`` contiguous index groups. """
    parts = max(1, min(parts, count))
    size, extra = divmod(count, parts)
    groups = []
    start = 0
    for p in range(parts):
        length = size + (1 if p < extra else 0)
        groups.append(list(range(start, start + length)))
        start += length
    return [g for g in groups if g]


def _parse_span(path, options, start, end):
    """ Parse one byte span [start, end) of an AFP file into a private model. """
    worker = StreamFile.__new__(StreamFile)        # avoid full-file segment in __init__
    worker.name = path
    worker.file_type = "afp"
    worker.type = "input"
    worker.documents = worker.pages = worker.records = 0
    worker.segments = []

    class _Parser:
        pass
    p = _Parser()
    p.options = options
    from model.document import StreamDocumentSet
    p.document_set = StreamDocumentSet()
    worker.parser = p

    segment = StreamSegmentAFP(worker, 1, start_byte_offset=start, end_byte_offset=end)
    segment.parse()
    return p.document_set


def parse_afp_threaded(path, parser, threads=None):
    """ Parse an AFP file using ``threads`` workers, filling parser.document_set so the
    result is identical in structure to a serial parse. Returns the thread count used. """
    pages, docs, total = scan_afp_boundaries(path)
    n_threads = max_threads(threads)
    if len(pages) <= 1 or n_threads <= 1:
        _serial(path, parser)
        return 1

    groups = _partition(len(pages), n_threads)
    spans = []
    for gi, group in enumerate(groups):
        start = pages[group[0]][0]
        end = pages[groups[gi + 1][0]][0] if gi + 1 < len(groups) else total
        spans.append((start, end))

    options = ParseOptions(level=parser.options.level)   # span parses fully, no paging
    with ThreadPoolExecutor(max_workers=n_threads) as pool:
        results = list(pool.map(lambda s: _parse_span(path, options, s[0], s[1]), spans))

    _reconcile(parser, results, pages, docs)
    logger.info("Parsed %s with %d threads (%d pages, %d docs)",
                path, n_threads, len(pages), len(docs))
    return n_threads


def _reconcile(parser, results, pages, docs):
    """ Concatenate worker pages in order and regroup them into the scanned docs. """
    all_pages = []
    worker_resources = []
    for ds in results:
        worker_pages = ds.all_pages()
        all_pages.extend(worker_pages)
        worker_resources.append([r for d in ds.documents for r in d.resource_library])

    page_doc = [di for _off, di in pages]
    final = parser.document_set
    final_docs = {}
    for gpn, page in enumerate(all_pages):
        di = page_doc[gpn] if gpn < len(page_doc) else (page_doc[-1] if page_doc else 0)
        if di not in final_docs:
            name = docs[di][1] if di < len(docs) else None
            final_docs[di] = final.add_document(Document(name=name))
        page.number = gpn + 1
        final_docs[di].add_page(page)
    # Best-effort: make every composed resource available on each final document.
    for res_list in worker_resources:
        for res in res_list:
            for doc in final_docs.values():
                if res.name not in doc.resource_library:
                    doc.resource_library.add(res)


def _serial(path, parser):
    sf = StreamFile(parser, path, file_type="afp", type="input")
    parser.input_files.append(sf)
    sf.parse()
