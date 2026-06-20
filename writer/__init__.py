""" Writers render the generic model to a concrete print-stream format.

Each writer exposes ``write(document_set, path)``. Writers are the only format-aware
code on the output side; everything upstream works on the model. Register new writers
in ``writer.registry``.
"""
