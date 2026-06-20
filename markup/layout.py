""" PSML layout engine: flow the markup AST into the generic model.

Implements the hard parts of an XSL-FO-style formatter: automatic text flow with
line wrapping, multi-column and multi-page pagination, page headers/footers with
page-number fields, widow/orphan control, and keep-together. Block primitives
(image, line, rectangle, ellipse, polygon, path, barcode, table) place onto the page
as model elements. All measurements are in printer points.
"""

from __future__ import annotations

import logging
import os
import re

import fontmetrics
from markup.model import Markup, Node, PageMaster, inheritable, resolve_style
from model.document import Document, StreamDocumentSet
from model.element import (BarcodeElement, ContainerElement, DrawOp,
                           GraphicElement, ImageElement, LineElement,
                           OverlayElement, TextElement)
from model.geometry import Color, Point, Rect
from model.page import IndexTag, Page
from units import parse_length

logger = logging.getLogger(__name__)

_DEFAULT_SIZE = 11.0
_DEFAULT_LEADING = 1.2          # line-height multiple
_PRIMITIVES = {"line", "rectangle", "ellipse", "polygon", "path", "barcode", "image"}


# --- value parsing ---------------------------------------------------------

def parse_color(value):
    if not value:
        return None
    s = str(value).strip().lower()
    if s.startswith("#") and len(s) == 7:
        return Color.rgb(int(s[1:3], 16) / 255, int(s[3:5], 16) / 255, int(s[5:7], 16) / 255)
    if s.startswith("rgb(") and s.endswith(")"):
        r, g, b = (float(v) for v in s[4:-1].split(","))
        scale = 255.0 if max(r, g, b) > 1 else 1.0
        return Color.rgb(r / scale, g / scale, b / scale)
    if s.startswith("cmyk(") and s.endswith(")"):
        c, m, y, k = (float(v) for v in s[5:-1].split(","))
        return Color.cmyk(c, m, y, k)
    return Color.named(s)


def _truthy(v):
    return str(v).lower() in ("1", "true", "yes", "always", "on")


class TextStyle:
    """ Concrete text style resolved from PSML properties. """

    def __init__(self, props):
        family = props.get("font") or props.get("font-family")
        weight = (props.get("weight") or props.get("font-weight") or "").lower()
        fstyle = (props.get("style_") or props.get("font-style") or "").lower()
        self.bold = "bold" in weight or weight in ("700", "800", "900")
        self.italic = fstyle in ("italic", "oblique")
        self.base = fontmetrics.base_font(family, self.bold, self.italic)
        self.size = parse_length(props.get("size") or props.get("font-size"), _DEFAULT_SIZE)
        self.color = parse_color(props.get("color")) or Color.rgb(0, 0, 0)
        self.letter_spacing = parse_length(props.get("letter-spacing"), 0.0)

    def width(self, text):
        w = fontmetrics.width(text, self.base, self.size)
        if self.letter_spacing and text:
            w += self.letter_spacing * len(text)
        return w


# --- frames and pagination -------------------------------------------------

class Frame:
    def __init__(self, x, top, w, bottom):
        self.x = x
        self.width = w
        self.bottom = bottom
        self.y = top              # cursor (top of next content)

    def space(self):
        return self.bottom - self.y


class Paginator:
    def __init__(self, engine, document, master):
        self.engine = engine
        self.document = document
        self.master = master
        self.page_no = 0
        self.frames = []
        self.frame_idx = 0
        self.page = None
        self.new_page()

    def new_page(self):
        m = self.master
        self.page_no += 1
        self.page = self.document.add_page(
            Page(number=len(self.document.pages) + 1, size=Rect(0, 0, m.width, m.height)))
        cw = m.column_width()
        self.frames = [Frame(m.body_left + i * (cw + m.column_gap), m.body_top, cw, m.body_bottom)
                       for i in range(m.columns)]
        self.frame_idx = 0
        self.engine.render_regions(self.page, self.page_no, m)

    @property
    def frame(self):
        return self.frames[self.frame_idx]

    def next_frame(self):
        if self.frame_idx < len(self.frames) - 1:
            self.frame_idx += 1
        else:
            self.new_page()


# --- layout engine ---------------------------------------------------------

class LayoutEngine:
    def __init__(self, markup: Markup):
        self.markup = markup
        self.doc_set = StreamDocumentSet()
        self._pagecount_tokens = []     # TextElements needing the final page count
        self._page = None               # current model page being filled

    def run(self) -> StreamDocumentSet:
        for seq in self.markup.sequences:
            self._layout_sequence(seq)
        self._fill_page_counts()
        return self.doc_set

    def _layout_sequence(self, seq: Node):
        master = self.markup.masters.get(seq.get("master"),
                                         next(iter(self.markup.masters.values())))
        document = self.doc_set.add_document(Document(name=seq.get("name")))
        for b in seq.find("bookmark"):
            document.index_tags.append(IndexTag(
                name="bookmark", value=b.get("title") or b.get("name"),
                attributes={"id": b.get("name")}))
        paginator = Paginator(self, document, master)
        flow = seq.first("flow") or seq
        self._flow_blocks(flow.children, paginator, {})

    # -- block flow -------------------------------------------------------

    def _flow_blocks(self, blocks, paginator, inherited):
        for block in blocks:
            if block.tag in ("paragraph", "block", "heading"):
                self._layout_paragraph(block, paginator, inherited)
            elif block.tag == "table":
                self._layout_table(block, paginator, inherited)
            elif block.tag in _PRIMITIVES:
                self._place_primitive(block, paginator)
            elif block.tag in ("overlay", "page-segment", "object-container",
                                "structured-field", "medium-map"):
                self._place_afp(block, paginator)
            elif block.tag in ("footnote", "annotation", "bookmark", "layer"):
                self._record_meta(block, paginator)
            elif block.tag == "page-break":
                paginator.new_page()

    def _record_meta(self, block, paginator):
        paginator.page.index_tags.append(
            IndexTag(name=block.tag, value=block.get("name") or block.text))

    def _place_afp(self, block, paginator):
        """ AFP-specific PSML constructs -> model elements the AFP writer emits. """
        self._page = paginator.page
        x, y = block.length("x"), block.length("y")
        if block.tag == "overlay":
            self._page.add_element(OverlayElement(
                resource_ref=block.get("name"),
                bbox=Rect(x, y, block.length("width"), block.length("height")),
                attributes={"x": x, "y": y}))
        elif block.tag == "medium-map":
            self._page.attributes["medium_map"] = block.get("name")
        else:
            raw = None
            if block.get("hex"):
                raw = bytes.fromhex(block.get("hex").replace(" ", ""))
            self._page.add_element(ContainerElement(
                preserved_type=block.tag, raw=raw,
                bbox=Rect(x, y, 0, 0) if block.get("x") else None,
                attributes={"name": block.get("name"), "x": x, "y": y}))

    # -- paragraphs (the flow core) --------------------------------------

    def _layout_paragraph(self, block, paginator, inherited):
        eff = resolve_style(block, self.markup.styles, inherited)
        base_style = TextStyle(eff)
        align = (eff.get("text-align") or "left").lower()
        leading = parse_length(eff.get("line-height"), 0.0) or base_style.size * _DEFAULT_LEADING
        space_before = parse_length(eff.get("space-before"), 0.0)
        space_after = parse_length(eff.get("space-after"), 0.0)
        start_indent = parse_length(eff.get("start-indent"), 0.0)
        end_indent = parse_length(eff.get("end-indent"), 0.0)
        first_indent = parse_length(eff.get("first-line-indent"), 0.0)
        widows = int(eff.get("widows", "2"))
        orphans = int(eff.get("orphans", "2"))
        keep = _truthy(eff.get("keep-together", "false"))
        keep_with_next = _truthy(eff.get("keep-with-next", "false"))

        words = self._tokenize(block, base_style, inheritable(eff))
        frame = paginator.frame
        avail = frame.width - start_indent - end_indent
        lines = self._wrap(words, avail, first_indent)
        if not lines:
            return

        frame.y += space_before
        # keep-with-next reserves space for the start of the following block so a
        # heading never sits alone at the foot of a column.
        self._place_lines(lines, paginator, leading, align, start_indent,
                          end_indent, first_indent, widows, orphans,
                          keep or keep_with_next, reserve=2 if keep_with_next else 0)
        paginator.frame.y += space_after

    def _tokenize(self, block, style, inherited):
        """ Flatten paragraph inline content into styled tokens.

        Each token is (word, style, space_before): ``space_before`` records whether
        original whitespace separated this token from the previous one, so inline
        adjacency like "x/<field>" is preserved (no spurious spaces inserted).
        """
        tokens = []
        state = {"space": False}

        def add_text(s, st):
            for part in re.split(r"(\s+)", s):
                if not part:
                    continue
                if part.isspace():
                    state["space"] = True
                else:
                    tokens.append((part, st, state["space"]))
                    state["space"] = False

        def walk(item, st):
            if isinstance(item, str):
                add_text(item, st)
                return
            node = item
            if node.tag in ("page-number", "page-count"):
                marker = "\x00PAGE" if node.tag == "page-number" else "\x00COUNT"
                tokens.append((marker, st, state["space"]))
                state["space"] = False
                return
            child_style = TextStyle(resolve_style(node, self.markup.styles, dict(inherited)))
            for child in (node.content or ([node.text] if node.text else [])):
                walk(child, child_style)

        for item in (block.content or ([block.text] if block.text else [])):
            walk(item, style)
        return tokens

    def _wrap(self, tokens, avail, first_indent):
        lines = []
        cur = []
        cur_w = 0.0
        indent = first_indent
        for word, style, space_before in tokens:
            ww = style.width(word)
            space = style.width(" ") if (cur and space_before) else 0.0
            if cur and cur_w + space + ww > avail - indent:
                lines.append(cur)
                cur = [(word, style, False)]      # first word of a line: no lead space
                cur_w = ww
                indent = 0.0
            else:
                cur.append((word, style, space_before if cur else False))
                cur_w += space + ww
        if cur:
            lines.append(cur)
        return lines

    def _place_lines(self, lines, paginator, leading, align, start_indent,
                     end_indent, first_indent, widows, orphans, keep, reserve=0):
        total = len(lines)
        frame = paginator.frame
        # keep-together / keep-with-next: if the block (plus any reserved following
        # lines) fits in a fresh frame but not here, advance first.
        need = (total + reserve) * leading
        if keep and need > frame.space() and need <= (frame.bottom - paginator.master.body_top):
            paginator.next_frame()
            frame = paginator.frame

        placed = 0
        while placed < total:
            frame = paginator.frame
            fit = max(0, int(frame.space() // leading))
            remaining = total - placed
            if fit >= remaining:
                count = remaining
            else:
                count = fit
                # orphan control: don't strand fewer than `orphans` lines here.
                if count < orphans and placed == 0:
                    paginator.next_frame()
                    continue
                # widow control: don't push fewer than `widows` lines forward.
                if remaining - count < widows:
                    count = max(orphans, remaining - widows)
                    if count <= 0:
                        paginator.next_frame()
                        continue
            for i in range(placed, placed + count):
                self._emit_line(lines[i], paginator.frame, leading, align,
                                start_indent, end_indent,
                                first_indent if i == 0 else 0.0,
                                last=(i == total - 1))
            placed += count
            if placed < total:
                paginator.next_frame()

    def _emit_line(self, line, frame, leading, align, start_indent, end_indent,
                   first_indent, last):
        avail = frame.width - start_indent - end_indent - first_indent
        word_widths = [s.width(w) for w, s, _ in line]
        spaces = [(s.width(" ") if sb else 0.0) for _, s, sb in line]
        natural = sum(word_widths) + sum(spaces)
        x0 = frame.x + start_indent + first_indent
        if align == "right":
            x0 = frame.x + frame.width - end_indent - natural
        elif align == "center":
            x0 = frame.x + start_indent + first_indent + (avail - natural) / 2
        justify_extra = 0.0
        gaps = sum(1 for _, _, sb in line if sb)
        if align == "justify" and not last and gaps:
            justify_extra = (avail - natural) / gaps

        baseline = frame.y + leading * 0.8
        x = x0
        run_text, run_style, run_x = "", None, x
        for (word, style, sb), ww, sp in zip(line, word_widths, spaces):
            extra = justify_extra if (sb and justify_extra) else 0.0
            x += sp + extra
            is_field = word in ("\x00PAGE", "\x00COUNT")
            # Merge adjacent same-style tokens, preserving original spacing, but never
            # merge page-number/count fields and never across a justification stretch.
            if run_style is style and extra == 0.0 and not is_field and run_style is not None:
                run_text += (" " if sb else "") + word
            else:
                if run_style is not None:
                    self._emit_run(frame, run_text, run_style, run_x, baseline, leading)
                run_text, run_style, run_x = word, style, x
            if is_field:                      # fields stand alone so they resolve
                self._emit_run(frame, run_text, run_style, run_x, baseline, leading)
                run_text, run_style = "", None
            x += ww
        if run_style is not None:
            self._emit_run(frame, run_text, run_style, run_x, baseline, leading)
        frame.y += leading

    def _emit_run(self, frame, text, style, x, baseline, leading):
        field = None
        if text == "\x00PAGE":
            display = str(self._page.number)        # current page is known now
        elif text == "\x00COUNT":
            display, field = "", "page-count"        # filled in a post-pass
        else:
            display = text
        w = style.width(display)
        element = TextElement(
            text=display, position=Point(x, baseline), font_size=style.size,
            color=style.color, font_ref=style.base,
            bbox=Rect(x, baseline - style.size, w, leading),
        )
        if field:
            element.attributes["field"] = field
            self._pagecount_tokens.append(element)
        self._page.add_element(element)

    # -- tables (simple grid) --------------------------------------------

    def _layout_table(self, block, paginator, inherited):
        rows = block.find("row")
        if not rows:
            return
        self._page = paginator.page
        frame = paginator.frame
        table_eff = resolve_style(block, self.markup.styles, inherited)
        col_widths = self._table_columns(block, rows, frame.width)
        border = block.length("border", 0.0)
        padding = block.length("cellpadding", 3.0)

        for row in rows:
            cells = row.find("cell")
            # Lay out each cell's wrapped content; honour colspan.
            laid = []
            ci = 0
            for cell in cells:
                span = max(1, int(cell.get("colspan", "1")))
                width = sum(col_widths[ci:ci + span])
                lines = self._cell_lines(cell, width - 2 * padding, table_eff)
                height = sum(ld for _, ld, _ in lines)
                laid.append((ci, span, width, lines, height))
                ci += span
            row_h = max([h for *_, h in laid] or [0.0]) + 2 * padding
            row_h = max(row_h, row.length("height", 0.0))
            if frame.space() < row_h:                 # keep rows intact across frames
                paginator.next_frame()
                self._page = paginator.page
                frame = paginator.frame
            row_y = frame.y
            for ci2, span, width, lines, _h in laid:
                x = frame.x + sum(col_widths[:ci2])
                if border > 0:
                    self._page.add_element(GraphicElement(
                        ops=[DrawOp("box", [Point(x, row_y), Point(x + width, row_y + row_h)])],
                        stroke=Color.rgb(0, 0, 0), bbox=Rect(x, row_y, width, row_h)))
                self._emit_cell(lines, x + padding, row_y + padding, width - 2 * padding)
            frame.y += row_h

    def _table_columns(self, block, rows, frame_width):
        cols = block.find("column")
        if cols:
            widths = [c.length("width", 0.0) for c in cols]
            flex = [i for i, w in enumerate(widths) if w <= 0]
            remaining = frame_width - sum(widths)
            for i in flex:
                widths[i] = remaining / len(flex) if flex else 0.0
            return widths
        ncols = max(sum(max(1, int(c.get("colspan", "1"))) for c in r.find("cell"))
                    for r in rows)
        return [frame_width / ncols] * ncols

    def _cell_lines(self, cell, content_w, inherited):
        """ Wrap a cell's paragraph(s) into (line, leading, align) tuples. """
        blocks = [c for c in cell.children if c.tag in ("paragraph", "block", "heading")]
        if not blocks:
            blocks = [cell]                           # treat inline content as one paragraph
        out = []
        for para in blocks:
            eff = resolve_style(para, self.markup.styles, inherited)
            style = TextStyle(eff)
            leading = parse_length(eff.get("line-height"), 0.0) or style.size * _DEFAULT_LEADING
            align = (eff.get("text-align") or "left").lower()
            tokens = self._tokenize(para, style, inheritable(eff))
            for line in self._wrap(tokens, content_w, 0.0):
                out.append((line, leading, align))
        return out

    def _emit_cell(self, lines, x, y, content_w):
        cy = y
        for line, leading, align in lines:
            self._emit_cell_line(line, x, cy + leading * 0.8, content_w, align)
            cy += leading

    def _emit_cell_line(self, line, x, baseline, content_w, align):
        widths = [s.width(w) for w, s, _ in line]
        spaces = [(s.width(" ") if sb else 0.0) for _, s, sb in line]
        natural = sum(widths) + sum(spaces)
        if align == "right":
            cx = x + content_w - natural
        elif align == "center":
            cx = x + (content_w - natural) / 2
        else:
            cx = x
        run_text, run_style, run_x = "", None, cx
        for (word, style, sb), ww, sp in zip(line, widths, spaces):
            cx += sp
            if run_style is style and run_style is not None and word not in ("\x00PAGE", "\x00COUNT"):
                run_text += (" " if sb else "") + word
            else:
                if run_style is not None:
                    self._emit_run_at(run_text, run_style, run_x, baseline)
                run_text, run_style, run_x = word, style, cx
            cx += ww
        if run_style is not None:
            self._emit_run_at(run_text, run_style, run_x, baseline)

    def _emit_run_at(self, text, style, x, baseline):
        self._page.add_element(TextElement(
            text=text, position=Point(x, baseline), font_size=style.size,
            color=style.color, font_ref=style.base,
            bbox=Rect(x, baseline - style.size, style.width(text), style.size * _DEFAULT_LEADING)))

    # -- block primitives -------------------------------------------------

    def _place_primitive(self, block, paginator):
        self._page = paginator.page
        if block.tag == "line":
            self._page.add_element(LineElement(
                start=Point(block.length("x1"), block.length("y1")),
                end=Point(block.length("x2"), block.length("y2")),
                weight=block.length("width", 1.0),
                color=parse_color(block.get("color")),
                bbox=Rect.from_corners(block.length("x1"), block.length("y1"),
                                       block.length("x2"), block.length("y2"))))
        elif block.tag in ("rectangle", "ellipse", "polygon", "path"):
            self._page.add_element(self._graphic(block))
        elif block.tag == "barcode":
            x, y = block.length("x"), block.length("y")
            self._page.add_element(BarcodeElement(
                symbology=block.get("symbology", "code128"), data=block.get("data", ""),
                bbox=Rect(x, y, block.length("width", 144), block.length("height", 36)),
                color=parse_color(block.get("color"))))
        elif block.tag == "image":
            self._place_image(block, paginator)

    def _graphic(self, block):
        x, y = block.length("x"), block.length("y")
        w, h = block.length("width"), block.length("height")
        ops = []
        if block.tag == "rectangle":
            ops.append(DrawOp("box", [Point(x, y), Point(x + w, y + h)]))
        elif block.tag == "ellipse":
            ops.append(DrawOp("ellipse", [Point(x, y), Point(x + w, y + h)]))
        elif block.tag in ("polygon", "path"):
            pts = [Point(*map(parse_length, p.split(",")))
                   for p in (block.get("points", "")).split() if "," in p]
            ops.append(DrawOp("polyline" if block.tag == "polygon" else "path", pts))
        return GraphicElement(
            ops=ops, stroke=parse_color(block.get("color")),
            fill=parse_color(block.get("fill")),
            bbox=Rect(x, y, w, h) if (w or h) else None)

    def _place_image(self, block, paginator):
        src = block.get("src")
        data = None
        if src and os.path.exists(src):
            with open(src, "rb") as fh:
                data = fh.read()
        w = block.length("width", 72)
        h = block.length("height", 72)
        if block.get("x") is not None:
            x, y = block.length("x"), block.length("y")
        else:                              # flow: place at the cursor
            frame = paginator.frame
            if frame.space() < h:
                paginator.next_frame()
                frame = paginator.frame
            x, y = frame.x, frame.y
            frame.y += h
        paginator.page.add_element(ImageElement(
            data=data, encoding=(os.path.splitext(src)[1].lstrip(".") if src else None),
            bbox=Rect(x, y, w, h)))

    # -- headers / footers ------------------------------------------------

    def render_regions(self, page, page_no, master: PageMaster):
        self._page = page
        if master.header:
            self._render_region(page, master.header, master.body_left,
                                 master.margin_top, master.body_right - master.body_left,
                                 master.header_extent, page_no)
        if master.footer:
            self._render_region(page, master.footer, master.body_left,
                                 master.height - master.margin_bottom - master.footer_extent,
                                 master.body_right - master.body_left,
                                 master.footer_extent, page_no)

    def _render_region(self, page, blocks, x, top, w, h, page_no):
        frame = Frame(x, top, w, top + h)
        for block in blocks:
            eff = resolve_style(block, self.markup.styles, {})
            st = TextStyle(eff)
            align = (eff.get("text-align") or "left").lower()
            words = self._tokenize(block, st, inheritable(eff))
            # Build the region text; page-number resolves now, page-count later.
            has_count = any(w0 == "\x00COUNT" for w0, *_ in words)
            template = " ".join(("{count}" if w0 == "\x00COUNT"
                                 else (str(page_no) if w0 == "\x00PAGE" else w0))
                                for w0, *_ in words)
            text = template.replace("{count}", "") if has_count else template
            tw = st.width(template.replace("{count}", "00"))
            if align == "right":
                tx = x + w - tw
            elif align == "center":
                tx = x + (w - tw) / 2
            else:
                tx = x
            element = TextElement(
                text=text, position=Point(tx, frame.y + st.size), font_size=st.size,
                color=st.color, font_ref=st.base,
                bbox=Rect(tx, frame.y, tw, st.size * _DEFAULT_LEADING))
            if has_count:
                element.attributes["pagecount_template"] = template
                self._pagecount_tokens.append(element)
            page.add_element(element)
            frame.y += st.size * _DEFAULT_LEADING

    # -- page-count post-pass --------------------------------------------

    def _fill_page_counts(self):
        total = self.doc_set.page_count
        for el in self._pagecount_tokens:
            if el.attributes.get("field") == "page-count":
                el.text = str(total)
            elif "pagecount_template" in el.attributes:
                el.text = el.attributes["pagecount_template"].replace("{count}", str(total))
