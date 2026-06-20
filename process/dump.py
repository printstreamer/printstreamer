""" Serialize the in-memory model to a file for inspection/debugging. """

import json

from model.element import ElementKind


def _element_dict(element):
    bbox = element.bbox
    out = {
        "kind": element.kind.value,
        "z_order": element.z_order,
        "bbox": [bbox.x, bbox.y, bbox.width, bbox.height] if bbox else None,
    }
    if element.kind == ElementKind.TEXT:
        out.update(text=element.text, font_ref=element.font_ref,
                   font_size=element.font_size,
                   position=[element.position.x, element.position.y])
    elif element.kind == ElementKind.LINE:
        out.update(start=[element.start.x, element.start.y],
                   end=[element.end.x, element.end.y], weight=element.weight)
    elif element.kind == ElementKind.BARCODE:
        out.update(symbology=element.symbology, data=element.data)
    elif element.kind == ElementKind.IMAGE:
        out.update(encoding=element.encoding, resource_ref=element.resource_ref,
                   bytes=len(element.data) if element.data else 0)
    if element.source_ref is not None:
        out["source"] = {"record_type": element.source_ref.record_type,
                         "byte_offset": element.source_ref.byte_offset}
    return out


def _page_dict(page):
    return {
        "number": page.number,
        "size": [page.size.width, page.size.height],
        "attributes": {k: v for k, v in page.attributes.items()
                       if isinstance(v, (str, int, float, bool))},
        "elements": [_element_dict(e) for e in page.ordered_elements()],
    }


def model_to_dict(document_set):
    return {
        "documents": [
            {
                "name": doc.name,
                "page_count": doc.page_count,
                "pages": [_page_dict(p) for p in doc.pages],
            }
            for doc in document_set.documents
        ]
    }


def dump_model(document_set, path: str) -> str:
    """ Write a JSON dump of the model to ``path``. Returns the path. """
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(model_to_dict(document_set), fh, indent=2)
    return path
