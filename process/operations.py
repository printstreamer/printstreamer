""" Declarative edit operations over the generic model.

Drives extract / delete / modify / add from XML ``<step name="edit">`` children, so
workflows can transform a stream without code. Selection reuses model.visitor
(by text, by hex, by window). Operations are format-agnostic; they run on the model
and are written out by any writer.
"""

from __future__ import annotations

import logging

import re

from model import visitor
from model.element import (BarcodeElement, DrawOp, ElementKind, GraphicElement,
                           ImageElement, LineElement, OverlayElement, TextElement)
from model.geometry import Color, Point, Rect

logger = logging.getLogger(__name__)

_KINDS = {k.value: k for k in ElementKind}


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
        return Color.cmyk(*(float(v) for v in s[5:-1].split(",")))
    return Color.named(s)


def _rect(spec):
    x, y, w, h = (float(v) for v in spec.split(","))
    return Rect(x, y, w, h)


def parse_operations(step):
    """ Read operation nodes from a step into a list of op dicts. """
    ops = []
    for node in step.childNodes:
        if node.nodeType != node.ELEMENT_NODE:
            continue
        if node.tagName in ("extract", "delete", "modify", "add"):
            op = {"verb": node.tagName}
            for i in range(node.attributes.length):
                attr = node.attributes.item(i)
                op[attr.name] = attr.value
            op["_text"] = node.firstChild.data if node.firstChild else None
            ops.append(op)
    return ops


def _select(page, op):
    kind = _KINDS.get(op.get("kind"))
    if op.get("window"):
        return visitor.select_in_window(page, _rect(op["window"]), contained=False, kind=kind)
    if op.get("text"):
        return visitor.select_by_text(page, op["text"], regex=op.get("regex") == "true", kind=kind)
    if op.get("hex"):
        return visitor.select_by_hex(page, op["hex"], kind=kind)
    return list(visitor.iter_elements(page, kind))


_FIELD = re.compile(r"\{(\w+)\}")


def _subst(value, context):
    if context and isinstance(value, str):
        return _FIELD.sub(lambda m: str(context.get(m.group(1), "")), value)
    return value


def apply_operations(doc_set, ops, context_for=None):
    """ Apply ops to every page; returns extracted field values.

    ``context_for(page)`` may return a dict of field values for ``{field}``
    substitution in ``add`` operations (e.g. index-record fields during merge). """
    extracted = []
    for op in ops:
        verb = op["verb"]
        for document, page in doc_set.iter_pages():
            matches = _select(page, op)
            if verb == "delete":
                visitor.remove(matches)
            elif verb == "modify":
                _modify(matches, op)
            elif verb == "extract":
                for mch in matches:
                    extracted.append({
                        "field": op.get("field", "value"),
                        "page": page.number,
                        "value": getattr(mch.element, "text", None) or getattr(mch.element, "data", ""),
                    })
                if op.get("delete") == "true":
                    visitor.remove(matches)
            elif verb == "add":
                ctx = context_for(page) if context_for else None
                _add(page, {k: _subst(v, ctx) for k, v in op.items()})
    return extracted


def apply_to_page(page, ops, context=None):
    """ Apply a list of ops to a single page, with optional ``{field}`` context. """
    for op in ops:
        verb = op["verb"]
        matches = _select(page, op)
        if verb == "delete":
            visitor.remove(matches)
        elif verb == "modify":
            _modify(matches, op)
        elif verb == "add":
            _add(page, {k: _subst(v, context) for k, v in op.items()})


def _modify(matches, op):
    color = parse_color(op.get("set-color"))
    for mch in matches:
        el = mch.element
        if op.get("set-text") is not None and hasattr(el, "text"):
            el.text = op["set-text"]
        if op.get("set-font") and hasattr(el, "font_ref"):
            el.font_ref = op["set-font"]
        if op.get("set-size") and hasattr(el, "font_size"):
            el.font_size = float(op["set-size"])
        if color is not None and hasattr(el, "color"):
            el.color = color
        if op.get("dx") or op.get("dy"):
            dx, dy = float(op.get("dx", 0)), float(op.get("dy", 0))
            if getattr(el, "position", None):
                el.position = Point(el.position.x + dx, el.position.y + dy)
            if el.bbox:
                el.bbox = Rect(el.bbox.x + dx, el.bbox.y + dy, el.bbox.width, el.bbox.height)


def _pages_for(page, op):
    target = op.get("page")
    return target is None or int(target) == page.number


def _add(page, op):
    if not _pages_for(page, op):
        return
    kind = op.get("kind", "text")
    x, y = float(op.get("x", 0)), float(op.get("y", 0))
    if kind == "text":
        page.add_element(TextElement(
            text=op.get("_text") or op.get("text", ""), position=Point(x, y),
            font_size=float(op.get("size", 10)), color=parse_color(op.get("color")),
            bbox=Rect(x, y - float(op.get("size", 10)), float(op.get("width", 100)),
                      float(op.get("size", 10)))))
    elif kind == "barcode":
        page.add_element(BarcodeElement(
            symbology=op.get("symbology", "code128"), data=op.get("data", ""),
            bbox=Rect(x, y, float(op.get("width", 144)), float(op.get("height", 36)))))
    elif kind == "line":
        page.add_element(LineElement(
            start=Point(x, y), end=Point(float(op.get("x2", x)), float(op.get("y2", y))),
            weight=float(op.get("weight", 1)), color=parse_color(op.get("color")),
            bbox=Rect.from_corners(x, y, float(op.get("x2", x)), float(op.get("y2", y)))))
    elif kind == "image":
        data = None
        src = op.get("src")
        if src:
            import os
            if os.path.exists(src):
                with open(src, "rb") as fh:
                    data = fh.read()
        page.add_element(ImageElement(
            data=data, encoding=(op.get("src", "").rsplit(".", 1)[-1] if op.get("src") else None),
            bbox=Rect(x, y, float(op.get("width", 72)), float(op.get("height", 72)))))
    elif kind in ("rectangle", "ellipse"):
        w, h = float(op.get("width", 0)), float(op.get("height", 0))
        page.add_element(GraphicElement(
            ops=[DrawOp("box" if kind == "rectangle" else "ellipse",
                        [Point(x, y), Point(x + w, y + h)])],
            stroke=parse_color(op.get("color")), fill=parse_color(op.get("fill")),
            bbox=Rect(x, y, w, h)))
    elif kind == "omr":
        page.add_element(BarcodeElement(
            symbology="omr", data=op.get("data", ""),
            params={"mark_height": float(op.get("mark_height", 2)),
                    "pitch": float(op.get("pitch", 0)) or None},
            bbox=Rect(x, y, float(op.get("width", 8)), float(op.get("height", 144)))))
    elif kind == "overlay":
        page.add_element(OverlayElement(
            resource_ref=op.get("name"), attributes={"x": x, "y": y},
            bbox=Rect(x, y, float(op.get("width", 0)), float(op.get("height", 0)))))
