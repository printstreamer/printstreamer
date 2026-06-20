""" Geometry transforms for placing pages/elements onto other pages.

Shared by n-up imposition, label sheet generation, and merge/reorder. Because every
element carries a position/bbox in points, placing a source page onto a sub-rectangle
of an output page is a pure model transform: clone each element, scale it, and
translate it into the target cell. No format-specific code is involved.
"""

from __future__ import annotations

import copy

from model.document import Document, StreamDocumentSet
from model.element import ElementKind
from model.geometry import Point, Rect
from model.page import Page


def rotate_point(x, y, rot, w, h):
    """ Rotate a point in a w x h page (top-left origin, y down) by ``rot`` degrees
    clockwise, returning its coordinates in the rotated page. """
    rot %= 360
    if rot == 90:
        return h - y, x
    if rot == 180:
        return w - x, h - y
    if rot == 270:
        return y, w - x
    return x, y


def rotated_size(w, h, rot):
    return (h, w) if rot % 360 in (90, 270) else (w, h)


def _xp(p: Point, sx, sy, dx, dy, rot, w, h) -> Point:
    rx, ry = rotate_point(p.x, p.y, rot, w, h)
    return Point(dx + rx * sx, dy + ry * sy)


def transform_element(element, sx, sy, dx, dy, rot=0, page_w=0.0, page_h=0.0):
    """ Return a deep copy of ``element`` rotated by ``rot`` degrees within its
    page (page_w x page_h), then scaled by (sx, sy) and translated by (dx, dy). """
    el = copy.deepcopy(element)
    if el.bbox is not None:
        b = el.bbox
        c0 = _xp(Point(b.x, b.y), sx, sy, dx, dy, rot, page_w, page_h)
        c1 = _xp(Point(b.x1, b.y1), sx, sy, dx, dy, rot, page_w, page_h)
        el.bbox = Rect.from_corners(c0.x, c0.y, c1.x, c1.y)
    if el.kind == ElementKind.TEXT:
        el.position = _xp(el.position, sx, sy, dx, dy, rot, page_w, page_h)
        if el.font_size:
            el.font_size *= sy
        el.orientation = (el.orientation + rot) % 360
    elif el.kind == ElementKind.LINE:
        el.start = _xp(el.start, sx, sy, dx, dy, rot, page_w, page_h)
        el.end = _xp(el.end, sx, sy, dx, dy, rot, page_w, page_h)
        el.weight = (el.weight or 1.0) * sy
    elif el.kind == ElementKind.GRAPHIC:
        for op in el.ops:
            op.points = [_xp(p, sx, sy, dx, dy, rot, page_w, page_h) for p in op.points]
    return el


def place_page(dest: Page, src: Page, cell: Rect, *, scale=True, valign="top",
               halign="left", rotate=0, explicit_scale=None):
    """ Place a source page's content into ``cell`` on ``dest``.

    Rotated by ``rotate`` degrees (0/90/180/270). The scale is ``explicit_scale`` if
    given, else fit-to-cell when ``scale`` is true, else 1.0. ``halign``/``valign``
    position the (rotated, scaled) page within the cell. Returns the scale used.
    """
    sw = src.size.width or cell.width
    sh = src.size.height or cell.height
    rw, rh = rotated_size(sw, sh, rotate)
    if explicit_scale is not None:
        s = explicit_scale
    elif scale and rw and rh:
        s = min(cell.width / rw, cell.height / rh)
    else:
        s = 1.0
    dx, dy = cell.x, cell.y
    if halign == "center":
        dx += (cell.width - rw * s) / 2
    elif halign == "right":
        dx += cell.width - rw * s
    if valign == "center":
        dy += (cell.height - rh * s) / 2
    elif valign == "bottom":
        dy += cell.height - rh * s
    for element in src.ordered_elements():
        dest.add_element(transform_element(element, s, s, dx, dy, rotate, sw, sh))
    return s


_PAGE_SIZES = {
    "letter": (612, 792), "legal": (612, 1008), "a4": (595.28, 841.89),
    "a3": (841.89, 1190.55), "tabloid": (792, 1224), "ledger": (1224, 792),
}


def resolve_page_size(name, width=None, height=None) -> Rect:
    pw, ph = _PAGE_SIZES.get((name or "letter").lower(), _PAGE_SIZES["letter"])
    return Rect(0, 0, width or pw, height or ph)


def resolve_page_ref(ref, group, slot):
    """ Resolve a cell's page reference within a group of input pages.

    "auto" -> the cell's flow position (``slot``); "n" -> last page, "n-1" ->
    second-to-last, ...; an integer -> that 1-based page in the group. """
    ref = (ref or "auto").strip().lower()
    if ref == "auto":
        idx = slot
    elif ref == "n":
        idx = len(group) - 1
    elif ref.startswith("n-"):
        try:
            idx = len(group) - 1 - int(ref[2:])
        except ValueError:
            return None
    else:
        try:
            idx = int(ref) - 1
        except ValueError:
            return None
    return group[idx] if 0 <= idx < len(group) else None


def impose_spec(doc_set: StreamDocumentSet, imp) -> StreamDocumentSet:
    """ Impose pages onto sheets per an ImpositionSpec (process.spec.ImpositionSpec),
    honouring per-cell page references, rotation, scale, and alignment. """
    page_size = resolve_page_size(imp.page_size, imp.page_width, imp.page_height)
    cells = list(grid_cells(page_size, imp.rows, imp.cols, margin_top=imp.margin_top,
                            margin_left=imp.margin_left, h_gap=imp.h_gap, v_gap=imp.v_gap))
    group_size = imp.group_size or (imp.rows * imp.cols)
    out = StreamDocumentSet()
    doc = out.add_document(Document(name="imposed"))
    pages = doc_set.all_pages()
    for gi in range(0, len(pages), group_size):
        group = pages[gi:gi + group_size]
        sheet = doc.add_page(Page(number=len(doc.pages) + 1, size=page_size))
        if imp.cells:
            for cs in imp.cells:
                slot = cs.row * imp.cols + cs.col
                if not (0 <= slot < len(cells)):
                    continue
                src = resolve_page_ref(cs.page, group, slot)
                if src is None:
                    continue
                place_page(sheet, src, cells[slot],
                           scale=imp.scale, explicit_scale=cs.scale,
                           rotate=cs.rotate or imp.rotate,
                           halign=cs.halign, valign=cs.valign)
        else:
            for slot, src in enumerate(group[:len(cells)]):
                place_page(sheet, src, cells[slot], scale=imp.scale, rotate=imp.rotate)
    return out


def grid_cells(page_size: Rect, rows: int, cols: int, *, margin_top=0.0,
               margin_left=0.0, h_pitch=None, v_pitch=None,
               cell_width=None, cell_height=None, h_gap=0.0, v_gap=0.0):
    """ Yield Rect cells (row-major) for an n-up / label grid, in points. """
    if cell_width is None:
        cell_width = (page_size.width - 2 * margin_left - (cols - 1) * h_gap) / cols
    if cell_height is None:
        cell_height = (page_size.height - 2 * margin_top - (rows - 1) * v_gap) / rows
    if h_pitch is None:
        h_pitch = cell_width + h_gap
    if v_pitch is None:
        v_pitch = cell_height + v_gap
    for r in range(rows):
        for c in range(cols):
            yield Rect(margin_left + c * h_pitch, margin_top + r * v_pitch,
                       cell_width, cell_height)


def impose(doc_set: StreamDocumentSet, rows: int, cols: int, page_size: Rect,
           *, margin_top=0.0, margin_left=0.0, h_gap=0.0, v_gap=0.0,
           rotate=0, order="row") -> StreamDocumentSet:
    """ N-up: place ``rows*cols`` source pages onto each output page, each rotated by
    ``rotate`` degrees. """
    out = StreamDocumentSet()
    doc = out.add_document(Document(name="imposed"))
    cells = list(grid_cells(page_size, rows, cols, margin_top=margin_top,
                            margin_left=margin_left, h_gap=h_gap, v_gap=v_gap))
    per_sheet = rows * cols
    pages = doc_set.all_pages()
    for i in range(0, len(pages), per_sheet):
        sheet = doc.add_page(Page(number=len(doc.pages) + 1, size=page_size))
        for slot, src in enumerate(pages[i:i + per_sheet]):
            place_page(sheet, src, cells[slot], scale=True, rotate=rotate)
    return out
