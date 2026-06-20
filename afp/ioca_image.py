""" Decode IOCA image content into a renderable raster (PNG bytes).

AFP IOCA images are commonly bilevel and compressed (IBM MMR / CCITT G4 or G3). To
render real pixels we wrap the compressed strip in a minimal in-memory TIFF and let
Pillow decode it, then re-encode as PNG. JPEG-coded images are returned as-is.
Unsupported codecs return None so callers can fall back to an outline.
"""

from __future__ import annotations

import io
import logging
import struct

logger = logging.getLogger(__name__)

# IOCA compression id -> TIFF Compression tag (3 = CCITT G3/T.4, 4 = CCITT G4/T.6).
_TIFF_COMPRESSION = {
    0x01: 4,    # IBM MMR (~ T.6 / G4)
    0x06: 4,    # G4 (T.6)
    0x03: 3,    # G3 MH (T.4)
    0x04: 3,    # G3 MR (T.4)
    0x80: 4,
    0x82: 4,
}


def _compression_id(encoding):
    if encoding and encoding.startswith("ioca-"):
        try:
            return int(encoding.split("-")[1], 16)
        except ValueError:
            return None
    return None


def _build_tiff(width, height, data, compression_tag):
    """ Build a minimal single-strip little-endian TIFF around a compressed strip. """
    tags = [
        (256, 4, width),                # ImageWidth
        (257, 4, height),               # ImageLength
        (258, 3, 1),                    # BitsPerSample
        (259, 3, compression_tag),      # Compression
        (262, 3, 0),                    # PhotometricInterpretation: WhiteIsZero
        (273, 4, 0),                    # StripOffsets (patched below)
        (277, 3, 1),                    # SamplesPerPixel
        (278, 4, height),               # RowsPerStrip
        (279, 4, len(data)),            # StripByteCounts
    ]
    count = len(tags)
    ifd_offset = 8
    data_offset = ifd_offset + 2 + count * 12 + 4
    out = bytearray()
    out += b"II" + struct.pack("<HI", 42, ifd_offset)
    out += struct.pack("<H", count)
    for tag, typ, value in tags:
        if tag == 273:
            value = data_offset
        out += struct.pack("<HHI", tag, typ, 1)
        out += struct.pack("<I", value) if typ == 4 else struct.pack("<HH", value, 0)
    out += struct.pack("<I", 0)         # next IFD = none
    out += data
    return bytes(out)


def ioca_to_png(data: bytes, width: int, height: int, encoding: str) -> bytes | None:
    """ Return PNG bytes for an IOCA image, or None if it cannot be decoded. """
    if not data:
        return None
    if data[:2] == b"\xff\xd8":          # already JPEG
        return data
    comp = _compression_id(encoding)
    tiff_comp = _TIFF_COMPRESSION.get(comp)
    if tiff_comp is None or not width or not height:
        return None
    try:
        from PIL import Image
        tiff = _build_tiff(width, height, data, tiff_comp)
        img = Image.open(io.BytesIO(tiff))
        img.load()
        buf = io.BytesIO()
        img.convert("L").save(buf, format="PNG")
        return buf.getvalue()
    except Exception as exc:
        logger.debug("IOCA decode failed (%s): %s", encoding, exc)
        return None
