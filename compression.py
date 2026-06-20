""" Output compression with a normalized 0-10 level (0 = none).

The normalized level is mapped onto the chosen codec's native range so callers do
not have to know codec specifics. gzip/zlib are built in; extend ``_CODECS`` for more.
"""

import gzip
import zlib


def _scale(level, lo, hi):
    """ Map a 0-10 request onto [lo, hi]. """
    level = max(0, min(10, int(level)))
    return round(lo + (hi - lo) * level / 10)


def compress(data: bytes, codec: str = "gzip", level: int = 6) -> bytes:
    if level <= 0 or codec in (None, "", "none"):
        return data
    if codec == "gzip":
        return gzip.compress(data, compresslevel=_scale(level, 1, 9))
    if codec == "zlib":
        return zlib.compress(data, level=_scale(level, 1, 9))
    raise ValueError(f"Unknown compression codec: {codec!r}")


def suffix(codec: str, level: int) -> str:
    if level <= 0 or codec in (None, "", "none"):
        return ""
    return {"gzip": ".gz", "zlib": ".zz"}.get(codec, "")


def write_file(path: str, data: bytes, codec: str = "none", level: int = 0) -> str:
    """ Write ``data`` to ``path``, optionally compressed. Returns the path written. """
    out_path = path + suffix(codec, level)
    with open(out_path, "wb") as fh:
        fh.write(compress(data, codec=codec, level=level))
    return out_path


def decompress(data: bytes) -> bytes:
    """ Decompress gzip/zlib data; return as-is if it is not compressed. """
    if data[:2] == b"\x1f\x8b":            # gzip magic
        return gzip.decompress(data)
    try:
        return zlib.decompress(data)
    except zlib.error:
        return data


def read_file(path: str) -> bytes:
    """ Read a file, transparently decompressing gzip/zlib content. """
    with open(path, "rb") as fh:
        return decompress(fh.read())
