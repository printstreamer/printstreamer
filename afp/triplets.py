""" Universal AFP triplet engine.

Triplets are the self-describing (length, id, content) parameter groups that carry
the bulk of AFP semantics across MO:DCA, IOCA, FOCA and BCOCA structured fields. This
module decodes *every* documented triplet id into named fields so no parameter is
lost, and can rebuild a triplet list back into bytes.

A ``Triplet`` is transient: records use it to populate the normalized model and then
discard it (the model never stores raw structured-field bytes). ``parse_triplets`` is
the single entry point used everywhere a triplet area appears; an optional
``policy`` may suppress decoding of triplets a given process does not need (speed).

Design goals (see plan): share one decoder for all records, leave no unknown
triplets, and stay cheap enough to run on very large streams.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


# --- triplet container -----------------------------------------------------

@dataclass
class Triplet:
    """ One decoded triplet. ``data`` is the content after (length,id); kept only for
    re-emission (``build``) and never stored in the model. """
    tid: int
    name: str
    fields: dict = field(default_factory=dict)
    data: bytes = b""
    unknown: bool = False

    def __repr__(self):
        return f"<Triplet 0x{self.tid:02X} {self.name} {self.fields}>"


# --- decode helpers --------------------------------------------------------

def _u(b):
    return int.from_bytes(b, "big", signed=False)


def _s(b):
    return int.from_bytes(b, "big", signed=True)


def _ebcdic(b):
    try:
        return b.decode("cp500", "replace").rstrip()
    except Exception:
        return b.hex()


# --- individual triplet decoders -------------------------------------------
# Each takes the triplet content bytes (everything after the length+id) and returns
# a dict of named fields. They must never raise on short/odd data.

def _t_cgcsgid(d):
    if len(d) >= 4:
        return {"gcsgid": _u(d[0:2]), "cpgid": _u(d[2:4])}
    if len(d) >= 2:
        return {"cpgid": _u(d[0:2])}
    return {}


# Fully Qualified Name type byte -> meaning.
FQN_TYPES = {
    0x01: "replace_first_gid", 0x07: "begin_resource_group",
    0x08: "media_eject_control", 0x09: "color_attribute_table",
    0x0A: "data_object_external", 0x0B: "data_object_internal",
    0x10: "begin_overlay", 0x41: "font_family", 0x6E: "data_object_external_ref",
    0x7E: "begin_page_group", 0x83: "color_management_resource",
    0x84: "data_object_external", 0x85: "code_page", 0x86: "font_charset",
    0x87: "code_page_index", 0x8D: "begin_medium_map", 0x8E: "coded_font",
    0x9C: "data_object_font", 0xB0: "data_object", 0xBE: "data_object_external",
    0xCA: "index_element_gid", 0xCE: "other_object_data",
    0xD8: "begin_resource", 0xDE: "attribute_gid",
}


def _t_fqn(d):
    if len(d) < 2:
        return {"raw": d.hex()}
    fqn_type = d[0]
    fqn_fmt = d[1]
    body = d[2:]
    name = _ebcdic(body) if fqn_fmt in (0x00,) else (
        _ebcdic(body) if all(0x40 <= c <= 0xFE or c == 0x00 for c in body) else body.hex())
    return {"fqn_type": fqn_type, "fqn_type_name": FQN_TYPES.get(fqn_type, f"0x{fqn_type:02X}"),
            "fqn_format": fqn_fmt, "name": name.strip() if isinstance(name, str) else name}


def _t_mapping_option(d):
    return {"value": d[0]} if d else {}


def _t_object_classification(d):
    out = {}
    if len(d) >= 2:
        out["object_class"] = d[1]
    if len(d) >= 6:
        out["structure_flags"] = _u(d[4:6])
    if len(d) >= 22:
        out["registered_oid"] = d[6:22].hex()
    if len(d) >= 54:
        out["object_type_name"] = _ebcdic(d[22:54])
    return out


def _t_modca_is(d):
    return {"interchange_set": d.hex()}


def _t_ext_resource_local_id(d):
    if len(d) >= 5:
        return {"resource_type": d[0], "resource_local_id": _u(d[1:5])}
    return {"raw": d.hex()}


def _t_resource_local_id(d):
    if len(d) >= 2:
        return {"resource_type": d[0], "resource_local_id": d[1]}
    return {"raw": d.hex()}


def _t_char_rotation(d):
    return {"rotation": _u(d[0:2])} if len(d) >= 2 else {}


def _t_measurement_units(d):
    if len(d) >= 6:
        return {"x_base": d[0], "y_base": d[1],
                "x_units": _u(d[2:4]), "y_units": _u(d[4:6])}
    return {"raw": d.hex()}


def _t_object_area_size(d):
    if len(d) >= 7:
        return {"size_type": d[0], "x_size": _u(d[1:4]), "y_size": _u(d[4:7])}
    return {"raw": d.hex()}


def _t_area_definition(d):
    if len(d) >= 9:
        return {"x_origin": _u(d[0:3]), "y_origin": _u(d[3:6]),
                "x_extent": _u(d[6:9])}
    return {"raw": d.hex()}


def _t_color_specification(d):
    """ X'4E' Color Specification: reserved, color space, reserved(4), bits/component
    x4, then the colour value. Decodes common RGB/CMYK/highlight/gray spaces. """
    if len(d) < 8:
        return {"raw": d.hex()}
    space = d[1]
    bits = d[4:8]
    val = d[8:]
    out = {"color_space": space, "bits_per_component": list(bits)}
    names = {0x01: "rgb", 0x04: "cmyk", 0x06: "highlight", 0x08: "gray",
             0x40: "srgb", 0x02: "fountain"}
    out["color_space_name"] = names.get(space, f"0x{space:02X}")
    if space == 0x01 and len(val) >= 3:
        out["rgb"] = (val[0], val[1], val[2])
    elif space == 0x04 and len(val) >= 4:
        out["cmyk"] = (val[0], val[1], val[2], val[3])
    elif space == 0x08 and len(val) >= 1:
        out["gray"] = val[0]
    else:
        out["value"] = val.hex()
    return out


def _t_encoding_scheme(d):
    return {"encoding_scheme": _u(d[0:2])} if len(d) >= 2 else {}


def _t_u4(name):
    def dec(d):
        return {name: _u(d[0:4])} if len(d) >= 4 else {"raw": d.hex()}
    return dec


def _t_u2(name):
    def dec(d):
        return {name: _u(d[0:2])} if len(d) >= 2 else {"raw": d.hex()}
    return dec


def _t_u1(name):
    def dec(d):
        return {name: d[0]} if d else {}
    return dec


def _t_font_descriptor_spec(d):
    """ X'5D' Font Descriptor Specification (used in MCF / data-object fonts). """
    out = {}
    if len(d) >= 2:
        out["weight_class"] = d[0]
        out["width_class"] = d[1]
    if len(d) >= 4:
        out["height"] = _u(d[2:4])
    if len(d) >= 6:
        out["width"] = _u(d[4:6])
    if len(d) >= 8:
        out["descriptor_flags"] = _u(d[6:8])
    return out


def _t_font_resolution_metric(d):
    """ X'8B' Font Resolution and Metric Technology. """
    out = {}
    if d:
        out["metric_technology"] = d[0]
    if len(d) >= 2:
        out["unit_base"] = d[1]
    if len(d) >= 6:
        out["x_resolution"] = _u(d[2:4])
        out["y_resolution"] = _u(d[4:6])
    return out


def _t_data_object_font(d):
    out = {}
    if len(d) >= 1:
        out["flags"] = d[0]
    if len(d) >= 5:
        out["vertical_size"] = _u(d[3:5])
    if len(d) >= 9:
        out["nominal_vertical_size"] = _u(d[5:7])
        out["nominal_horizontal_size"] = _u(d[7:9])
    return out


def _t_attribute_value(d):
    """ X'36' Attribute Value: reserved(2) then the EBCDIC attribute value. """
    body = d[2:] if len(d) >= 2 else d
    return {"value": _ebcdic(body)}


def _t_text_orientation(d):
    if len(d) >= 4:
        return {"inline_rotation": _u(d[0:2]), "baseline_rotation": _u(d[2:4])}
    return {"raw": d.hex()}


# --- complete triplet registry --------------------------------------------
# name + optional decoder for every documented triplet id. Ids without a bespoke
# decoder still get a name and their content captured as hex (``raw``), so nothing
# is ever "unknown".

_GENERIC = None  # sentinel: name-only, capture raw

TRIPLET_DEFS = {
    0x01: ("coded_graphic_character_set_gid", _t_cgcsgid),
    0x02: ("fully_qualified_name", _t_fqn),
    0x04: ("mapping_option", _t_mapping_option),
    0x06: ("object_area_size_obsolete", _t_object_area_size),
    0x10: ("object_classification", _t_object_classification),
    0x18: ("modca_interchange_set", _t_modca_is),
    0x1F: ("object_function_set_specification", _GENERIC),
    0x21: ("object_function_set_specification", _GENERIC),
    0x22: ("extended_resource_local_id", _t_ext_resource_local_id),
    0x23: ("metric_adjustment", _GENERIC),
    0x24: ("resource_local_id", _t_resource_local_id),
    0x25: ("resource_section_number", _t_u1("section")),
    0x26: ("character_rotation", _t_char_rotation),
    0x2D: ("object_byte_offset", _t_u4("byte_offset")),
    0x36: ("attribute_value", _t_attribute_value),
    0x43: ("descriptor_position", _t_u1("position_id")),
    0x45: ("media_eject_control", _GENERIC),
    0x46: ("page_overlay_conditional_processing", _GENERIC),
    0x47: ("resource_usage_attribute", _GENERIC),
    0x4B: ("measurement_units", _t_measurement_units),
    0x4C: ("object_area_size", _t_object_area_size),
    0x4D: ("area_definition", _t_area_definition),
    0x4E: ("color_specification", _t_color_specification),
    0x50: ("encoding_scheme_id", _t_encoding_scheme),
    0x56: ("medium_map_page_number", _t_u2("page_number")),
    0x57: ("object_byte_extent", _t_u4("byte_extent")),
    0x58: ("object_structured_field_offset", _t_u4("sf_offset")),
    0x59: ("object_structured_field_extent", _t_u4("sf_extent")),
    0x5A: ("object_offset", _t_u4("offset")),
    0x5D: ("font_descriptor_specification", _t_font_descriptor_spec),
    0x5E: ("data_object_object_offset", _GENERIC),
    0x62: ("font_horizontal_scale_factor", _t_u2("scale")),
    0x63: ("object_count", _t_u2("count")),
    0x64: ("local_date_and_time_stamp", _GENERIC),
    0x65: ("comment", _GENERIC),
    0x68: ("medium_orientation", _t_u1("orientation")),
    0x6C: ("resource_object_include", _GENERIC),
    0x70: ("presentation_space_reset_mixing", _t_u1("reset")),
    0x71: ("presentation_space_mixing_rule", _GENERIC),
    0x72: ("universal_date_and_time_stamp", _GENERIC),
    0x73: ("toner_saver", _t_u1("toner_saver")),
    0x74: ("color_fidelity", _GENERIC),
    0x75: ("font_fidelity", _GENERIC),
    0x78: ("attribute_qualifier", _GENERIC),
    0x79: ("page_position_information", _GENERIC),
    0x80: ("toner_saver", _t_u1("toner_saver")),
    0x81: ("color_fidelity", _GENERIC),
    0x83: ("font_fidelity", _GENERIC),
    0x84: ("metric_adjustment", _GENERIC),
    0x85: ("attribute_qualifier", _GENERIC),
    0x86: ("font_resolution_metric_technology", _t_font_resolution_metric),
    0x87: ("finishing_operation", _GENERIC),
    0x88: ("text_fidelity", _GENERIC),
    0x8B: ("font_resolution_and_metric_technology", _t_font_resolution_metric),
    0x8C: ("finishing_operation", _GENERIC),
    0x8D: ("text_fidelity", _GENERIC),
    0x8E: ("media_fidelity", _GENERIC),
    0x8F: ("finishing_fidelity", _GENERIC),
    0x90: ("font_position", _GENERIC),
    0x91: ("data_object_font_descriptor", _t_data_object_font),
    0x92: ("locale_selector", _GENERIC),
    0x93: ("up3i_finishing_operation", _GENERIC),
    0x95: ("up3i_finishing_operation", _GENERIC),
    0x96: ("color_management_resource_descriptor", _GENERIC),
    0x97: ("invoke_cmr", _GENERIC),
    0x98: ("rendering_intent", _GENERIC),
    0x9A: ("rendering_intent", _GENERIC),
    0x9C: ("device_appearance", _GENERIC),
    0x9D: ("image_resolution", _t_font_resolution_metric),
    0x9E: ("object_container_presentation_space_size", _GENERIC),
    0x9F: ("media_eject_control", _GENERIC),
    0xA1: ("image_resolution", _t_font_resolution_metric),
    0xA8: ("object_container_presentation_space_size", _GENERIC),
    0xB4: ("data_object_font_descriptor", _t_data_object_font),
    0xB5: ("linked_font_descriptor", _GENERIC),
    0xF7: ("text_orientation", _t_text_orientation),
}


def triplet_name(tid: int) -> str:
    entry = TRIPLET_DEFS.get(tid)
    return entry[0] if entry else f"unknown_0x{tid:02X}"


# --- public API ------------------------------------------------------------

def decode_triplet(tid: int, content: bytes) -> Triplet:
    entry = TRIPLET_DEFS.get(tid)
    if entry is None:
        logger.warning("Unknown AFP triplet id 0x%02X (%d bytes)", tid, len(content))
        return Triplet(tid=tid, name=f"unknown_0x{tid:02X}",
                       fields={"raw": content.hex()}, data=content, unknown=True)
    name, decoder = entry
    fields = {}
    if decoder is not None:
        try:
            fields = decoder(content)
        except Exception:
            logger.exception("Triplet 0x%02X decode error; capturing raw", tid)
            fields = {"raw": content.hex()}
    else:
        fields = {"raw": content.hex()} if content else {}
    return Triplet(tid=tid, name=name, fields=fields, data=content)


def parse_triplets(data: bytes, policy=None) -> list[Triplet]:
    """ Walk a triplet area into a list of decoded ``Triplet`` objects.

    Each triplet is ``length(1) id(1) content(length-2)``. A zero/short length stops
    the walk (defensive). ``policy.wants_triplet(tid)`` may skip decoding (the bytes
    are still consumed so the walk stays in sync).
    """
    out = []
    i = 0
    n = len(data)
    while i + 1 < n:
        length = data[i]
        if length < 2 or i + length > n:
            break
        tid = data[i + 1]
        content = data[i + 2:i + length]
        if policy is None or policy.wants_triplet(tid):
            out.append(decode_triplet(tid, content))
        i += length
    return out


def find(triplets: list[Triplet], tid: int) -> Triplet | None:
    for t in triplets:
        if t.tid == tid:
            return t
    return None


def find_all(triplets: list[Triplet], tid: int) -> list[Triplet]:
    return [t for t in triplets if t.tid == tid]


def build(triplets: list[Triplet]) -> bytes:
    """ Re-emit a triplet list to bytes (uses each triplet's preserved content). """
    out = bytearray()
    for t in triplets:
        content = t.data or b""
        out += bytes([len(content) + 2, t.tid]) + content
    return bytes(out)


def scan_unknowns(data: bytes) -> list[int]:
    """ Return the ids of any triplets in ``data`` not in the registry (for tests). """
    return [t.tid for t in parse_triplets(data) if t.unknown]
