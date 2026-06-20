""" Collect a representative set of sample printstream files into the data directory.

This utility builds a small, ready-to-use corpus of print streams for testing and
demos. It does two things:

  1. Downloads real, public-domain sample files for each major printstream engine —
     PDF, PostScript (PS), and PCL — plus a real AFP (MO:DCA) structured document.
  2. Locally synthesizes a Xerox Metacode sample (no public Metacode sample exists),
     so every engine the project supports is represented.

Each collected file is then classified by its magic-byte signature and bucketed into a
size tier, and the results are written to a JSON manifest (``printstream_test_report.json``)
that downstream test runners can consume.

Everything is written into the project's central data directory (see ``paths.py``),
which is the default working directory for the whole project. By default that is
``<project root>/data``; override it with the ``PRINTSTREAMER_DATA_DIR`` environment
variable or the ``--data-dir`` flag.

Usage:
    python scripts/sample_printstream_file_collection.py [--data-dir DIR]
"""

import argparse
import os
import sys
import urllib.request

import json

# The script lives in scripts/; make the project root importable so we share the one
# definition of the data directory with the rest of the codebase.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from paths import ensure_data_dir  # noqa: E402

# Download/socket timeout (seconds): keeps a stalled server from hanging the run.
DOWNLOAD_TIMEOUT = 30

# Filename of the JSON manifest, written inside the data directory.
REPORT_OUTPUT = "printstream_test_report.json"

# 1. Comprehensive download matrix across distinct printstream engines. Each URL is a
#    real, direct-download sample file (verified to return the expected file content).
DOWNLOAD_TARGETS = {
    # PORTABLE DOCUMENT FORMAT (PDF) TARGETS
    "PDF_Small_Interactive": {
        "url": "https://raw.githubusercontent.com/OpenPrinting/sample-files/main/pdf/letter-portrait-vector-color.pdf",
        "ext": ".pdf"
    },
    "PDF_Medium_Payload": {
        "url": "https://raw.githubusercontent.com/OpenPrinting/sample-files/main/pdf/a3-portrait-vector-color.pdf",
        "ext": ".pdf"
    },

    # ADOBE POSTSCRIPT (PS) TARGETS
    "PostScript_Small_Vector": {
        "url": "https://raw.githubusercontent.com/OpenPrinting/cups/master/examples/onepage-letter.ps",
        "ext": ".ps"
    },
    "PostScript_Medium_Layout": {
        "url": "https://raw.githubusercontent.com/OpenPrinting/cups/master/examples/document-letter.ps",
        "ext": ".ps"
    },

    # PRINTER COMMAND LANGUAGE (PCL) TARGETS
    "PCL_Technical_Matrix": {
        "url": "https://raw.githubusercontent.com/kanton-aargau/pcl-viewer/master/test/owl.pcl",
        "ext": ".pcl"
    },
    "PCL_Macro_Overlay": {
        "url": "https://raw.githubusercontent.com/kanton-aargau/pcl-viewer/master/test/grashopp.pcl",
        "ext": ".pcl"
    },

    # ADVANCED FUNCTION PRINTING (AFP / MO:DCA) TARGETS
    "AFP_Structured_Document": {
        "url": "https://raw.githubusercontent.com/yan74/afplib/master/org.afplib/testdata/bim.afp",
        "ext": ".afp"
    }
}

# 2. Industry-standard Magic Bytes (File Signatures) for validation logic.
MAGIC_BYTES = {
    b"%PDF": "Portable Document Format (PDF)",
    b"%!PS": "Adobe PostScript (PS)",
    b"\x1b%-12345": "HP PCL / PJL (Universal Exit Language)",
    b"\x1bE": "HP Printer Command Language (PCL 5/6)",
    b"\x5a": "Advanced Function Printing (AFP / MO:DCA)",
    b"\x1b\x5b\x4b": "Xerox Metacode Stream Engine"
}

# Hints that a "download" actually returned an HTML error/landing page rather than a file.
HTML_SNIFF = (b"<!", b"<html", b"<HTML", b"<?xml")

# Canonical sample printstream files this corpus is expected to contain: every download
# target, the generated Metacode sample, and the pre-existing AFP/PDF inputs the test
# suite relies on. The manifest tags each file "known" so these are easy to assert on.
KNOWN_SAMPLES = (
    {f"{label}{t['ext']}" for label, t in DOWNLOAD_TARGETS.items()}
    | {"Metacode_Generated_Mock.met", "test_afp.afp", "test_pdf.pdf"}
)


def _looks_like_expected(header, ext):
    """ True if the file header matches a known signature consistent with its extension.
    Used only to warn — some genuine samples (e.g. HP-GL/2 PCL) start with a different
    escape sequence than the canonical one and are still valid. """
    if header.startswith(HTML_SNIFF):
        return False
    return any(header.startswith(magic) for magic in MAGIC_BYTES)


def download_and_generate_payloads(data_dir):
    """ Fetch public-domain streams and write the locally synthesized Metacode sample. """
    print("\n--- Initiating Document Ingestion Layer ---")

    for label, target in DOWNLOAD_TARGETS.items():
        dest_path = os.path.join(data_dir, f"{label}{target['ext']}")
        if os.path.exists(dest_path):
            print(f" [*] Record exists in data directory: {label}")
            continue
        try:
            print(f"[~] Fetching printstream bundle for: {label}...")
            # A standard User-Agent header keeps some servers from blocking the request.
            req = urllib.request.Request(
                target['url'],
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            )
            with urllib.request.urlopen(req, timeout=DOWNLOAD_TIMEOUT) as response, \
                    open(dest_path, 'wb') as out_file:
                payload = response.read()
                out_file.write(payload)
            # Sanity-check the bytes: warn (don't fail) if we likely got an HTML page or
            # an unexpected signature, so a moved/renamed URL is easy to spot.
            if not _looks_like_expected(payload[:8], target['ext']):
                print(f" [!] Warning: {label} content does not match an expected "
                      f"signature (header={payload[:8].hex().upper()}); the source URL "
                      f"may have moved.")
            else:
                print(f" [+] Ingested successfully: {dest_path}")
        except Exception as e:
            print(f" [-] Network ingestion error on resource {label}: {e}")
            # Don't leave a partial/empty file behind to confuse the manifest step.
            if os.path.exists(dest_path):
                os.remove(dest_path)

    # Generate a localized Metacode sample: no public Xerox Metacode stream exists, so we
    # synthesize one that is consistent with the bundled JSL (config/metacode.jsl). The
    # JSL supplies the DJDE prefix, encoding, fonts, and page geometry, so the same JSL
    # round-trips this file back to a page when parsing.
    metacode_path = os.path.join(data_dir, "Metacode_Generated_Mock.met")
    print("[~] Programmatically synthesizing JSL-consistent Xerox Metacode stream...")
    with open(metacode_path, "wb") as f:
        f.write(_build_metacode_sample())
    print(f" [+] Generated JSL-consistent Metacode asset: {metacode_path}")


def _build_metacode_sample():
    """ Build a small JSL-consistent Metacode order stream.

    Layout (each record is length-prefixed): a leading ``ESC [ K`` marker record (keeps
    the recognizable Metacode magic and is skipped by the parser), a DJDE descriptor
    record using the JSL's prefix, then SET_X/SET_Y/FONT/TEXT/ENDPG orders using the
    JSL's encoding, fonts, and resolution.
    """
    from metacode.jsl import load_jsl, default_jsl_path

    jsl = load_jsl(default_jsl_path()) if default_jsl_path() else None
    prefix = jsl.djde_prefix if jsl else "$DJDE$"
    encoding = jsl.encoding if jsl else "cp500"
    dpi = jsl.dpi if jsl else 300

    def rec(body):
        return bytes([len(body)]) + body

    # Marker record: 27-byte body beginning 0x5B 0x4B so the file header is 1B 5B 4B.
    marker = (b"\x5b\x4b" + b"XEROX METACODE (JSL)")[:27].ljust(27, b" ")
    out = bytearray(rec(marker))

    # DJDE descriptor (recognized via the JSL IDEN prefix; preserved on parse).
    djde = f"{prefix} JDE=ONLINE,JDL=ONLINE,FONTINDEX=(0,L0112,1),FORMAT=FORM01,END;"
    out += rec(djde.encode(encoding, "replace"))

    # One page of text at 1in,1in using font index 0.
    x = y = dpi  # 1 inch in dots
    out += rec(bytes([0xC2, 0x00]))                       # FONT 0
    out += rec(bytes([0xC1]) + x.to_bytes(2, "big"))      # SET_X
    out += rec(bytes([0xC0]) + y.to_bytes(2, "big"))      # SET_Y
    msg = "Hello Metacode (JSL-driven sample)".encode(encoding, "replace")
    out += rec(bytes([0xC3, len(msg)]) + msg)             # TEXT
    out += rec(bytes([0xFF]))                             # ENDPG
    return bytes(out)


def isolate_tier(size_bytes):
    """ Categorizes test objects based on structural payload sizes. """
    kb = size_bytes / 1024
    if kb < 500:
        return "Small", "Low (Simple strings, discrete asset coordinates, scalar variables)"
    elif kb < 10240:
        return "Medium", "Medium (Aggregated data streams, structural business forms, multi-page grids)"
    else:
        return "Large", "High (Production density spools, raster fonts, multi-document overlays)"


def build_json_manifest(data_dir):
    """ Analyzes collected files to construct an actionable test runner schema. """
    print("\n--- Constructing Programmatic JSON Manifest ---")

    manifest = {
        "pipeline_signature": "Printstream Automated Automation Target Matrix",
        "data_directory": os.path.abspath(data_dir),
        "active_test_assets_found": 0,
        "test_suite_registry": []
    }

    report_path = os.path.join(data_dir, REPORT_OUTPUT)
    # Catalogue every collected file except the manifest itself.
    files = [f for f in os.listdir(data_dir)
             if os.path.isfile(os.path.join(data_dir, f)) and f != REPORT_OUTPUT]
    manifest["active_test_assets_found"] = len(files)

    for file_name in files:
        file_path = os.path.join(data_dir, file_name)
        size_bytes = os.path.getsize(file_path)
        size_mb = size_bytes / (1024 * 1024)
        tier, complexity = isolate_tier(size_bytes)

        # Read the file footprint header signature.
        with open(file_path, "rb") as f:
            header = f.read(8)

        detected_format = "Custom / Non-Standard Legacy Format"
        for magic, name in MAGIC_BYTES.items():
            if header.startswith(magic):
                detected_format = name
                break

        # Format registry layout optimized for automation runners.
        record_entry = {
            "identifier": os.path.splitext(file_name)[0],
            "file_name": file_name,
            "known": file_name in KNOWN_SAMPLES,
            "target_format_classification": detected_format,
            "hex_header_signature": header.hex().upper(),
            "file_system_metrics": {
                "absolute_path": os.path.abspath(file_path),
                "byte_weight": size_bytes,
                "megabyte_weight": round(size_mb, 3),
                "workload_tier": tier
            },
            "testing_metadata": {
                "structural_complexity_profile": complexity,
                "suggested_parser_subroutine": "Format Isolation Test" if tier == "Small" else "Streaming Chunk Buffer Loop"
            }
        }
        manifest["test_suite_registry"].append(record_entry)

    with open(report_path, "w") as json_out:
        json.dump(manifest, json_out, indent=4)

    print(f"\n[+] Production JSON manifest compiled and saved to: {os.path.abspath(report_path)}")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--data-dir", default=None,
                        help="Directory to collect samples into (default: the project "
                             "data directory / PRINTSTREAMER_DATA_DIR).")
    args = parser.parse_args(argv)
    if args.data_dir:
        os.environ["PRINTSTREAMER_DATA_DIR"] = os.path.abspath(args.data_dir)

    data_dir = ensure_data_dir()
    print(f"[+] Collecting sample printstream files into: {data_dir}")
    download_and_generate_payloads(data_dir)
    build_json_manifest(data_dir)


if __name__ == "__main__":
    main()
