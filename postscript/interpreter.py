""" A small stack-based PostScript interpreter producing model pages. """

from __future__ import annotations

import logging
import re

import fontmetrics
from model.element import DrawOp, GraphicElement, LineElement, Point, TextElement
from model.geometry import Color, Rect

logger = logging.getLogger(__name__)

_TOKEN = re.compile(r"""
    (?P<ws>\s+)
  | (?P<comment>%[^\n]*)
  | (?P<string>\((?:[^()\\]|\\.)*\))
  | (?P<hexstring><[0-9A-Fa-f\s]*>)
  | (?P<proc>[{}])
  | (?P<array>[\[\]])
  | (?P<name>/?[^\s{}\[\]()<>%/]+)
""", re.VERBOSE)


def tokenize(text):
    pos = 0
    out = []
    n = len(text)
    while pos < n:
        m = _TOKEN.match(text, pos)
        if not m:
            pos += 1
            continue
        pos = m.end()
        kind = m.lastgroup
        if kind in ("ws", "comment"):
            continue
        out.append((kind, m.group()))
    return out


def _num(tok):
    try:
        return int(tok)
    except ValueError:
        try:
            return float(tok)
        except ValueError:
            return None


def _unescape(s):
    body = s[1:-1]
    return re.sub(r"\\(\d{1,3}|.)", lambda m: _esc(m.group(1)), body)


def _esc(seq):
    simple = {"n": "\n", "r": "\r", "t": "\t", "b": "\b", "f": "\f",
              "\\": "\\", "(": "(", ")": ")"}
    if seq in simple:
        return simple[seq]
    if seq.isdigit():
        return chr(int(seq, 8) & 0xFF)
    return seq


class GState:
    def __init__(self):
        self.x = 0.0
        self.y = 0.0
        self.font = "Helvetica"
        self.size = 12.0
        self.color = Color.rgb(0, 0, 0)
        self.line_width = 1.0
        # CTM as translate+scale (a, d, e, f); sufficient for typical print PS.
        self.sx = 1.0
        self.sy = 1.0
        self.tx = 0.0
        self.ty = 0.0

    def copy(self):
        g = GState()
        g.__dict__.update(self.__dict__)
        return g

    def dev(self, x, y):
        return (x * self.sx + self.tx, y * self.sy + self.ty)


class PSInterpreter:
    """ Interpret PostScript tokens, emitting pages through a sink.

    The sink receives ``begin_page(width, height)`` and element adds; ``end_page()``
    finalizes. Coordinates are converted from PostScript (bottom-left origin) to the
    model's top-left origin using the page height.
    """

    # Cap on nested procedure execution. Real-world prologues define procedures that
    # call procedures; pathological or self-referential definitions would otherwise
    # recurse until Python's stack overflows. We stop descending past this depth
    # (best-effort interpretation) so a deep/looping definition never crashes the parse.
    MAX_PROC_DEPTH = 120
    # Hard bounds so a large/pathological stream can never hang or exhaust memory:
    # interpretation stops after this many operators (best-effort, page is finalized),
    # and the operand stack is trimmed if it grows without bound (mis-tracked stacks).
    MAX_OPS = 1_000_000
    MAX_STACK = 100_000

    def __init__(self, on_page):
        self.on_page = on_page
        self.stack = []
        self.gstack = []
        self.gs = GState()
        self.defs = {}
        self.page_w = 612.0
        self.page_h = 792.0
        self.elements = []
        self.path = []          # list of subpaths; each is list of (x, y) device points
        self._page_open = False
        self._depth = 0         # current nested-procedure execution depth
        self._ops = 0           # operators executed (budget counter)

    # -- running ----------------------------------------------------------

    def run(self, text):
        self._scan_bbox(text)
        tokens = tokenize(text)
        i = 0
        while i < len(tokens) and self._ops <= self.MAX_OPS:
            i = self._exec(tokens, i)
        if self._ops > self.MAX_OPS:
            logger.warning("PostScript op budget (%d) reached; finalizing best-effort.",
                           self.MAX_OPS)
        if self._page_open:
            self._showpage()

    def _scan_bbox(self, text):
        m = re.search(r"%%(?:Page)?BoundingBox:\s*([\d.\- ]+)", text)
        if m:
            try:
                x0, y0, x1, y1 = (float(v) for v in m.group(1).split()[:4])
                self.page_w, self.page_h = x1 - x0, y1 - y0
            except ValueError:
                pass

    def _exec(self, tokens, i):
        self._ops += 1
        if self._ops > self.MAX_OPS:
            return len(tokens)              # budget exhausted: end this token list
        if len(self.stack) > self.MAX_STACK:
            del self.stack[:-1000]          # runaway stack (mis-tracked): keep the tail
        kind, tok = tokens[i]
        if kind == "string":
            self.stack.append(_unescape(tok))
        elif kind == "hexstring":
            self.stack.append(tok)
        elif kind == "proc" and tok == "{":
            proc, i = self._collect_proc(tokens, i + 1)
            self.stack.append(proc)
            return i
        elif kind == "array" and tok == "[":
            self.stack.append("[")
        elif kind == "array" and tok == "]":
            self._close_array()
        elif kind == "name":
            if tok.startswith("/"):
                self.stack.append(("name", tok[1:]))
            else:
                num = _num(tok)
                if num is not None:
                    self.stack.append(num)
                else:
                    self._operator(tok)
        return i + 1

    def _collect_proc(self, tokens, i):
        depth = 1
        body = []
        while i < len(tokens) and depth:
            kind, tok = tokens[i]
            if tok == "{":
                depth += 1
            elif tok == "}":
                depth -= 1
                if depth == 0:
                    break
            body.append((kind, tok))
            i += 1
        return ("proc", body), i + 1

    def _close_array(self):
        arr = []
        while self.stack and self.stack[-1] != "[":
            arr.append(self.stack.pop())
        if self.stack:
            self.stack.pop()
        self.stack.append(list(reversed(arr)))

    # -- operators --------------------------------------------------------

    def _operator(self, op):
        handler = getattr(self, f"op_{op}", None)
        if handler:
            handler()
        elif op in self.defs:
            self._run_proc(self.defs[op])
        # unknown operators are ignored (best-effort interpretation)

    def _run_proc(self, value):
        if isinstance(value, tuple) and value and value[0] == "proc":
            if self._depth >= self.MAX_PROC_DEPTH:
                return                      # too deep: stop (best-effort, never crash)
            self._depth += 1
            try:
                i = 0
                body = value[1]
                while i < len(body) and self._ops <= self.MAX_OPS:
                    i = self._exec(body, i)
            finally:
                self._depth -= 1
        else:
            self.stack.append(value)

    def _pop(self, n=1):
        vals = self.stack[-n:] if n else []
        del self.stack[-n:]
        return vals if n != 1 else (vals[0] if vals else None)

    def _fpop(self):
        """ Pop one operand coerced to float; 0.0 when the stack holds a non-number
        (stack imbalances are common in best-effort interpretation). """
        v = self._pop()
        return v if isinstance(v, (int, float)) else 0.0

    def _open_page(self):
        if not self._page_open:
            self.elements = []
            self._page_open = True

    def _showpage(self):
        self.on_page(self.page_w, self.page_h, self.elements)
        self.elements = []
        self._page_open = False

    def _add(self, element):
        self._open_page()
        self.elements.append(element)

    def _ty(self, y):
        return self.page_h - y          # PS bottom-left -> model top-left

    # path
    def op_newpath(self):
        self.path = []

    def op_moveto(self):
        y = self._fpop(); x = self._fpop()
        self.gs.x, self.gs.y = self.gs.dev(x, y)
        self.path.append([(self.gs.x, self.gs.y)])

    def op_rmoveto(self):
        dy = self._fpop(); dx = self._fpop()
        self.gs.x += dx * self.gs.sx
        self.gs.y += dy * self.gs.sy
        self.path.append([(self.gs.x, self.gs.y)])

    def op_lineto(self):
        y = self._fpop(); x = self._fpop()
        self.gs.x, self.gs.y = self.gs.dev(x, y)
        if not self.path:
            self.path.append([(self.gs.x, self.gs.y)])
        else:
            self.path[-1].append((self.gs.x, self.gs.y))

    def op_rlineto(self):
        dy = self._fpop(); dx = self._fpop()
        self.gs.x += dx * self.gs.sx
        self.gs.y += dy * self.gs.sy
        if self.path:
            self.path[-1].append((self.gs.x, self.gs.y))

    def op_closepath(self):
        if self.path and len(self.path[-1]) > 1:
            self.path[-1].append(self.path[-1][0])

    def op_stroke(self):
        for sub in self.path:
            for a, b in zip(sub, sub[1:]):
                self._add(LineElement(
                    start=Point(a[0], self._ty(a[1])), end=Point(b[0], self._ty(b[1])),
                    weight=self.gs.line_width, color=self.gs.color,
                    bbox=Rect.from_corners(a[0], self._ty(a[1]), b[0], self._ty(b[1]))))
        self.path = []

    def op_fill(self):
        for sub in self.path:
            if len(sub) >= 2:
                pts = [Point(x, self._ty(y)) for x, y in sub]
                xs = [p.x for p in pts]; ys = [p.y for p in pts]
                self._add(GraphicElement(
                    ops=[DrawOp("polyline", pts)], fill=self.gs.color,
                    bbox=Rect.from_corners(min(xs), min(ys), max(xs), max(ys))))
        self.path = []

    def op_rectfill(self):
        h = self._fpop(); w = self._fpop(); y = self._fpop(); x = self._fpop()
        x0, y0 = self.gs.dev(x, y)
        self._add(GraphicElement(
            ops=[DrawOp("box", [Point(x0, self._ty(y0 + h * self.gs.sy)),
                                Point(x0 + w * self.gs.sx, self._ty(y0))])],
            fill=self.gs.color, bbox=Rect(x0, self._ty(y0 + h * self.gs.sy),
                                          w * self.gs.sx, h * self.gs.sy)))

    def op_rectstroke(self):
        h = self._fpop(); w = self._fpop(); y = self._fpop(); x = self._fpop()
        x0, y0 = self.gs.dev(x, y)
        self._add(GraphicElement(
            ops=[DrawOp("box", [Point(x0, self._ty(y0 + h * self.gs.sy)),
                                Point(x0 + w * self.gs.sx, self._ty(y0))])],
            stroke=self.gs.color, bbox=Rect(x0, self._ty(y0 + h * self.gs.sy),
                                            w * self.gs.sx, h * self.gs.sy)))

    # colour
    def op_setrgbcolor(self):
        b = self._fpop(); g = self._fpop(); r = self._fpop()
        self.gs.color = Color.rgb(r, g, b)

    def op_setgray(self):
        self.gs.color = Color.gray(self._fpop())

    def op_sethsbcolor(self):
        self._pop(3)        # not modelled precisely; keep current colour

    def op_setlinewidth(self):
        self.gs.line_width = self._fpop() * self.gs.sx

    # fonts / text
    def op_findfont(self):
        name = self._pop()
        fname = name[1] if isinstance(name, tuple) else str(name)
        self.stack.append({"font": fname, "size": 1.0})

    def op_scalefont(self):
        size = self._fpop(); fd = self._pop()
        if isinstance(fd, dict):
            fd = dict(fd); fd["size"] = size
            self.stack.append(fd)
        else:
            self.stack.append({"font": "Helvetica", "size": size})

    def op_setfont(self):
        fd = self._pop()
        if isinstance(fd, dict):
            self.gs.font = fd.get("font", "Helvetica")
            self.gs.size = fd.get("size", 12.0) * self.gs.sy

    def _base_font(self):
        name = self.gs.font.lower()
        bold = "bold" in name
        italic = "italic" in name or "oblique" in name
        if "times" in name or "serif" in name:
            fam = "serif"
        elif "courier" in name or "mono" in name:
            fam = "mono"
        else:
            fam = "sans"
        return fontmetrics.base_font(fam, bold, italic)

    def op_show(self):
        s = self._pop()
        if not isinstance(s, str):
            return
        base = self._base_font()
        self._add(TextElement(
            text=s, position=Point(self.gs.x, self._ty(self.gs.y)),
            font_size=self.gs.size, color=self.gs.color, font_ref=base,
            bbox=Rect(self.gs.x, self._ty(self.gs.y) - self.gs.size,
                      fontmetrics.width(s, base, self.gs.size), self.gs.size)))
        self.gs.x += fontmetrics.width(s, base, self.gs.size)

    def op_ashow(self):
        s = self._pop(); self._pop(2)        # ax ay (string) ashow
        self.stack.append(s)
        self.op_show()

    def op_showpage(self):
        self._showpage()

    # graphics state
    def op_gsave(self):
        self.gstack.append(self.gs.copy())

    def op_grestore(self):
        if self.gstack:
            self.gs = self.gstack.pop()

    def op_translate(self):
        ty = self._fpop(); tx = self._fpop()
        self.gs.tx += tx * self.gs.sx
        self.gs.ty += ty * self.gs.sy

    def op_scale(self):
        sy = self._fpop(); sx = self._fpop()
        self.gs.sx *= sx or 1.0
        self.gs.sy *= sy or 1.0

    # definitions
    def op_def(self):
        value = self._pop(); key = self._pop()
        if isinstance(key, tuple) and key[0] == "name":
            self.defs[key[1]] = value

    def op_bind(self):
        pass        # leave procedures as-is

    def op_dup(self):
        if self.stack:
            self.stack.append(self.stack[-1])

    def op_pop(self):
        self._pop()

    def op_exch(self):
        if len(self.stack) >= 2:
            self.stack[-1], self.stack[-2] = self.stack[-2], self.stack[-1]

    # arithmetic
    def _bin(self, fn):
        b = self._pop(); a = self._pop()
        try:
            self.stack.append(fn(a, b))
        except Exception:
            self.stack.append(0)

    def op_add(self):
        self._bin(lambda a, b: a + b)

    def op_sub(self):
        self._bin(lambda a, b: a - b)

    def op_mul(self):
        self._bin(lambda a, b: a * b)

    def op_div(self):
        self._bin(lambda a, b: a / b if b else 0)

    def op_idiv(self):
        self._bin(lambda a, b: int(a) // int(b) if b else 0)

    def op_mod(self):
        self._bin(lambda a, b: int(a) % int(b) if b else 0)

    def _unary(self, fn):
        a = self._pop()
        try:
            self.stack.append(fn(a))
        except Exception:
            self.stack.append(0)

    def op_neg(self):
        self._unary(lambda a: -a)

    def op_abs(self):
        self._unary(abs)

    def op_round(self):
        self._unary(round)

    def op_truncate(self):
        self._unary(lambda a: float(int(a)))

    def op_sqrt(self):
        import math
        self._unary(lambda a: math.sqrt(max(0.0, a)))

    # comparison / boolean
    def op_eq(self):
        self._bin(lambda a, b: a == b)

    def op_ne(self):
        self._bin(lambda a, b: a != b)

    def op_gt(self):
        self._bin(lambda a, b: a > b)

    def op_lt(self):
        self._bin(lambda a, b: a < b)

    def op_ge(self):
        self._bin(lambda a, b: a >= b)

    def op_le(self):
        self._bin(lambda a, b: a <= b)

    # stack operators
    def op_count(self):
        self.stack.append(len(self.stack))

    def op_clear(self):
        self.stack.clear()

    def op_copy(self):
        n = self._pop()
        if isinstance(n, (int, float)) and n > 0:
            self.stack.extend(self.stack[-int(n):])

    def op_index(self):
        n = int(self._pop())
        if 0 <= n < len(self.stack):
            self.stack.append(self.stack[-1 - n])

    def op_roll(self):
        j = int(self._pop()); n = int(self._pop())
        if 0 < n <= len(self.stack):
            j %= n
            part = self.stack[-n:]
            self.stack[-n:] = part[-j:] + part[:-j]

    # control flow
    def op_exec(self):
        self._run_proc(self._pop())

    def op_if(self):
        proc = self._pop(); cond = self._pop()
        if cond:
            self._run_proc(proc)

    def op_ifelse(self):
        p2 = self._pop(); p1 = self._pop(); cond = self._pop()
        self._run_proc(p1 if cond else p2)

    def op_repeat(self):
        proc = self._pop(); n = self._pop()
        for _ in range(int(n) if isinstance(n, (int, float)) else 0):
            if self._ops > self.MAX_OPS:
                break
            self._run_proc(proc)

    def op_for(self):
        proc = self._pop(); limit = self._fpop(); inc = self._fpop(); i = self._fpop()
        if inc == 0:
            return
        guard = 0
        while ((inc > 0 and i <= limit) or (inc < 0 and i >= limit)) and guard < 100000:
            if self._ops > self.MAX_OPS:
                break
            self.stack.append(i)
            self._run_proc(proc)
            i += inc
            guard += 1

    # paths: curves approximated by line segments
    def op_curveto(self):
        y3 = self._fpop(); x3 = self._fpop(); y2 = self._fpop(); x2 = self._fpop()
        y1 = self._fpop(); x1 = self._fpop()
        p0 = (self.gs.x, self.gs.y)
        p1 = self.gs.dev(x1, y1); p2 = self.gs.dev(x2, y2); p3 = self.gs.dev(x3, y3)
        for k in range(1, 9):
            t = k / 8.0
            mt = 1 - t
            x = (mt**3 * p0[0] + 3 * mt**2 * t * p1[0]
                 + 3 * mt * t**2 * p2[0] + t**3 * p3[0])
            y = (mt**3 * p0[1] + 3 * mt**2 * t * p1[1]
                 + 3 * mt * t**2 * p2[1] + t**3 * p3[1])
            if self.path:
                self.path[-1].append((x, y))
        self.gs.x, self.gs.y = p3

    def op_arc(self):
        import math
        a2 = self._fpop(); a1 = self._fpop(); r = self._fpop(); cy = self._fpop(); cx = self._fpop()
        pts = []
        steps = max(4, int(abs(a2 - a1) / 15))
        for k in range(steps + 1):
            ang = math.radians(a1 + (a2 - a1) * k / steps)
            pts.append(self.gs.dev(cx + r * math.cos(ang), cy + r * math.sin(ang)))
        if pts:
            self.path.append(pts)
            self.gs.x, self.gs.y = pts[-1]

    op_arcn = op_arc

    def op_selectfont(self):
        size = self._fpop(); name = self._pop()
        fname = name[1] if isinstance(name, tuple) else str(name)
        self.gs.font = fname
        self.gs.size = size * self.gs.sy

    def op_stringwidth(self):
        s = self._pop()
        w = fontmetrics.width(s, self._base_font(), self.gs.size) if isinstance(s, str) else 0
        self.stack.append(w); self.stack.append(0.0)

    def op_setlinecap(self):
        self._pop()

    def op_setlinejoin(self):
        self._pop()

    def op_setdash(self):
        self._pop(2)

    def op_initgraphics(self):
        self.gs = GState()

    # -- extended coverage (real-world prologues) -------------------------
    # colour
    def op_setcmykcolor(self):
        k = self._pop(); y = self._pop(); m = self._pop(); c = self._pop()
        try:
            r = (1 - c) * (1 - k); g = (1 - m) * (1 - k); b = (1 - y) * (1 - k)
            self.gs.color = Color.rgb(r, g, b)
        except Exception:
            pass

    # paint / clip (clip is a no-op here; just clear the current path like PS does)
    op_eofill = op_fill

    def op_clip(self):
        pass

    op_eoclip = op_clip
    op_initclip = op_clip

    def op_rectclip(self):
        self._pop(4)

    # text show variants -> treat like show (spacing nuances dropped)
    def op_widthshow(self):
        s = self._pop(); self._pop(3)       # cx cy char (string) widthshow
        self.stack.append(s); self.op_show()

    def op_awidthshow(self):
        s = self._pop(); self._pop(5)       # cx cy char ax ay (string) awidthshow
        self.stack.append(s); self.op_show()

    def op_kshow(self):
        s = self._pop(); self._pop()        # (string) proc kshow
        self.stack.append(s); self.op_show()

    def op_xshow(self):
        self._pop()                          # numarray
        self.op_show()

    op_yshow = op_xshow
    op_xyshow = op_xshow

    def op_glyphshow(self):
        self._pop()                          # name/glyph: no metrics, skip

    # matrix / ctm
    def op_concat(self):
        m = self._pop()
        if isinstance(m, list) and len(m) >= 6:
            a, b, c, d, e, f = (m[i] if isinstance(m[i], (int, float)) else 0 for i in range(6))
            self.gs.sx *= a or 1.0
            self.gs.sy *= d or 1.0
            self.gs.tx += e * self.gs.sx
            self.gs.ty += f * self.gs.sy

    def op_matrix(self):
        self.stack.append([1.0, 0.0, 0.0, 1.0, 0.0, 0.0])

    op_currentmatrix = op_matrix

    def op_setmatrix(self):
        self._pop()

    def op_currentpoint(self):
        self.stack.append(self.gs.x); self.stack.append(self.gs.y)

    # path
    def op_rcurveto(self):
        dy3 = self._fpop(); dx3 = self._fpop(); dy2 = self._fpop()
        dx2 = self._fpop(); dy1 = self._fpop(); dx1 = self._fpop()
        x0, y0 = self.gs.x, self.gs.y
        p1 = (x0 + dx1 * self.gs.sx, y0 + dy1 * self.gs.sy)
        p2 = (x0 + dx2 * self.gs.sx, y0 + dy2 * self.gs.sy)
        p3 = (x0 + dx3 * self.gs.sx, y0 + dy3 * self.gs.sy)
        for k in range(1, 9):
            t = k / 8.0; mt = 1 - t
            x = mt**3 * x0 + 3 * mt**2 * t * p1[0] + 3 * mt * t**2 * p2[0] + t**3 * p3[0]
            y = mt**3 * y0 + 3 * mt**2 * t * p1[1] + 3 * mt * t**2 * p2[1] + t**3 * p3[1]
            if self.path:
                self.path[-1].append((x, y))
        self.gs.x, self.gs.y = p3

    op_arct = op_arc

    # dict / scoping (definitions are kept flat in self.defs; scoping is a no-op)
    def op_dict(self):
        self._pop(); self.stack.append({})

    def op_begin(self):
        self._pop()

    def op_end(self):
        pass

    def op_load(self):
        key = self._pop()
        name = key[1] if isinstance(key, tuple) else key
        self.stack.append(self.defs.get(name))

    def op_known(self):
        self._pop(2); self.stack.append(False)

    def op_where(self):
        self._pop(); self.stack.append(False)

    def op_cvx(self):
        pass

    op_cvi = op_round
    op_cvr = op_truncate

    def op_cvn(self):
        v = self._pop()
        self.stack.append(("name", v) if isinstance(v, str) else v)

    def op_cvs(self):
        v = self._pop(); self._pop()        # any string cvs -> string
        self.stack.append(str(v))

    # images: recognized so they don't fall through as unknown; inline pixel data in
    # the token stream is not decoded (documented fidelity limit).
    def op_image(self):
        self.stack.clear()

    op_imagemask = op_image
    op_colorimage = op_image
