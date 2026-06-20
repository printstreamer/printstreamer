""" Geometry primitives for the generic model.

All coordinates are in points (1/72 inch) with the origin at the top-left of the
page and y increasing downward. Parsers/writers convert to/from this convention at
their boundary (see ``units`` for scale conversion).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field


@dataclass
class Point:
    """ A 2-D point in points. """
    x: float = 0.0
    y: float = 0.0


@dataclass
class Rect:
    """ An axis-aligned rectangle given by its top-left origin plus width/height.

    This is the shape used for "window" selection (x, y origin then width and
    height), as well as element bounding boxes and page sizes.
    """
    x: float = 0.0
    y: float = 0.0
    width: float = 0.0
    height: float = 0.0

    @property
    def x0(self) -> float:
        return self.x

    @property
    def y0(self) -> float:
        return self.y

    @property
    def x1(self) -> float:
        return self.x + self.width

    @property
    def y1(self) -> float:
        return self.y + self.height

    @classmethod
    def from_corners(cls, x0: float, y0: float, x1: float, y1: float) -> "Rect":
        return cls(min(x0, x1), min(y0, y1), abs(x1 - x0), abs(y1 - y0))

    def contains_point(self, px: float, py: float) -> bool:
        return self.x0 <= px <= self.x1 and self.y0 <= py <= self.y1

    def contains_rect(self, other: "Rect") -> bool:
        return (self.x0 <= other.x0 and self.y0 <= other.y0
                and self.x1 >= other.x1 and self.y1 >= other.y1)

    def intersects(self, other: "Rect") -> bool:
        return not (other.x0 > self.x1 or other.x1 < self.x0
                    or other.y0 > self.y1 or other.y1 < self.y0)


@dataclass
class Matrix:
    """ A 2-D affine transform [a b c d e f] mapping (x, y) ->
    (a*x + c*y + e, b*x + d*y + f). Used for placement, n-up imposition,
    rotation, and scaling of elements without touching their content.
    """
    a: float = 1.0
    b: float = 0.0
    c: float = 0.0
    d: float = 1.0
    e: float = 0.0
    f: float = 0.0

    @classmethod
    def identity(cls) -> "Matrix":
        return cls()

    @classmethod
    def translate(cls, dx: float, dy: float) -> "Matrix":
        return cls(1, 0, 0, 1, dx, dy)

    @classmethod
    def scale(cls, sx: float, sy: float | None = None) -> "Matrix":
        if sy is None:
            sy = sx
        return cls(sx, 0, 0, sy, 0, 0)

    @classmethod
    def rotate(cls, degrees: float) -> "Matrix":
        r = math.radians(degrees)
        cos, sin = math.cos(r), math.sin(r)
        return cls(cos, sin, -sin, cos, 0, 0)

    def multiply(self, other: "Matrix") -> "Matrix":
        """ Return self * other (apply ``other`` first, then ``self``). """
        return Matrix(
            self.a * other.a + self.c * other.b,
            self.b * other.a + self.d * other.b,
            self.a * other.c + self.c * other.d,
            self.b * other.c + self.d * other.d,
            self.a * other.e + self.c * other.f + self.e,
            self.b * other.e + self.d * other.f + self.f,
        )

    def apply(self, point: Point) -> Point:
        return Point(self.a * point.x + self.c * point.y + self.e,
                     self.b * point.x + self.d * point.y + self.f)

    def is_identity(self) -> bool:
        return (self.a, self.b, self.c, self.d, self.e, self.f) == (1, 0, 0, 1, 0, 0)


@dataclass
class Color:
    """ A colour in a named colour space.

    ``space`` is one of "rgb", "cmyk", "gray", or "named"; ``components`` holds the
    normalized channel values (0..1) for rgb/cmyk/gray, and ``name`` holds the token
    for named colours. Keeping the original space lets writers preserve fidelity
    (e.g. CMYK in AFP) rather than forcing an early conversion to RGB.
    """
    space: str = "rgb"
    components: tuple = field(default_factory=lambda: (0.0, 0.0, 0.0))
    name: str | None = None

    @classmethod
    def rgb(cls, r: float, g: float, b: float) -> "Color":
        return cls("rgb", (r, g, b))

    @classmethod
    def cmyk(cls, c: float, m: float, y: float, k: float) -> "Color":
        return cls("cmyk", (c, m, y, k))

    @classmethod
    def gray(cls, level: float) -> "Color":
        return cls("gray", (level,))

    @classmethod
    def named(cls, name: str) -> "Color":
        return cls("named", (), name)

    @classmethod
    def from_rgb_int(cls, value: int) -> "Color":
        """ Build from a packed 0xRRGGBB integer (PyMuPDF/PDF style). """
        return cls.rgb(((value >> 16) & 0xFF) / 255.0,
                       ((value >> 8) & 0xFF) / 255.0,
                       (value & 0xFF) / 255.0)

    def to_rgb(self) -> tuple:
        """ Best-effort conversion to an (r, g, b) tuple in 0..1. """
        if self.space == "rgb":
            return self.components
        if self.space == "gray":
            g = self.components[0]
            return (g, g, g)
        if self.space == "cmyk":
            c, m, y, k = self.components
            return ((1 - c) * (1 - k), (1 - m) * (1 - k), (1 - y) * (1 - k))
        if self.space == "named":
            return _NAMED_RGB.get((self.name or "").lower(), (0.0, 0.0, 0.0))
        return (0.0, 0.0, 0.0)


# A handful of standard named colours; extend as overlays/color tables need them.
_NAMED_RGB = {
    "black": (0.0, 0.0, 0.0),
    "white": (1.0, 1.0, 1.0),
    "red": (1.0, 0.0, 0.0),
    "green": (0.0, 1.0, 0.0),
    "blue": (0.0, 0.0, 1.0),
    "cyan": (0.0, 1.0, 1.0),
    "magenta": (1.0, 0.0, 1.0),
    "yellow": (1.0, 1.0, 0.0),
    "brown": (0.6, 0.4, 0.2),
}
