""" Central data directory: the default working location for sample inputs,
generated outputs, and index files.

All code resolves *bare* filenames (no directory component) against this directory,
so a process file can say ``name="test_afp.afp"`` and have it picked up from the data
directory automatically. The location defaults to ``<project root>/data`` and can be
overridden with the ``PRINTSTREAMER_DATA_DIR`` environment variable.
"""

import os

# Repo root = the directory containing this module (flat layout).
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))


def data_dir() -> str:
    """ The data directory: env ``PRINTSTREAMER_DATA_DIR`` if set, else ``<root>/data``. """
    return os.environ.get("PRINTSTREAMER_DATA_DIR") or os.path.join(PROJECT_ROOT, "data")


def ensure_data_dir() -> str:
    """ Return the data directory, creating it if it does not yet exist. """
    directory = data_dir()
    os.makedirs(directory, exist_ok=True)
    return directory


def in_data(name: str) -> str:
    """ Resolve a *bare* filename against the data directory.

    Absolute paths and paths that already contain a directory component are returned
    unchanged, so explicit paths (e.g. ``examples/letter.psml``) are respected and only
    plain filenames are redirected into the data directory.
    """
    if not name or os.path.isabs(name) or os.path.dirname(name):
        return name
    return os.path.join(data_dir(), name)
