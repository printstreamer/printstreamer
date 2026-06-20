""" Generate n-up label sheets from index records and a PSML label template. """

from __future__ import annotations

import logging
import re

from labels.stock import get_stock
from markup import loader
from markup.layout import LayoutEngine
from model.document import Document, StreamDocumentSet
from model.geometry import Rect
from process.imposition import grid_cells, transform_element

logger = logging.getLogger(__name__)

_FIELD = re.compile(r"\{(\w+)\}")

_LABEL_DOC = """<document>
  <master-page name="L" page-width="{w}" page-height="{h}"
     margin-top="{pad}" margin-bottom="{pad}" margin-left="{pad}" margin-right="{pad}"/>
  <page-sequence master="L"><flow>{body}</flow></page-sequence>
</document>"""


def _fill(template: str, fields: dict) -> str:
    return _FIELD.sub(lambda m: str(fields.get(m.group(1), "")), template)


def generate_labels(records, label_template: str, stock_name: str,
                    padding: float = 4.0) -> StreamDocumentSet:
    """ Build label sheets.

    :param records: iterable of IndexRecord (each record's ``fields`` fills one label)
    :param label_template: a PSML flow fragment with ``{field}`` placeholders
    :param stock_name: a key in labels.stock.STOCKS
    :returns: a StreamDocumentSet of label sheets
    """
    stock = get_stock(stock_name)
    out = StreamDocumentSet()
    doc = out.add_document(Document(name="labels"))
    cells = list(grid_cells(stock.page_size, stock.rows, stock.cols,
                            margin_top=stock.margin_top, margin_left=stock.margin_left,
                            h_pitch=stock.h_pitch, v_pitch=stock.v_pitch,
                            cell_width=stock.label_width, cell_height=stock.label_height))
    sheet = None
    for i, record in enumerate(records):
        slot = i % stock.per_sheet
        if slot == 0:
            sheet = _new_sheet(doc, stock.page_size)
        cell = cells[slot]
        body = _fill(label_template, getattr(record, "fields", {}) or {})
        markup = loader.load_string(_LABEL_DOC.format(
            w=stock.label_width, h=stock.label_height, pad=padding, body=body))
        label_pages = LayoutEngine(markup).run().all_pages()
        if not label_pages:
            continue
        for element in label_pages[0].ordered_elements():
            sheet.add_element(transform_element(element, 1.0, 1.0, cell.x, cell.y))
    logger.info("Generated %d label sheet(s) on %s", doc.page_count, stock_name)
    return out


def _new_sheet(doc, page_size: Rect):
    from model.page import Page
    return doc.add_page(Page(number=len(doc.pages) + 1, size=page_size))
