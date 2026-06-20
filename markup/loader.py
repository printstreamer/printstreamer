""" Load a PSML XML file into the markup AST (markup.model). """

from __future__ import annotations

from xml.dom import minidom

from markup.model import Markup, Node, PageMaster


def _to_node(element) -> Node:
    props = {}
    if element.attributes:
        for i in range(element.attributes.length):
            attr = element.attributes.item(i)
            props[attr.name] = attr.value
    node = Node(tag=element.tagName, props=props)
    text_parts = []
    for child in element.childNodes:
        if child.nodeType == child.ELEMENT_NODE:
            child_node = _to_node(child)
            node.children.append(child_node)
            node.content.append(child_node)
        elif child.nodeType in (child.TEXT_NODE, child.CDATA_SECTION_NODE):
            text_parts.append(child.data)
            if child.data.strip():
                node.content.append(child.data)
    text = "".join(text_parts)
    # Keep meaningful text; collapse pure-whitespace to None.
    node.text = text if text.strip() else None
    return node


def _page_master(node: Node) -> PageMaster:
    pm = PageMaster(name=node.get("name", "default"))
    pm.width = node.length("page-width", pm.width)
    pm.height = node.length("page-height", pm.height)
    # margin shorthand then per-side overrides
    if node.get("margin"):
        m = node.length("margin")
        pm.margin_top = pm.margin_right = pm.margin_bottom = pm.margin_left = m
    pm.margin_top = node.length("margin-top", pm.margin_top)
    pm.margin_right = node.length("margin-right", pm.margin_right)
    pm.margin_bottom = node.length("margin-bottom", pm.margin_bottom)
    pm.margin_left = node.length("margin-left", pm.margin_left)
    pm.columns = int(node.get("columns", "1"))
    pm.column_gap = node.length("column-gap", pm.column_gap)
    pm.header_extent = node.length("header-extent", 0.0)
    pm.footer_extent = node.length("footer-extent", 0.0)
    header = node.first("header")
    footer = node.first("footer")
    if header is not None:
        pm.header = header.children
        if not pm.header_extent:
            pm.header_extent = header.length("extent", 36.0)
    if footer is not None:
        pm.footer = footer.children
        if not pm.footer_extent:
            pm.footer_extent = footer.length("extent", 36.0)
    return pm


def _collect_styles(node: Node, styles: dict):
    for style in node.find("style"):
        name = style.get("name")
        if name:
            styles[name] = {k: v for k, v in style.props.items() if k != "name"}


def load(path: str) -> Markup:
    """ Parse a PSML file into a Markup AST. """
    dom = minidom.parse(path)
    root = _to_node(dom.documentElement)
    return load_node(root)


def load_string(text: str) -> Markup:
    dom = minidom.parseString(text)
    return load_node(_to_node(dom.documentElement))


def load_node(root: Node) -> Markup:
    markup = Markup(props=dict(root.props))
    # A <defines>/<declarations> block or top-level definitions both work.
    scope = root
    for master in scope.find("master-page"):
        pm = _page_master(master)
        markup.masters[pm.name] = pm
    _collect_styles(scope, markup.styles)
    for res_tag in ("font", "color", "image-resource", "overlay", "page-segment",
                    "object-container", "medium-map"):
        markup.resources.extend(scope.find(res_tag))
    markup.sequences = scope.find("page-sequence")
    # Convenience: allow a bare <document> with direct <flow> and a default master.
    if not markup.sequences and scope.first("flow") is not None:
        markup.sequences = [scope]
    if not markup.masters:
        markup.masters["default"] = PageMaster(name="default")
    return markup
