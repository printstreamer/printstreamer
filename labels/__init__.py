""" Label printing: n-up label sheets generated from an index file via PSML.

Per R8, labels are produced by the generation (compose) path: a label template (PSML
fragment) is filled from each index record's fields and placed into the cells of a
common label stock. Reuses the layout engine and imposition geometry.
"""

from labels.generate import generate_labels

__all__ = ["generate_labels"]
