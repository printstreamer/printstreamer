""" External AFP font-resource library lookup.

When a coded font is referenced by name but not embedded in the print stream, its true
point size and per-character widths can be supplied from an external library directory
(``ParseOptions.font_path``). Two resource forms are supported, tried in order for a
character-set / coded-font name:

1. a JSON metrics sidecar ``<name>.json`` — ``{"size": 12.0, "widths": {"65": 600, ...},
   "encoding": {"65": "A", ...}}`` (widths in 1/1000 em, keyed by code point); a reliable,
   tool-agnostic way to provide exact metrics;
2. a native AFP FOCA resource file ``<name>`` (structured fields) — parsed best-effort for
   per-character increments via the Font Index (FNI).

Returns False (so the caller falls back to base-font metrics) whenever nothing usable is
found, so a configured-but-incomplete library never degrades output.
"""

from __future__ import annotations

import json
import logging
import os
import struct

logger = logging.getLogger(__name__)


def _candidates(directory, name):
    if not name:
        return []
    out = []
    for fn in (f"{name}.json", f"{name}.JSON", name, f"{name}.fnt", f"{name}.FNT"):
        p = os.path.join(directory, fn)
        if os.path.isfile(p):
            out.append(p)
    return out


def apply(font, font_path) -> bool:
    """ Look up ``font`` in the library dir; fill size/metrics/encoding. True if found. """
    if not font_path or not os.path.isdir(font_path):
        return False
    for name in (font.char_set, font.coded_font):
        for path in _candidates(font_path, name):
            if path.lower().endswith(".json"):
                if _apply_json(font, path):
                    return True
            elif _apply_foca(font, path):
                return True
    return False


def _apply_json(font, path) -> bool:
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except Exception:
        logger.exception("Bad font metrics sidecar %s", path)
        return False
    widths = data.get("widths") or {}
    metrics = {}
    encoding = data.get("encoding") or {}
    enc_map = {int(k): v for k, v in encoding.items()} if encoding else {}
    for cp_str, adv in widths.items():
        cp = int(cp_str)
        ch = enc_map.get(cp) or font.encoding_map.get(cp) or chr(cp)
        metrics[ord(ch)] = float(adv)
    if metrics:
        font.metrics = metrics
    if enc_map and not font.encoding_map:
        font.encoding_map = enc_map
    if data.get("size"):
        font.size = float(data["size"])
    if not font.size:
        font.size = 10.0
    return bool(metrics)


def _iter_sf(data):
    i, n = 0, len(data)
    while i + 6 <= n and data[i:i + 1] == b"\x5a":
        rl = struct.unpack(">H", data[i + 1:i + 3])[0] + 1
        if rl <= 0 or i + rl > n:
            break
        yield data[i + 3:i + 6], data[i + 9:i + rl]
        i += rl


def _apply_foca(font, path) -> bool:
    """ Best-effort native FOCA resource: pull per-character increments from FNI.

    FNI (X'D38C89') carries one fixed-length entry per character; the character
    increment (advance) is a 2-byte field within each entry. Layouts vary by font, so
    this only applies metrics when the entry size divides the data cleanly and yields
    plausible advances, otherwise returns False to fall back to base metrics. """
    try:
        with open(path, "rb") as fh:
            blob = fh.read()
    except Exception:
        return False
    from afp import fonts
    builder = fonts.FontBuilder(name=font.char_set)
    for rid, body in _iter_sf(blob):
        fonts.apply_foca_record(builder, rid, body)
    builder.finish()
    if builder.metrics or builder.size:
        builder.apply(font)
        return bool(font.metrics)
    return False
