""" Render barcodes onto a ReportLab canvas for the PDF writer.

Maps model barcode symbology names to ReportLab barcode widgets and draws them scaled
into the element's box. Supported: Code 39 (3of9), Code 128 (incl. 128C), Code 93,
QR, DataMatrix (ECC200), USPS 4-State, and OMR timing marks. Unknown symbologies fall
back to a framed human-readable value.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

# Normalized symbology name -> ReportLab createBarcodeDrawing type.
_RL_TYPES = {
    "code39": "Standard39", "3of9": "Standard39", "39": "Standard39",
    "ext39": "Extended39",
    "code128": "Code128", "128": "Code128", "128a": "Code128",
    "128b": "Code128", "128c": "Code128",
    "code93": "Standard93", "93": "Standard93",
    "qr": "QR", "qrcode": "QR",
    "datamatrix": "ECC200DataMatrix", "ecc200": "ECC200DataMatrix", "2d": "QR",
    "usps": "USPS_4State", "imb": "USPS_4State",
}


def supported():
    return sorted(set(_RL_TYPES) | {"omr"})


def render(c, symbology, data, params, x, y, w, h):
    """ Draw a barcode in the box (x, y, w, h) in canvas (bottom-left) coordinates. """
    sym = (symbology or "code128").lower()
    if sym == "omr":
        return _render_omr(c, data, params or {}, x, y, w, h)
    rl_type = _RL_TYPES.get(sym)
    if rl_type is None:
        return False
    try:
        from reportlab.graphics.barcode import createBarcodeDrawing
        from reportlab.graphics import renderPDF
        opts = {"value": str(data)}
        if rl_type in ("Standard39", "Extended39", "Code128", "Standard93"):
            opts["barHeight"] = h
            opts["humanReadable"] = bool((params or {}).get("hri", True))
        drawing = createBarcodeDrawing(rl_type, **opts)
        sx = w / drawing.width if drawing.width else 1.0
        sy = h / drawing.height if drawing.height else 1.0
        c.saveState()
        c.translate(x, y)
        c.scale(sx, sy)
        renderPDF.draw(drawing, c, 0, 0)
        c.restoreState()
        return True
    except Exception as exc:
        logger.debug("Barcode %s render failed: %s", symbology, exc)
        return False


def _render_omr(c, data, params, x, y, w, h):
    """ OMR timing marks: one horizontal bar per '1' in the data bit string.

    ``data`` is a bit string (e.g. "10110"); ``params`` may set ``mark_height`` and
    ``pitch`` (points). Marks fill the box top-to-bottom.
    """
    bits = [ch for ch in str(data) if ch in "01"]
    if not bits:
        return False
    mark_h = float(params.get("mark_height") or 2.0)
    pitch = float(params.get("pitch") or max(h / max(len(bits), 1), mark_h * 2))
    c.saveState()
    c.setFillColorRGB(0, 0, 0)
    for i, bit in enumerate(bits):
        if bit == "1":
            my = y + h - (i + 1) * pitch
            c.rect(x, my, w, mark_h, stroke=0, fill=1)
    c.restoreState()
    return True
