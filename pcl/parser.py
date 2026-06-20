""" Parse PCL into model pages via an escape-sequence state machine.

Handles the PCL5 text/cursor subset, plus the constructs that show up in real-world
files: PJL job wrappers (skipped), embedded HP-GL/2 vector blocks (parsed to graphics),
and PCL raster graphics (consumed by length and modelled as an image). Numeric parsing
is tolerant so binary payloads can never crash the parser.
"""

from __future__ import annotations

import logging
import re

import fontmetrics
from model.element import ContainerElement, GraphicElement, DrawOp, ImageElement, TextElement
from model.geometry import Color, Point, Rect

logger = logging.getLogger(__name__)

ESC = 0x1B
_POINTS_PER_DOT = 72.0 / 300.0      # default PCL unit resolution: 300 dpi
_POINTS_PER_DECIPOINT = 0.1         # 1 decipoint = 1/720 inch = 0.1 pt
_POINTS_PER_HPGL = 72.0 / 1016.0    # 1 HP-GL/2 plotter unit = 1/1016 inch


def _to_float(num: str) -> float:
    """ Parse a PCL numeric run, tolerating malformed input (binary bytes). """
    try:
        return float(num)
    except (TypeError, ValueError):
        return 0.0


class PCLParser:
    """ Interpret PCL bytes, emitting pages through ``on_page(width, height, elements)``. """

    def __init__(self, on_page, page_width=612.0, page_height=792.0):
        self.on_page = on_page
        self.page_width = page_width
        self.page_height = page_height
        self.reset_state()

    def reset_state(self):
        self.x = 0.0                 # cursor, in points, top-left origin
        self.y = 0.0
        self.left_margin = 0.0
        self.top_margin = 0.0
        self.font_size = 12.0
        self.bold = False
        self.italic = False
        self.color = Color.rgb(0, 0, 0)
        self.elements = []
        self._page_open = False
        # mode flags / pending state
        self._pjl = False            # inside a PJL block (skip until next ESC)
        self._hpgl = False           # inside an HP-GL/2 block
        self._consume = 0            # bytes of binary payload to skip after a command
        # raster graphics state
        self._raster = False
        self._raster_rows = 0
        self._raster_width = 0       # widest transferred row, in bytes
        self._raster_res = 300
        # HP-GL/2 pen state
        self._pen_xy = (0.0, 0.0)
        self._pen_down = False
        self._pen_abs = True
        self._stroke = None

    # -- driving ----------------------------------------------------------

    def parse(self, data: bytes):
        i = 0
        n = len(data)
        run = bytearray()
        while i < n:
            b = data[i]
            if self._pjl and b != ESC:
                i += 1               # discard PJL header text until the next escape
                continue
            if self._hpgl and b != ESC:
                j = data.find(b"\x1b", i)
                j = n if j < 0 else j
                self._hpgl_block(data[i:j])
                i = j
                continue
            if b == ESC:
                self._flush(run)
                self._pjl = False    # any escape ends a PJL block
                i = self._escape(data, i + 1)
            elif b in (0x0C, 0x0D, 0x0A):
                self._flush(run)
                self._control(b)
                i += 1
            elif b >= 0x20:
                run.append(b)
                i += 1
            else:
                i += 1
        self._flush(run)
        if self._page_open:
            self._finish_page()

    def _control(self, b):
        if b == 0x0D:                # CR
            self.x = self.left_margin
        elif b == 0x0A:              # LF
            self.y += self.font_size * 1.2
        elif b == 0x0C:              # FF: eject the page if one is open
            if self._page_open:
                self._finish_page()
            self.y = self.top_margin

    def _flush(self, run):
        if not run:
            return
        text = run.decode("latin-1", "replace")
        run.clear()
        base = fontmetrics.base_font("sans", self.bold, self.italic)
        width = fontmetrics.width(text, base, self.font_size)
        self._add(TextElement(
            text=text, position=Point(self.x, self.y + self.font_size),
            font_size=self.font_size, color=self.color, font_ref=base,
            bbox=Rect(self.x, self.y, width, self.font_size)))
        self.x += width

    def _add(self, element):
        if not self._page_open:
            self.elements = []
            self._page_open = True
        element.z_order = len(self.elements)
        self.elements.append(element)

    def _finish_page(self):
        self.on_page(self.page_width, self.page_height, self.elements)
        self.elements = []
        self._page_open = False

    # -- escape sequences -------------------------------------------------

    def _escape(self, data, i):
        n = len(data)
        if i >= n:
            return i
        first = data[i]
        # Two-character sequence, e.g. ESC E (reset). A reset ends the job, so eject
        # any page in progress before clearing state.
        if 0x30 <= first <= 0x7E:
            if first == ord("E"):
                if self._page_open:
                    self._finish_page()
                self.reset_state()
            return i + 1
        # Parameterized sequence: ESC p g [value cmd]...  (cmd uppercase ends).
        param = chr(first)
        i += 1
        group = chr(data[i]) if i < n and 0x60 <= data[i] <= 0x7E else ""
        if group:
            i += 1
        while i < n:
            num = ""
            while i < n and (data[i] in (0x2B, 0x2D, 0x2E) or 0x30 <= data[i] <= 0x39):
                num += chr(data[i]); i += 1
            if i >= n:
                break
            cmd = data[i]; i += 1
            value = _to_float(num)
            self._command(param, group, chr(cmd).upper(), value)
            if self._consume:                # binary payload follows this command
                skip = min(self._consume, n - i)
                i += skip
                self._consume = 0
            if 0x40 <= cmd <= 0x5E:          # uppercase terminates the sequence
                break
        return i

    def _command(self, param, group, cmd, value):
        if param == "*" and group == "p":
            if cmd == "X":
                self.x = value * _POINTS_PER_DOT
            elif cmd == "Y":
                self.y = value * _POINTS_PER_DOT
        elif param == "&" and group == "a":
            if cmd == "H":
                self.x = value * _POINTS_PER_DECIPOINT
            elif cmd == "V":
                self.y = value * _POINTS_PER_DECIPOINT
            elif cmd == "C":                 # column -> approximate by font width
                self.x = self.left_margin + value * self.font_size * 0.5
            elif cmd == "R":                 # row -> line height
                self.y = self.top_margin + value * self.font_size * 1.2
        elif param in "()" and group == "s":
            if cmd == "V":
                self.font_size = value       # font height in points
            elif cmd == "B":
                self.bold = value > 0
            elif cmd == "S":
                self.italic = value != 0
        elif param == "&" and group == "l":
            if cmd == "D" and value:          # lines per inch -> line height
                pass
        elif param == "%":
            # ESC %-12345X = PJL Universal Exit Language; ESC %#B / %#A enter/exit HP-GL/2.
            if cmd == "X" and value < 0:
                self._pjl = True
            elif cmd == "B":
                self._hpgl = True
                self._pen_xy = (0.0, 0.0); self._pen_down = False; self._pen_abs = True
            elif cmd == "A":
                self._hpgl = False
        elif param == "*" and group == "t":
            if cmd == "R":                    # raster resolution (dpi)
                self._raster_res = int(value) or 300
        elif param == "*" and group == "r":
            if cmd == "A":                    # start raster graphics
                self._raster = True
                self._raster_rows = 0
                self._raster_width = 0
            elif cmd in ("B", "C"):           # end raster graphics -> emit image
                self._finish_raster()
        elif param == "*" and group == "b":
            if cmd in ("W", "V"):             # transfer raster row: <value> bytes follow
                self._consume = int(value) if value > 0 else 0
                if self._raster:
                    self._raster_rows += 1
                    self._raster_width = max(self._raster_width, int(value))

    def _finish_raster(self):
        """ Model a completed raster block as a placed image (dimensions from the rows
        transferred). Pixel decode is intentionally out of scope; the element preserves
        placement and size so the page is represented rather than dropped. """
        if not self._raster:
            return
        self._raster = False
        if self._raster_rows <= 0:
            return
        res = self._raster_res or 300
        w_pt = (self._raster_width * 8) * 72.0 / res
        h_pt = self._raster_rows * 72.0 / res
        self._add(ImageElement(
            bbox=Rect(self.x, self.y, w_pt or 1.0, h_pt or 1.0),
            encoding="pcl-raster",
            attributes={"rows": self._raster_rows, "row_bytes": self._raster_width,
                        "resolution": res}))

    # -- HP-GL/2 ----------------------------------------------------------

    def _hpgl_point(self, ux, uy):
        """ HP-GL plotter units -> model points (top-left origin). """
        return (ux * _POINTS_PER_HPGL, self.page_height - uy * _POINTS_PER_HPGL)

    def _hpgl_block(self, chunk: bytes):
        """ Parse a minimal HP-GL/2 pen-plotting subset into graphic/text elements.

        Drawings that use the compact PE (Polyline Encoded) / polygon-fill encoding are
        beyond this subset; rather than drop them, the block is preserved as a container
        so the page is still represented. """
        before = len(self.elements)
        text = chunk.decode("latin-1", "replace")
        for mnem, args in re.findall(r"([A-Za-z]{2})([^A-Za-z;]*)", text):
            mnem = mnem.upper()
            nums = [_to_float(v) for v in re.findall(r"-?\d*\.?\d+", args)]
            if mnem in ("PA", "PD", "PU", "PR"):
                if mnem == "PR":
                    self._pen_abs = False
                elif mnem == "PA":
                    self._pen_abs = True
                pen_down = self._pen_down if mnem in ("PA", "PR") else (mnem == "PD")
                self._hpgl_move(nums, pen_down)
                self._pen_down = pen_down
            elif mnem == "SP":               # select pen -> a colour
                self._stroke = Color.rgb(0, 0, 0) if not nums or nums[0] else None
            elif mnem == "LB":               # label text at the pen position
                px, py = self._pen_xy
                base = fontmetrics.base_font("sans")
                self._add(TextElement(
                    text=args.split("\x03")[0], position=Point(px, py),
                    font_size=self.font_size, color=Color.rgb(0, 0, 0), font_ref=base,
                    bbox=Rect(px, py - self.font_size, 0, self.font_size)))
            # IN/DT/SI/etc.: ignored (no geometry contribution)
        # PE/PM/FP-encoded artwork yields no points above: preserve it so the page
        # is represented and the data is not silently dropped.
        if len(self.elements) == before and re.search(r"\b(PE|PM|FP|RF|PD|PA)\b", text):
            self._add(ContainerElement(preserved_type="hpgl2", raw=bytes(chunk),
                                       bbox=Rect(0, 0, self.page_width, self.page_height)))

    def _hpgl_move(self, nums, pen_down):
        """ Apply a run of (x, y) coordinate pairs, drawing a polyline when pen is down. """
        pts = []
        ux, uy = self._pen_xy_units()
        for k in range(0, len(nums) - 1, 2):
            if self._pen_abs:
                ux, uy = nums[k], nums[k + 1]
            else:
                ux, uy = ux + nums[k], uy + nums[k + 1]
            pts.append(self._hpgl_point(ux, uy))
        if pts:
            self._pen_xy = pts[-1]
            self._pen_units = (ux, uy)
            if pen_down and len(pts) >= 1:
                start = [self._last_pen_point] if getattr(self, "_last_pen_point", None) else []
                line = start + pts
                if len(line) >= 2:
                    self._add(GraphicElement(
                        ops=[DrawOp("polyline", line)],
                        stroke=self._stroke or Color.rgb(0, 0, 0),
                        bbox=Rect.from_corners(min(p.x for p in line), min(p.y for p in line),
                                               max(p.x for p in line), max(p.y for p in line))))
            self._last_pen_point = pts[-1]

    def _pen_xy_units(self):
        return getattr(self, "_pen_units", (0.0, 0.0))
