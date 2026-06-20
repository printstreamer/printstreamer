""" Test configuration: ensure the project root is importable and quiet logging. """

import logging
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

logging.disable(logging.CRITICAL)

from paths import in_data  # noqa: E402  (requires ROOT on sys.path, set just above)

# Sample inputs are referenced by bare filename and resolved from the data directory.
AFP_SAMPLE = in_data("test_afp.afp")
PDF_SAMPLE = in_data("test_pdf.pdf")
