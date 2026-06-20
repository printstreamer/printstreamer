""" A restricted PostScript interpreter that parses common print-stream PostScript
and EPS into the generic model. It implements the standard imaging operators used by
print streams (path construction, stroke/fill, text, fonts, colour, CTM, showpage);
constructs it does not model are skipped rather than failing. PostScript is
Turing-complete, so full fidelity is out of scope — see Phase 5 notes.
"""
