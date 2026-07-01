"""CLI entry point for export-noga-nace-mapping."""

from __future__ import annotations

import argparse
from pathlib import Path

from noga_nace_mapping.export import export_from_mapping_file


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export the NOGA ↔ NACE mapping to CSV and/or annotated RDF (Turtle).",
    )
    parser.add_argument(
        "-i",
        "--input",
        type=Path,
        help="Mapping JSON path (default: bundled package data/noga_nace_mapping.json)",
    )
    parser.add_argument(
        "-f",
        "--format",
        choices=("csv", "rdf", "all"),
        default="all",
        help="Export format (default: all)",
    )
    args = parser.parse_args()

    exports = export_from_mapping_file(args.input, formats={args.format})
    for path in exports:
        print(f"Wrote {path}")
