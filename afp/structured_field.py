""" Shared, data-driven structured-field decode engine.

Instead of ~90 bespoke parsers, one generic decoder turns any MO:DCA/FOCA/IOCA/
BCOCA structured-field data area into a transient ``RecordView`` (fixed-field prefix +
triplets + repeating groups), driven by a compact per-record ``Layout`` table. The
``RecordView`` is consumed to build the normalized model and then discarded — the
model never holds raw structured fields (see plan §2/§3).

This is the "share as much code as possible" backbone: triplet decoding is delegated
to :mod:`afp.triplets`, fixed-field unpacking and repeating-group walking are common,
and a record only needs a table entry (and an emitter for the model) rather than its
own byte parser.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from afp import triplets as _triplets

logger = logging.getLogger(__name__)


# --- layout description ----------------------------------------------------

@dataclass
class Field:
    """ One fixed field. ``length`` may be an int or ``"rest"`` for the remainder. """
    name: str
    length: object          # int | "rest"
    kind: str = "u"         # u=unsigned int, s=signed int, ebcdic, bytes


@dataclass
class Repeat:
    """ A repeating group: a length-prefixed group, optionally with its own fixed
    fields then a triplet area. ``length_bytes`` is the size of the leading length
    field, which counts itself + the group body. """
    length_bytes: int = 2
    fixed: list = field(default_factory=list)
    triplets: bool = True


@dataclass
class Layout:
    arch: str = "modca"
    fixed: list = field(default_factory=list)   # list[Field]
    triplets: bool = False                       # triplet area follows the fixed prefix
    repeat: Repeat | None = None                 # repeating groups follow the prefix
    raw: bool = False                            # content is opaque (GOCA/IOCA/bcoca data)


@dataclass
class RecordView:
    """ Transient decoded view of one structured field (never stored in the model). """
    type: str
    arch: str
    fixed: dict = field(default_factory=dict)
    triplets: list = field(default_factory=list)        # list[Triplet]
    groups: list = field(default_factory=list)          # list[dict]
    data: bytes = b""

    def triplet(self, tid):
        return _triplets.find(self.triplets, tid)

    def triplets_of(self, tid):
        return _triplets.find_all(self.triplets, tid)


# --- fixed-field unpacking -------------------------------------------------

def _read(data, off, fld):
    if fld.length == "rest":
        chunk = data[off:]
        off2 = len(data)
    else:
        chunk = data[off:off + fld.length]
        off2 = off + fld.length
    if fld.kind == "u":
        val = int.from_bytes(chunk, "big", signed=False) if chunk else 0
    elif fld.kind == "s":
        val = int.from_bytes(chunk, "big", signed=True) if chunk else 0
    elif fld.kind == "ebcdic":
        val = chunk.decode("cp500", "replace").rstrip()
    else:
        val = bytes(chunk)
    return val, off2


def _parse_fixed(data, fields):
    out = {}
    off = 0
    for fld in fields:
        if off >= len(data) and fld.length != "rest":
            break
        out[fld.name], off = _read(data, off, fld)
    return out, off


def _parse_repeat(data, off, repeat, policy):
    groups = []
    i = off
    n = len(data)
    lb = repeat.length_bytes
    while i + lb <= n:
        glen = int.from_bytes(data[i:i + lb], "big")
        if glen < lb or i + glen > n:
            break
        body = data[i + lb:i + glen]
        g = {}
        boff = 0
        if repeat.fixed:
            g, boff = _parse_fixed(body, repeat.fixed)
        if repeat.triplets:
            g["triplets"] = _triplets.parse_triplets(body[boff:], policy)
        groups.append(g)
        i += glen
    return groups


# --- public API ------------------------------------------------------------

def decode(rec_type: str, data: bytes, policy=None) -> RecordView:
    """ Decode a structured-field data area (bytes after the 9-byte introducer). """
    layout = RECORD_LAYOUTS.get(rec_type) or _DEFAULT_LAYOUT
    view = RecordView(type=rec_type, arch=layout.arch, data=data)
    if layout.raw:
        return view
    off = 0
    if layout.fixed:
        view.fixed, off = _parse_fixed(data, layout.fixed)
    if layout.repeat is not None:
        view.groups = _parse_repeat(data, off, layout.repeat, policy)
    elif layout.triplets:
        view.triplets = _triplets.parse_triplets(data[off:], policy)
    return view


# --- record layout table ---------------------------------------------------
# Compact descriptions distilled from the MO:DCA/FOCA/IOCA/BCOCA references. Records
# whose payload is purely triplets need only ``triplets=True``; descriptor records get
# a fixed prefix; mapping records get a repeating group.

_F = Field
_NAME = _F("name", 8, "ebcdic")

# Geometry descriptors: UnitBase x2, Units x2 (2 bytes each), Size x2 (3 bytes each).
_DESC_GEOM = [_F("x_unit_base", 1), _F("y_unit_base", 1),
              _F("x_units", 2), _F("y_units", 2),
              _F("x_size", 3), _F("y_size", 3)]

# Object Area Position body (OBP).
_OBP_FIXED = [_F("oapid", 1), _F("rglength", 1),
              _F("x_origin", 3, "s"), _F("y_origin", 3, "s"),
              _F("x_rotation", 2), _F("y_rotation", 2),
              _F("x_offset", 3, "s"), _F("y_offset", 3, "s")]

# Include records: name + position.
_INCLUDE = [_NAME, _F("x_origin", 3, "s"), _F("y_origin", 3, "s")]

RECORD_LAYOUTS = {
    # --- structural (name + optional triplets) ---
    "BAG": Layout("modca", [_NAME], triplets=True),
    "BBC": Layout("modca", [_NAME], triplets=True),
    "BCA": Layout("modca", [_NAME], triplets=True),
    "BDG": Layout("modca", triplets=True),
    "BDI": Layout("modca", [_NAME], triplets=True),
    "BDT": Layout("modca", [_NAME], triplets=True),
    "BFM": Layout("modca", [_NAME], triplets=True),
    "BGR": Layout("modca", [_NAME], triplets=True),
    "BIM": Layout("modca", [_NAME], triplets=True),
    "BMM": Layout("modca", [_NAME], triplets=True),
    "BMO": Layout("modca", [_NAME], triplets=True),
    "BNG": Layout("modca", [_NAME], triplets=True),
    "BOC": Layout("modca", [_NAME], triplets=True),
    "BOG": Layout("modca", triplets=True),
    "BPG": Layout("modca", [_NAME], triplets=True),
    "BPS": Layout("modca", [_NAME], triplets=True),
    "BPT": Layout("modca", [_NAME], triplets=True),
    "BRG": Layout("modca", [_NAME], triplets=True),
    "BRS": Layout("modca", [_NAME], triplets=True),
    "BSG": Layout("modca", [_NAME], triplets=True),
    "EAG": Layout("modca", triplets=True),
    "EBC": Layout("modca", [_NAME], triplets=True),
    "ECA": Layout("modca", [_NAME], triplets=True),
    "EDG": Layout("modca", triplets=True),
    "EDI": Layout("modca", triplets=True),
    "EDT": Layout("modca", [_NAME], triplets=True),
    "EFM": Layout("modca", [_NAME], triplets=True),
    "EGR": Layout("modca", [_NAME], triplets=True),
    "EIM": Layout("modca", [_NAME], triplets=True),
    "EMM": Layout("modca", [_NAME], triplets=True),
    "EMO": Layout("modca", [_NAME], triplets=True),
    "ENG": Layout("modca", [_NAME], triplets=True),
    "EOC": Layout("modca", [_NAME], triplets=True),
    "EOG": Layout("modca", triplets=True),
    "EPG": Layout("modca", [_NAME], triplets=True),
    "EPS": Layout("modca", [_NAME], triplets=True),
    "EPT": Layout("modca", [_NAME], triplets=True),
    "ERS": Layout("modca", [_NAME], triplets=True),
    "ESG": Layout("modca", triplets=True),
    # --- descriptors ---
    "PGD": Layout("modca", _DESC_GEOM, triplets=True),
    "MDD": Layout("modca", _DESC_GEOM, triplets=True),
    "PTD": Layout("modca", [_F("x_unit_base", 1), _F("y_unit_base", 1),
                            _F("x_units", 2), _F("y_units", 2),
                            _F("x_size", 3), _F("y_size", 3)], triplets=True),
    "OBD": Layout("modca", triplets=True),
    "CDD": Layout("modca", _DESC_GEOM, triplets=True),
    "GDD": Layout("goca", raw=True),
    "BDD": Layout("bcoca", raw=True),
    "IDD": Layout("ioca", raw=True),
    # --- positions / placement ---
    "OBP": Layout("modca", _OBP_FIXED, triplets=False),
    "PGP": Layout("modca", [_F("flags", 1), _F("x_origin", 3, "s"),
                            _F("y_origin", 3, "s")], triplets=True),
    "IPO": Layout("modca", _INCLUDE, triplets=True),
    "IPS": Layout("modca", _INCLUDE, triplets=True),
    "IPG": Layout("modca", [_NAME], triplets=True),
    "IOB": Layout("modca", [_NAME], triplets=True),
    "IMM": Layout("modca", [_NAME], triplets=True),
    # --- maps (repeating groups of triplets) ---
    "MCF": Layout("modca", repeat=Repeat(2, triplets=True)),
    "MMC": Layout("modca", repeat=Repeat(1, fixed=[_F("mid", 1), _F("flags", 1)],
                                         triplets=True)),
    "MCC": Layout("modca", repeat=Repeat(1, fixed=[_F("start", 2), _F("stop", 2),
                                                   _F("rgflgs", 1), _F("repeat", 2)],
                                         triplets=False)),
    "MDR": Layout("modca", repeat=Repeat(2, triplets=True)),
    "MCD": Layout("modca", repeat=Repeat(2, triplets=True)),
    "MMT": Layout("modca", repeat=Repeat(2, triplets=True)),
    "MPG": Layout("modca", repeat=Repeat(2, triplets=True)),
    "MPO": Layout("modca", repeat=Repeat(2, triplets=True)),
    "MMO": Layout("modca", repeat=Repeat(2, triplets=True)),
    "MPS": Layout("modca", repeat=Repeat(2, triplets=True)),
    "MGO": Layout("modca", repeat=Repeat(2, triplets=True)),
    "MIO": Layout("modca", repeat=Repeat(2, triplets=True)),
    "MBC": Layout("modca", repeat=Repeat(2, triplets=True)),
    "MCA": Layout("modca", repeat=Repeat(2, triplets=True)),
    "MSU": Layout("modca", triplets=True),
    # --- controls / misc ---
    "MFC": Layout("modca", triplets=True),
    "PMC": Layout("modca", [_F("flags", 1)], triplets=True),
    "PFC": Layout("modca", [_F("flags", 1)], triplets=True),
    "CAT": Layout("modca", triplets=True),
    "TLE": Layout("modca", triplets=True),
    "IEL": Layout("modca", triplets=True),
    "LLE": Layout("modca", triplets=True),
    "NOP": Layout("modca", [_F("comment", "rest", "bytes")]),
    "OCD": Layout("modca", raw=True),
    "PPO": Layout("modca", triplets=True),
    # --- FOCA (font) ---
    "BCF": Layout("foca", [_NAME], triplets=True),
    "BCP": Layout("foca", [_NAME], triplets=True),
    "BFN": Layout("foca", [_NAME], triplets=True),
    "ECF": Layout("foca", [_NAME], triplets=True),
    "ECP": Layout("foca", [_NAME], triplets=True),
    "EFN": Layout("foca", [_NAME], triplets=True),
    "CFC": Layout("foca", raw=True),
    "CPC": Layout("foca", raw=True),
    "CPD": Layout("foca", raw=True),
    "CPI": Layout("foca", raw=True),
    "FNC": Layout("foca", raw=True),
    "FND": Layout("foca", raw=True),
    "FNG": Layout("foca", raw=True),
    "FNI": Layout("foca", raw=True),
    "FNM": Layout("foca", raw=True),
    "FNN": Layout("foca", raw=True),
    "FNO": Layout("foca", raw=True),
    "FNP": Layout("foca", raw=True),
    "CFI": Layout("foca", raw=True),
    # --- object content (opaque) ---
    "GAD": Layout("goca", raw=True),
    "IPD": Layout("ioca", raw=True),
    "BDA": Layout("bcoca", raw=True),
    # --- presentation text content (opaque; parsed by the PTOCA record class) ---
    "PTX": Layout("ptoca", raw=True),
}

# Default: opaque. Triplet/field decoding only happens for records with an explicit
# layout, so content records (PTX, GOCA/IOCA data) are never mis-read as triplets.
_DEFAULT_LAYOUT = Layout("modca", raw=True)
