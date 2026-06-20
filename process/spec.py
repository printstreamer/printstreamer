""" Load a complete process specification (spec.xml).

A spec is the single place that defines everything a process does: its input and
output files (print streams, PSML, index files), document identification, extraction
fields, page enhancements, and imposition layout. A process file then only needs to
name each step and point it at a spec:

    <process>
      <step name="extract" spec="statements_extract.xml"/>
      <step name="merge"   spec="statements_merge.xml"/>
    </process>

Inline attributes/children on the step still work and override the spec, but the spec
is meant to carry the full definition. See docs/spec.md for the complete grammar.
"""

from __future__ import annotations

from dataclasses import dataclass, field as _field
from xml.dom import minidom

from model.geometry import Rect
from process.index import FieldSpec


@dataclass
class FileRef:
    name: str
    type: str | None = None        # printstream type, or "psml" / "index"


@dataclass
class IndexRef:
    name: str | None = None
    format: str = "json"
    compress: str = "none"
    level: int = 0


@dataclass
class CellSpec:
    """ One n-up output cell: which input page to place and how. """
    row: int = 0
    col: int = 0
    page: str = "auto"             # "auto" (flow), absolute "1".."k", or "n","n-1",...
    rotate: int = 0
    scale: float | None = None     # None = fit-to-cell; else explicit factor
    halign: str = "left"           # left | center | right
    valign: str = "top"            # top | center | bottom


@dataclass
class ImpositionSpec:
    page_size: str = "letter"
    page_width: float | None = None
    page_height: float | None = None
    rows: int = 1
    cols: int = 1
    margin_top: float = 0.0
    margin_left: float = 0.0
    h_gap: float = 0.0
    v_gap: float = 0.0
    rotate: int = 0                # default rotation applied to flowed cells
    scale: bool = True            # fit-scale flowed cells
    group_size: int | None = None  # input pages consumed per sheet (default rows*cols)
    cells: list = _field(default_factory=list)   # list[CellSpec]; empty = row-major flow


@dataclass
class Spec:
    process: str | None = None
    inputs: list = _field(default_factory=list)        # list[FileRef]
    outputs: list = _field(default_factory=list)       # list[FileRef]
    index: IndexRef | None = None
    options: dict = _field(default_factory=dict)
    pages_per_document: int | None = None
    boundary: FieldSpec | None = None
    fields: list = _field(default_factory=list)        # list[FieldSpec]
    operations: list = _field(default_factory=list)    # list[op dict]
    imposition: ImpositionSpec | None = None


# --- helpers ---------------------------------------------------------------

def _rect(spec):
    x, y, w, h = (float(v) for v in spec.split(","))
    return Rect(x, y, w, h)


def _len(node, name, default=0.0):
    from units import parse_length
    return parse_length(node.getAttribute(name), default) if node.hasAttribute(name) else default


def _attrs(node):
    out = {}
    if node.attributes:
        for i in range(node.attributes.length):
            a = node.attributes.item(i)
            out[a.name] = a.value
    return out


def _file_refs(parent):
    return [FileRef(f.getAttribute("name"),
                    f.getAttribute("type") or f.getAttribute("file_type") or None)
            for f in parent.getElementsByTagName("file")]


def _identify(node, spec):
    by = (node.getAttribute("by") or "").lower()
    value = node.getAttribute("value")
    if by == "page-count":
        spec.pages_per_document = int(node.getAttribute("pages") or value or "1")
    elif by == "window":
        spec.boundary = FieldSpec("boundary", window=_rect(value))
    elif by == "text":
        spec.boundary = FieldSpec("boundary", text=value)
    elif by == "hex":
        spec.boundary = FieldSpec("boundary", hex=value)


def _field_spec(node):
    name = node.getAttribute("name")
    if node.hasAttribute("window"):
        return FieldSpec(name, window=_rect(node.getAttribute("window")))
    if node.hasAttribute("text"):
        return FieldSpec(name, text=node.getAttribute("text"))
    if node.hasAttribute("hex"):
        return FieldSpec(name, hex=node.getAttribute("hex"))
    return FieldSpec(name)


def _operation(node):
    op = {"verb": node.tagName}
    op.update(_attrs(node))
    text = node.firstChild.data if node.firstChild else None
    if text and text.strip():
        op["_text"] = text.strip()
    return op


def _imposition(node):
    imp = ImpositionSpec()
    imp.page_size = node.getAttribute("page-size") or "letter"
    if node.hasAttribute("page-width"):
        imp.page_width = _len(node, "page-width")
    if node.hasAttribute("page-height"):
        imp.page_height = _len(node, "page-height")
    imp.rows = int(node.getAttribute("rows") or "1")
    imp.cols = int(node.getAttribute("cols") or "1")
    imp.margin_top = _len(node, "margin-top")
    imp.margin_left = _len(node, "margin-left")
    imp.h_gap = _len(node, "h-gap")
    imp.v_gap = _len(node, "v-gap")
    imp.rotate = int(node.getAttribute("rotate") or "0")
    imp.scale = (node.getAttribute("scale") or "true").lower() not in ("false", "0", "none")
    if node.hasAttribute("group-size"):
        imp.group_size = int(node.getAttribute("group-size"))
    for c in node.getElementsByTagName("cell"):
        imp.cells.append(CellSpec(
            row=int(c.getAttribute("row") or "0"),
            col=int(c.getAttribute("col") or "0"),
            page=c.getAttribute("page") or "auto",
            rotate=int(c.getAttribute("rotate") or "0"),
            scale=float(c.getAttribute("scale")) if c.hasAttribute("scale") else None,
            halign=c.getAttribute("halign") or "left",
            valign=c.getAttribute("valign") or "top"))
    return imp


# --- public API ------------------------------------------------------------

def load_spec(path: str) -> Spec:
    return _from_root(minidom.parse(path).documentElement)


def load_spec_string(text: str) -> Spec:
    return _from_root(minidom.parseString(text).documentElement)


def _from_root(root) -> Spec:
    spec = Spec(process=root.getAttribute("process") or None)
    for inputs in root.getElementsByTagName("inputs"):
        spec.inputs.extend(_file_refs(inputs))
    for outputs in root.getElementsByTagName("outputs"):
        spec.outputs.extend(_file_refs(outputs))
    idx = root.getElementsByTagName("index")
    if idx:
        n = idx[0]
        spec.index = IndexRef(
            name=n.getAttribute("name") or None,
            format=n.getAttribute("format") or "json",
            compress=n.getAttribute("compress") or "none",
            level=int(n.getAttribute("level") or "0"))
    opt = root.getElementsByTagName("options")
    if opt:
        spec.options = _attrs(opt[0])
    for node in root.getElementsByTagName("identify"):
        _identify(node, spec)
    for node in root.getElementsByTagName("field"):
        spec.fields.append(_field_spec(node))
    for parent_tag in ("enhancements", "operations"):
        for parent in root.getElementsByTagName(parent_tag):
            for child in parent.childNodes:
                if child.nodeType == child.ELEMENT_NODE and child.tagName in (
                        "add", "delete", "modify", "extract"):
                    spec.operations.append(_operation(child))
    imp = root.getElementsByTagName("imposition")
    if imp:
        spec.imposition = _imposition(imp[0])
    return spec
