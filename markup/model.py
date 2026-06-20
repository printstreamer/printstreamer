""" PSML markup AST and style resolution.

The AST is a generic ``Node`` tree (tag + props + children + text) so the vocabulary
can grow without code churn and unknown constructs are preserved. A parsed
``Markup`` collects the reusable pieces: page masters, named styles, resources, and
the page sequences that carry document content.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from units import parse_length


@dataclass
class Node:
    """ A generic markup element. """
    tag: str
    props: dict = field(default_factory=dict)
    children: list = field(default_factory=list)   # list[Node]
    text: str | None = None
    content: list = field(default_factory=list)    # ordered inline items: str | Node

    def get(self, name, default=None):
        return self.props.get(name, default)

    def length(self, name, default=0.0):
        return parse_length(self.props.get(name), default)

    def find(self, tag):
        return [c for c in self.children if c.tag == tag]

    def first(self, tag):
        for c in self.children:
            if c.tag == tag:
                return c
        return None


@dataclass
class PageMaster:
    """ A page template: geometry, margins, columns, and header/footer regions. """
    name: str
    width: float = 612.0
    height: float = 792.0
    margin_top: float = 72.0
    margin_right: float = 72.0
    margin_bottom: float = 72.0
    margin_left: float = 72.0
    columns: int = 1
    column_gap: float = 12.0
    header_extent: float = 0.0
    footer_extent: float = 0.0
    header: list = field(default_factory=list)     # list[Node] (block content)
    footer: list = field(default_factory=list)

    @property
    def body_left(self):
        return self.margin_left

    @property
    def body_right(self):
        return self.width - self.margin_right

    @property
    def body_top(self):
        return self.margin_top + self.header_extent

    @property
    def body_bottom(self):
        return self.height - self.margin_bottom - self.footer_extent

    def column_width(self):
        usable = self.body_right - self.body_left - (self.columns - 1) * self.column_gap
        return usable / self.columns


@dataclass
class Markup:
    """ A parsed PSML document. """
    masters: dict = field(default_factory=dict)    # name -> PageMaster
    styles: dict = field(default_factory=dict)     # name -> dict of props
    sequences: list = field(default_factory=list)  # list[Node] (page-sequence)
    resources: list = field(default_factory=list)  # list[Node] (font/color/image defs)
    props: dict = field(default_factory=dict)


# Properties that cascade from a block/style to its inline children.
INHERITED = {
    "font", "font-family", "size", "font-size", "color", "weight", "font-weight",
    "style", "font-style", "line-height", "text-align", "letter-spacing", "language",
}


def resolve_style(node: Node, styles: dict, inherited: dict | None = None) -> dict:
    """ Merge a named style (``style=`` ref), inline props, and inherited props into
    one effective property dict for ``node``. Inline props win over the named style,
    which wins over inherited. """
    effective = dict(inherited or {})
    named = node.props.get("style")
    if named and named in styles:
        effective.update(styles[named])
    for k, v in node.props.items():
        if k != "style":
            effective[k] = v
    return effective


def inheritable(effective: dict) -> dict:
    """ The subset of an effective style that cascades to children. """
    return {k: v for k, v in effective.items() if k in INHERITED}
