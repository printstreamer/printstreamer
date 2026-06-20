""" PSML — PrintStream Markup Language.

A custom XML vocabulary inspired by XSL-FO for generating print streams. It keeps
FO's strengths (automatic text flow, pagination, keeps, widow/orphan control) while
adding AFP-native concepts (overlays, medium maps, page segments, object containers,
structured fields) and mapping cleanly onto the generic model. All measurements are
in printer points (1/72 inch). See SCHEMA.md for the full vocabulary.

Pipeline: loader (XML -> markup AST) -> layout engine (AST -> generic model) ->
writers (+ document and page index files). Surfaced as the ``compose`` process.
"""

from markup.compose import compose

__all__ = ["compose"]
