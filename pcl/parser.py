""" Parse PCL5 into model pages via an escape-sequence state machine. """

from __future__ import annotations

import logging

import fontmetrics
from model.element import TextElement
from model.geometry import Color, Point, Rect

logger = logging.getLogger(__name__)

ESC = 0x1B
_POINTS_PER_DOT = 72.0 / 300.0      # default PCL unit resolution: 300 dpi
_POINTS_PER_DECIPOINT = 0.1         # 1 decipoint = 1/720 inch = 0.1 pt


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

    # -- driving ----------------------------------------------------------

    def parse(self, data: bytes):
        i = 0
        n = len(data)
        run = bytearray()
        while i < n:
            b = data[i]
            if b == ESC:
                self._flush(run)
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
            value = float(num) if num not in ("", "+", "-", ".") else 0.0
            self._command(param, group, chr(cmd).upper(), value)
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
