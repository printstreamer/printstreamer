""" Map an AFP code page to a code-point -> Unicode table for faithful text decode.

AFP text bytes are code points in the coded font's code page (e.g. T1001252 ->
Windows-1252, T1V10500 -> EBCDIC 500). Decoding them with the right code page — rather
than a blanket latin-1 — is what makes extracted/transformed text correct for the high
range (smart quotes, accented letters, EBCDIC, ...).

Embedded FOCA code-page resources (CPD/CPI) would give an exact table; absent those in
the print stream, we resolve the code page name to the matching Python codec by its
CPGID and build the 256-entry map from it.
"""

from __future__ import annotations

import re
from functools import lru_cache

# A few common AFP/IBM code page names whose CPGID is not simply the trailing digits.
_NAMED = {
    "T1V10500": 500, "T1V10037": 37, "T1V10273": 273, "T1V10277": 277,
    "T1V10278": 278, "T1V10280": 280, "T1V10284": 284, "T1V10285": 285,
    "T1DCDCF": 500,
}


def _cpgid_candidates(name: str | None):
    """ Yield candidate CPGIDs for an AFP code page name, most-specific first. """
    if not name:
        return
    key = name.strip().upper()
    if key in _NAMED:
        yield _NAMED[key]
    m = re.search(r"(\d+)$", key)
    if not m:
        return
    digits = m.group(1)
    seen = set()
    for cand in (digits[-4:], digits[-3:], digits[-5:], digits):
        if cand and cand not in seen:
            seen.add(cand)
            yield int(cand)


def _codec_for_cpgid(cpgid: int) -> str | None:
    import codecs
    for cand in (f"cp{cpgid}", f"cp{cpgid:03d}"):
        try:
            codecs.lookup(cand)
            return cand
        except LookupError:
            continue
    return None


def cpgid_for(name: str | None) -> int | None:
    """ Best-effort CPGID from an AFP code page name (the one whose codec resolves). """
    first = None
    for cand in _cpgid_candidates(name):
        if first is None:
            first = cand
        if _codec_for_cpgid(cand):
            return cand
    return first


def _codec_for(cpgid: int | None) -> str | None:
    return _codec_for_cpgid(cpgid) if cpgid is not None else None


@lru_cache(maxsize=256)
def unicode_map(code_page_name: str | None) -> dict:
    """ Return ``{codepoint: unicode_char}`` for an AFP code page, or {} if unknown. """
    codec = _codec_for(cpgid_for(code_page_name))
    if codec is None:
        return {}
    out = {}
    for b in range(256):
        try:
            out[b] = bytes([b]).decode(codec)
        except Exception:
            continue
    return out


def codec_name(code_page_name: str | None) -> str | None:
    """ The resolved Python codec name for a code page (for diagnostics/tests). """
    return _codec_for(cpgid_for(code_page_name))
