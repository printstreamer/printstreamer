""" Font metrics for precise text-run widths (R11).

The exact width of a text run is needed so the text element's window (bbox width) is
accurate for window-based extraction. Embedded FOCA metrics are used when present
(``FontResource.metrics``); otherwise we fall back to a real metrics engine
(reportlab ``stringWidth``) using a base font mapped from the AFP character-set name.
"""

from reportlab.pdfbase.pdfmetrics import stringWidth

# Base-14 fonts are always available in reportlab without registration.
_BASE_REGULAR = "Helvetica"
_BASE_BOLD = "Helvetica-Bold"
_BASE_ITALIC = "Helvetica-Oblique"


def base_font_for(charset_name: str | None) -> str:
    """ Map an AFP character-set / coded-font name to a base-14 reportlab font. """
    if not charset_name:
        return _BASE_REGULAR
    name = charset_name.upper()
    bold = any(tok in name for tok in ("BOLD", "B0", "DB", "BD"))
    italic = any(tok in name for tok in ("ITAL", "OBLI", "I0"))
    if bold:
        return _BASE_BOLD
    if italic:
        return _BASE_ITALIC
    return _BASE_REGULAR


_FAMILY_BASE = {
    "serif": "Times-Roman", "times": "Times-Roman", "roman": "Times-Roman",
    "sans": "Helvetica", "sans-serif": "Helvetica", "helvetica": "Helvetica",
    "arial": "Helvetica", "mono": "Courier", "monospace": "Courier",
    "courier": "Courier",
}
_FAMILY_VARIANTS = {
    "Times-Roman": ("Times-Roman", "Times-Bold", "Times-Italic", "Times-BoldItalic"),
    "Helvetica": ("Helvetica", "Helvetica-Bold", "Helvetica-Oblique", "Helvetica-BoldOblique"),
    "Courier": ("Courier", "Courier-Bold", "Courier-Oblique", "Courier-BoldOblique"),
}


def base_font(family: str | None, bold=False, italic=False) -> str:
    """ Resolve a font family + weight/style to a base-14 reportlab font name. """
    root = _FAMILY_BASE.get((family or "helvetica").strip().lower(), "Helvetica")
    regular, b, i, bi = _FAMILY_VARIANTS[root]
    if bold and italic:
        return bi
    if bold:
        return b
    if italic:
        return i
    return regular


def advance_1000(ch: str, base: str) -> float:
    """ Advance width of one character in 1/1000 em for a base font (== stringWidth at
    size 1000). This is the unit stored in ``FontResource.metrics``. """
    try:
        return stringWidth(ch, base, 1000)
    except Exception:
        return 500.0


def build_metrics(font) -> dict:
    """ Build a ``{unicode_codepoint: advance_1/1000em}`` table for a FontResource from
    its mapped base font, covering the characters the font's code page can represent.
    Used so every character's exact width is captured in the model (precise window
    extraction) and consistent on output. """
    base = getattr(font, "typeface", None) or base_font_for(getattr(font, "char_set", None))
    enc = getattr(font, "encoding_map", None) or {}
    chars = set(enc.values()) if enc else {chr(c) for c in range(32, 127)}
    metrics = {}
    for ch in chars:
        if ch:
            metrics[ord(ch)] = advance_1000(ch, base)
    return metrics


def width(text: str, base: str, size: float) -> float:
    """ Exact width of text in points for a named base font. """
    if not text:
        return 0.0
    try:
        return stringWidth(text, base, size)
    except Exception:
        return len(text) * size * 0.5


def char_advances(text: str, size: float, font=None) -> list:
    """ Per-character advance widths in points, using the font's captured metrics when
    present (else base-font glyph metrics). Used for precise sub-run window extraction. """
    if not text:
        return []
    metrics = getattr(font, "metrics", None) if font else None
    if metrics:
        return [metrics.get(ord(ch), 600) / 1000.0 * size for ch in text]
    base = base_font_for(getattr(font, "char_set", None) if font else None)
    out = []
    for ch in text:
        try:
            out.append(stringWidth(ch, base, size))
        except Exception:
            out.append(size * 0.5)
    return out


def text_width(text: str, size: float, font=None) -> float:
    """ Exact width of ``text`` in points at ``size`` for the given FontResource.

    If the font carries per-codepoint metrics (from FOCA), sum those; otherwise use
    reportlab glyph metrics for the mapped base font.
    """
    if not text:
        return 0.0
    if font is not None and getattr(font, "metrics", None):
        # metrics: codepoint -> advance in 1/1000 em; sum and scale by size.
        total = 0.0
        for ch in text:
            total += font.metrics.get(ord(ch), 600)
        return total / 1000.0 * size
    base = base_font_for(getattr(font, "char_set", None) if font else None)
    try:
        return stringWidth(text, base, size)
    except Exception:
        return len(text) * size * 0.5
