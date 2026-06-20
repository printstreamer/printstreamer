""" Query, selection, and edit helpers over the generic model.

These functions are the format-agnostic engine behind extraction, deletion,
modification, indexing, and merging. A *scope* is anything iterable into pages: a
``Page``, ``Document``, ``StreamDocumentSet``, or a list of those. Selectors return
``Match`` records that keep page/document context so edits know where to act.

Selection styles required by the engine:
- by text   : substring or regex match on a TextElement's decoded text
- by hex    : byte-sequence match on an element's source/encoded bytes
- by window : elements whose bbox falls within an (x, y, width, height) rectangle
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from model.document import Document, StreamDocumentSet
from model.element import Element, ElementKind, TextElement
from model.geometry import Rect
from model.page import Page


@dataclass
class Match:
    element: Element
    page: Page
    document: Document | None = None


def _iter_context(scope):
    """ Yield (document, page) pairs for any scope. """
    if isinstance(scope, StreamDocumentSet):
        yield from scope.iter_pages()
    elif isinstance(scope, Document):
        for page in scope.pages:
            yield scope, page
    elif isinstance(scope, Page):
        yield None, scope
    elif isinstance(scope, (list, tuple)):
        for item in scope:
            yield from _iter_context(item)
    else:
        raise TypeError(f"Unsupported scope: {type(scope)!r}")


def iter_elements(scope, kind: ElementKind | None = None):
    """ Yield Match records for every element in scope, optionally filtered by kind. """
    for document, page in _iter_context(scope):
        for element in page.elements:
            if kind is None or element.kind == kind:
                yield Match(element, page, document)


def select_by_text(scope, pattern: str, regex: bool = False,
                   ignore_case: bool = False, kind: ElementKind | None = ElementKind.TEXT):
    """ Select elements whose text matches ``pattern`` (substring or regex). """
    flags = re.IGNORECASE if ignore_case else 0
    compiled = re.compile(pattern, flags) if regex else None
    needle = pattern.lower() if ignore_case else pattern
    results = []
    for match in iter_elements(scope, kind):
        el = match.element
        text = getattr(el, "text", None) or getattr(el, "data", None)
        if not isinstance(text, str):
            continue
        hay = text.lower() if ignore_case else text
        if (compiled.search(text) if compiled else needle in hay):
            results.append(match)
    return results


def select_by_hex(scope, hex_or_bytes, kind: ElementKind | None = None):
    """ Select elements whose source bytes contain the given hex/byte sequence. """
    if isinstance(hex_or_bytes, str):
        target = bytes.fromhex(hex_or_bytes.replace(" ", ""))
    else:
        target = bytes(hex_or_bytes)
    return [m for m in iter_elements(scope, kind)
            if target in m.element.source_bytes()]


def select_in_window(scope, window: Rect, contained: bool = True,
                     kind: ElementKind | None = None):
    """ Select elements whose bbox falls inside ``window`` (x, y origin + w/h).

    With ``contained`` True the element's whole bbox must lie within the window;
    otherwise any intersection counts.
    """
    results = []
    for match in iter_elements(scope, kind):
        bbox = match.element.bbox
        if bbox is None:
            continue
        if (window.contains_rect(bbox) if contained else window.intersects(bbox)):
            results.append(match)
    return results


def text_in_window(element, window: Rect) -> str:
    """ Return only the characters of a text element that fall within ``window``.

    Uses the per-character advances captured at parse time (``attributes["char_advances"]``)
    to clip a run horizontally, so a window cutting through a line yields exactly the
    in-window characters. Falls back to the whole text when advances are unavailable. """
    text = getattr(element, "text", "") or ""
    advances = (element.attributes or {}).get("char_advances")
    if not text or not advances or getattr(element, "orientation", 0) % 360 != 0:
        return text
    x = element.position.x
    x0, x1 = window.x, window.x + window.width
    kept = []
    for ch, adv in zip(text, advances):
        cx0, cx1 = x, x + adv
        # include the character if its horizontal centre lies within the window
        if x0 <= (cx0 + cx1) / 2.0 <= x1:
            kept.append(ch)
        x = cx1
    return "".join(kept)


# --- edit operations -------------------------------------------------------

def remove(matches) -> int:
    """ Remove the matched elements from their pages. Returns the count removed. """
    count = 0
    for match in matches:
        if match.element in match.page.elements:
            match.page.elements.remove(match.element)
            _release_resources(match)
            count += 1
    return count


def replace(match: Match, new_element: Element) -> None:
    """ Replace a matched element in place, preserving z-order. """
    idx = match.page.elements.index(match.element)
    new_element.z_order = match.element.z_order
    match.page.elements[idx] = new_element


def add(page: Page, element: Element, resource_library=None) -> Element:
    """ Add an element to a page, registering any resource references. """
    page.add_element(element)
    ref = getattr(element, "resource_ref", None) or getattr(element, "font_ref", None)
    if ref:
        page.resources_used.add(ref)
        if resource_library is not None:
            resource_library.reference(ref)
    return element


def _release_resources(match: Match) -> None:
    ref = getattr(match.element, "resource_ref", None) or getattr(match.element, "font_ref", None)
    if ref and match.document is not None:
        match.document.resource_library.dereference(ref)
