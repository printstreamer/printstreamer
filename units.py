""" Measurement units and conversions for the generic model.

The generic model stores all geometry in **points** (1/72 inch) as floats, with the
page origin at the top-left corner. Each print-stream format measures in its own
units; convert at the parser/writer boundary using these helpers so that nothing in
the model or the processing layers has to know about format-specific units.

Common units:
- point    : 1/72 inch       (model canonical unit, also PDF user space)
- L-unit   : 1/1440 inch     (AFP, the usual 1440 dpi logical resolution)
- inch / mm : physical units for convenience
"""

POINTS_PER_INCH = 72.0
AFP_LUNITS_PER_INCH = 1440.0
MM_PER_INCH = 25.4


def afp_to_points(lunits, units_per_inch=AFP_LUNITS_PER_INCH):
    """ Convert AFP L-units to points.

    :param lunits: Measurement in AFP L-units (defaults assume 1440 units/inch)
    :param units_per_inch: L-units per inch as declared by the descriptor (e.g. PGD)
    :returns: Measurement in points (float)
    """
    return lunits * POINTS_PER_INCH / units_per_inch


def points_to_afp(points, units_per_inch=AFP_LUNITS_PER_INCH):
    """ Convert points to AFP L-units.

    :param points: Measurement in points
    :param units_per_inch: Target L-units per inch
    :returns: Measurement in L-units (rounded int)
    """
    return round(points * units_per_inch / POINTS_PER_INCH)


def inches_to_points(inches):
    """ Convert inches to points. """
    return inches * POINTS_PER_INCH


def points_to_inches(points):
    """ Convert points to inches. """
    return points / POINTS_PER_INCH


def mm_to_points(mm):
    """ Convert millimetres to points. """
    return mm / MM_PER_INCH * POINTS_PER_INCH


def points_to_mm(points):
    """ Convert points to millimetres. """
    return points / POINTS_PER_INCH * MM_PER_INCH


_LENGTH_FACTORS = {
    "pt": 1.0,
    "px": 1.0,                       # treat CSS px as points for print
    "in": POINTS_PER_INCH,
    "mm": POINTS_PER_INCH / MM_PER_INCH,
    "cm": POINTS_PER_INCH / MM_PER_INCH * 10,
    "pc": 12.0,                      # pica = 12 points
}


def parse_length(value, default=0.0):
    """ Parse a length string to points. Accepts a bare number (points) or a value
    with a unit suffix: pt, px, in, mm, cm, pc. Points are the canonical unit. """
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value).strip().lower()
    if not s:
        return default
    for suffix, factor in _LENGTH_FACTORS.items():
        if s.endswith(suffix):
            return float(s[:-len(suffix)].strip()) * factor
    return float(s)
