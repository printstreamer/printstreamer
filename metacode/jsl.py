""" Parse a Xerox JSL (Job Source Library) into the settings Metacode needs.

A JSL/JDL defines the print environment a Metacode/LCDS stream depends on: the DJDE
prefix and scanning rules (IDEN), page geometry and font assignments (PDE), and the
job descriptor (JDE). Metacode records carry no self-describing geometry, so these
settings are required to parse or generate a stream faithfully.

This is a tolerant reader: JSL is a sequence of ``[label:] COMMAND operand,operand;``
statements. We split on ``;``, pull out the statements we care about
(IDEN/PDE/FONTS/JDE/FORMAT), parse ``KEY=VALUE`` and ``KEY=(a,b,...)`` operands, and
ignore everything else. Anything missing falls back to standard LPS defaults.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# Standard Xerox LPS defaults (used when the JSL is silent on a setting).
DEFAULT_DJDE_PREFIX = "$DJDE$"
DEFAULT_DPI = 300
DEFAULT_ENCODING = "cp500"          # EBCDIC
# Default font index -> point size, matching metacode.parser's historical defaults.
DEFAULT_FONT_SIZES = {0: 10.0, 1: 12.0, 2: 8.0, 3: 14.0}


@dataclass
class JslConfig:
    """ The Metacode-relevant settings distilled from a JSL. """
    djde_prefix: str = DEFAULT_DJDE_PREFIX
    djde_offset: int = 0
    djde_skip: int = 0
    page_width: float = 612.0           # points
    page_height: float = 792.0          # points
    orientation: str = "portrait"
    dpi: int = DEFAULT_DPI
    encoding: str = DEFAULT_ENCODING
    fonts: list = field(default_factory=list)        # ordered font names from PDE FONTS
    font_sizes: dict = field(default_factory=lambda: dict(DEFAULT_FONT_SIZES))
    source: str | None = None           # path the config was loaded from

    def djde_prefix_bytes(self, encoding=None) -> bytes:
        return self.djde_prefix.encode(encoding or self.encoding, "replace")


def _operands(text: str) -> dict:
    """ Parse ``KEY=VALUE`` / ``KEY=(a,b,...)`` operands from one statement body. """
    out = {}
    # KEY=(...) groups first, then simple KEY=VALUE (value stops at comma).
    for key, group in re.findall(r"([A-Za-z][A-Za-z0-9]*)\s*=\s*\(([^)]*)\)", text):
        out[key.upper()] = [v.strip().strip("'\"") for v in group.split(",") if v.strip()]
    for key, val in re.findall(r"([A-Za-z][A-Za-z0-9]*)\s*=\s*([^,();]+)", text):
        key = key.upper()
        if key not in out:                       # don't clobber a parsed group
            out[key] = val.strip().strip("'\"")
    return out


def _to_float(v, default):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def parse_jsl(text: str) -> JslConfig:
    """ Parse JSL source text into a :class:`JslConfig`. """
    cfg = JslConfig()
    # Strip $$$ ... and * ... comment lines, then split into statements on ';'.
    lines = []
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("$$$") or s.startswith("*"):
            continue
        lines.append(line)
    body = "\n".join(lines)
    for raw in body.split(";"):
        stmt = raw.strip()
        if not stmt:
            continue
        # Drop an optional "label:" prefix, then take the first word as the command.
        after_label = stmt.split(":", 1)[1] if ":" in stmt.split("=", 1)[0] else stmt
        words = after_label.split(None, 1)
        if not words:
            continue
        cmd = words[0].upper()
        ops = _operands(after_label)
        if cmd == "IDEN":
            if "PREFIX" in ops:
                cfg.djde_prefix = ops["PREFIX"] if isinstance(ops["PREFIX"], str) else cfg.djde_prefix
            cfg.djde_offset = int(_to_float(ops.get("OFFSET"), cfg.djde_offset))
            cfg.djde_skip = int(_to_float(ops.get("SKIP"), cfg.djde_skip))
        elif cmd == "PDE":
            if "RESOLUTION" in ops:
                cfg.dpi = int(_to_float(ops["RESOLUTION"], cfg.dpi))
            if "PMODE" in ops and isinstance(ops["PMODE"], str):
                cfg.orientation = ops["PMODE"].lower()
            if "PAPERSIZE" in ops and isinstance(ops["PAPERSIZE"], list) and len(ops["PAPERSIZE"]) >= 2:
                cfg.page_width = _to_float(ops["PAPERSIZE"][0], 8.5) * 72.0
                cfg.page_height = _to_float(ops["PAPERSIZE"][1], 11.0) * 72.0
        if "FONTS" in ops:                        # appears on PDE and JDE
            names = ops["FONTS"] if isinstance(ops["FONTS"], list) else [ops["FONTS"]]
            if names and not cfg.fonts:
                cfg.fonts = names
    # If the JSL listed fonts, size them by index using the standard size ladder.
    if cfg.fonts:
        ladder = [12.0, 10.0, 8.0, 14.0, 9.0, 11.0]
        cfg.font_sizes = {i: ladder[i % len(ladder)] for i in range(len(cfg.fonts))}
    return cfg


def load_jsl(path: str) -> JslConfig:
    """ Load and parse a JSL file. """
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        cfg = parse_jsl(fh.read())
    cfg.source = path
    return cfg


def default_jsl_path() -> str | None:
    """ Path to the bundled config/metacode.jsl, or None if it is not present. """
    import os
    from paths import PROJECT_ROOT
    path = os.path.join(PROJECT_ROOT, "config", "metacode.jsl")
    return path if os.path.exists(path) else None
