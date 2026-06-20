""" Test configuration: ensure the project root is importable and quiet logging. """

import logging
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

logging.disable(logging.CRITICAL)

AFP_SAMPLE = os.path.join(ROOT, "test_afp.afp")
PDF_SAMPLE = os.path.join(ROOT, "test_pdf.pdf")
