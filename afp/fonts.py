""" Resolve precise font metrics for a FontResource, most-precise source first.

A coded font referenced by an MCF needs a point size, a code-point->Unicode map and a
per-character advance-width table so text width (and thus window extraction) is exact and
so the font can be converted faithfully on output. Three tiers, in order:

1. **Embedded FOCA** — metrics built from FOCA font resources carried in the same stream
   (see :mod:`afp.fonts` ``FontBuilder`` and the ``afp/foca`` record classes).
2. **External font library** — :mod:`afp.fontlib` looks up the font in a configured
   resource directory (``ParseOptions.font_path``).
3. **Base-font fallback** — per-character widths from the mapped base-14 font, so widths
   stay precise for the output font even when no font data is available.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

_DEFAULT_SIZE = 10.0


def resolve_font(font, policy=None, embedded=None):
    """ Fill ``font.size`` / ``.encoding_map`` / ``.metrics`` from the best source. """
    # 1. embedded FOCA captured during this parse
    if embedded:
        built = embedded.get(font.char_set) or embedded.get(font.coded_font)
        if built is not None:
            built.apply(font)
            font.attributes["metrics_source"] = "embedded-foca"
            return
    # 2. external font library
    path = getattr(policy, "font_path", None) if policy is not None else None
    if path:
        try:
            from afp import fontlib
            if fontlib.apply(font, path):
                font.attributes["metrics_source"] = "font-library"
                return
        except Exception:
            logger.exception("Font library lookup failed for %s", font.char_set)
    # 3. base-font fallback
    _base_fallback(font)


def _base_fallback(font):
    import fontmetrics
    if not font.metrics:
        font.metrics = fontmetrics.build_metrics(font)
    if not font.size:
        font.size = estimate_size(font.char_set) or _DEFAULT_SIZE
    font.attributes.setdefault("metrics_source", "base-font-estimate")


def estimate_size(char_set: str | None) -> float | None:
    """ Best-effort point size from an IBM coded-font / character-set name.

    Many IBM raster char-set names encode the vertical size in the trailing digits in
    tenths of a point (e.g. ``...0120`` -> 12.0pt). Returns None when not derivable so the
    caller can fall back to a default (and flag the size as estimated). """
    if not char_set:
        return None
    digits = "".join(c for c in char_set if c.isdigit())
    if len(digits) >= 3:
        try:
            tenths = int(digits[-3:])
            if 30 <= tenths <= 720:           # 3.0pt .. 72.0pt, a sane range
                return tenths / 10.0
        except ValueError:
            pass
    return None


# --- embedded FOCA builder -------------------------------------------------

class FontBuilder:
    """ Accumulates FOCA font-resource data for one font and applies it to a
    FontResource. Populated by the ``afp/foca`` record classes during parse. """

    def __init__(self, name=None):
        self.name = name
        self.code_page = None
        self.size = None
        self.unit_base = 1000          # FNORM/em units; FNC sets the real value
        self.x_resolution = None
        self.encoding_map = {}         # codepoint -> unicode
        self.gcgid_width = {}          # GCGID -> raw advance (font units)
        self.code_to_gcgid = {}        # codepoint -> GCGID
        self.metrics = {}              # codepoint -> advance in 1/1000 em

    def set_descriptor(self, *, size=None, unit_base=None, x_resolution=None):
        if size is not None:
            self.size = size
        if unit_base:
            self.unit_base = unit_base
        if x_resolution:
            self.x_resolution = x_resolution

    def add_char_width(self, gcgid, advance):
        self.gcgid_width[gcgid] = advance

    def map_code(self, codepoint, gcgid, unicode_char=None):
        self.code_to_gcgid[codepoint] = gcgid
        if unicode_char is not None:
            self.encoding_map[codepoint] = unicode_char

    def finish(self):
        """ Resolve per-codepoint advances (1/1000 em) from GCGID widths. """
        unit = self.unit_base or 1000
        for cp, gcgid in self.code_to_gcgid.items():
            adv = self.gcgid_width.get(gcgid)
            if adv is not None:
                self.metrics[ord(self.encoding_map.get(cp, chr(cp)))] = adv / unit * 1000.0
        return self

    def apply(self, font):
        if self.size and not font.size:
            font.size = self.size
        if self.encoding_map:
            # encoding map here is codepoint->unicode; merge without clobbering an
            # already-resolved code-page map unless we have nothing.
            if not font.encoding_map:
                font.encoding_map = dict(self.encoding_map)
        if self.metrics:
            font.metrics = dict(self.metrics)
        elif not font.metrics:
            import fontmetrics
            font.metrics = fontmetrics.build_metrics(font)
        if not font.size:
            font.size = _DEFAULT_SIZE


# --- FOCA record decoders (shared by embedded parse and the font library) ---
# Conservative: only set metrics when the layout is consistent, so a misread native
# resource degrades to base-font metrics rather than emitting wrong widths.

_FOCA_FNC = b"\xd3\xa7\x89"      # Font Control
_FOCA_FND = b"\xd3\xa6\x89"      # Font Descriptor
_FOCA_FNI = b"\xd3\x8c\x89"      # Font Index
_FOCA_CPI = b"\xd3\x8c\x87"      # Code Page Index


def apply_foca_record(builder: "FontBuilder", rid: bytes, body: bytes) -> None:
    """ Dispatch one FOCA structured field (by 3-byte id) into ``builder``. """
    if rid == _FOCA_FNC:
        _apply_fnc(builder, body)
    elif rid == _FOCA_FND:
        _apply_fnd(builder, body)
    elif rid == _FOCA_FNI:
        _apply_fni(builder, body)
    elif rid == _FOCA_CPI:
        _apply_cpi(builder, body)


def _apply_fnc(builder, body):
    # Font Control: the unit base / units-per-em used by FNI increments. The FNORM
    # X-unit value (units per em) is a 2-byte field; capture it when present.
    if len(body) >= 14:
        upem = int.from_bytes(body[12:14], "big")
        if 100 <= upem <= 20000:
            builder.unit_base = upem


def _apply_fnd(builder, body):
    # Font Descriptor: nominal vertical font size, in 1/1440 inch (a 2-byte field near
    # the start of the descriptor); convert to points when plausible.
    if len(body) >= 4:
        raw = int.from_bytes(body[2:4], "big")
        pts = raw / 20.0                       # 1/1440 in -> points (1440/72 = 20)
        if 3.0 <= pts <= 144.0:
            builder.size = pts


def _apply_fni(builder, body):
    # Font Index: fixed-length per-character entries. The common single-byte layout is
    # GCGID(2) + flags(2) + A-space(2,signed) + B-space(2) + C-space(2) = char increment.
    entry = 26
    if len(body) < entry or len(body) % entry:
        # try the compact 10-byte variant: GCGID(2)+reserved(6)+increment(2)
        entry = 10
        if len(body) < entry or len(body) % entry:
            return
    n = len(body) // entry
    for k in range(n):
        e = body[k * entry:(k + 1) * entry]
        gcgid = int.from_bytes(e[0:2], "big")
        increment = int.from_bytes(e[-2:], "big")
        builder.add_char_width(gcgid, increment)


def _apply_cpi(builder, body):
    # Code Page Index: per code point, a GCGID (8-byte name) + the single-byte code
    # point. Map code point -> a stable GCGID hash so FNI widths can be looked up.
    entry = 10
    if len(body) < entry or len(body) % entry:
        return
    for k in range(len(body) // entry):
        e = body[k * entry:(k + 1) * entry]
        gcgid_name = e[0:8]
        codepoint = e[9]
        builder.map_code(codepoint, int.from_bytes(gcgid_name[-2:], "big"))
