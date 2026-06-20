""" Unit tests for JSL parsing and JSL/DJDE-driven Metacode parsing. """

from metacode.jsl import JslConfig, default_jsl_path, load_jsl, parse_jsl
from metacode.parser import MetacodeParser


def test_bundled_jsl_settings():
    path = default_jsl_path()
    assert path, "config/metacode.jsl should be bundled"
    cfg = load_jsl(path)
    assert cfg.djde_prefix == "$DJDE$"
    assert cfg.djde_offset == 2 and cfg.djde_skip == 9
    assert round(cfg.page_width) == 612 and round(cfg.page_height) == 792
    assert cfg.dpi == 300
    assert cfg.fonts and "L0112" in cfg.fonts


def test_parse_jsl_defaults_when_silent():
    cfg = parse_jsl("ONLINE: JDL;\n  SYSTEM PFFORMAT=NONE;\n  END;")
    assert cfg.djde_prefix == "$DJDE$"        # default when no IDEN given
    assert cfg.dpi == 300


def test_djde_record_recognized_and_applied():
    """ A record carrying the JSL prefix is parsed as a DJDE (preserved), not as orders;
    a following text order still renders on the page. """
    cfg = JslConfig()                          # defaults: $DJDE$, cp500
    pages = []
    mp = MetacodeParser(lambda w, h, els: pages.append(els), jsl=cfg)

    def rec(body):
        return bytes([len(body)]) + body

    djde = "$DJDE$ FONTINDEX=(0,L0112,1),FORMAT=FORM01,END;".encode("cp500")
    text = "Hi".encode("cp500")
    stream = (rec(djde)
              + rec(bytes([0xC1]) + (300).to_bytes(2, "big"))      # SET_X
              + rec(bytes([0xC3, len(text)]) + text)               # TEXT
              + rec(bytes([0xFF])))                                # ENDPG
    mp.parse(stream)
    assert len(pages) == 1
    kinds = [e.kind.value for e in pages[0]]
    assert "container" in kinds                # DJDE preserved
    assert any(getattr(e, "text", "") == "Hi" for e in pages[0])
