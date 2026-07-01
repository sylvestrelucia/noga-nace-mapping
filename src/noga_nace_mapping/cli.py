"""CLI entry point for build-noga-nace-mapping."""

from __future__ import annotations

import argparse
from pathlib import Path

from noga_nace_mapping.builder import build_links, write_mapping
from noga_nace_mapping.export import (
    ExportFormat,
    export_mapping,
    mirror_exports_to_repo_data,
)
from noga_nace_mapping.mapping import clear_mapping_cache


def _parse_formats(raw: str) -> set[ExportFormat]:
    if raw == "all":
        return {"all"}
    return {raw}  # type: ignore[return-value]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Regenerate the NOGA ↔ NACE mapping JSON and exports.",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Output path (default: bundled package data/noga_nace_mapping.json)",
    )
    parser.add_argument(
        "-f",
        "--format",
        choices=("json", "csv", "rdf", "all"),
        default="all",
        help="Output format(s); default exports JSON plus CSV and RDF",
    )
    args = parser.parse_args()
    formats = _parse_formats(args.format)

    links, method = build_links()
    output_path: Path | None = None
    if "json" in formats or "all" in formats:
        output_path = write_mapping(links, method=method, output_path=args.output)
        print(f"Wrote {output_path}")

    export_base = output_path or args.output
    exports: list[Path] = []
    if {"csv", "rdf", "all"} & formats:
        exports = export_mapping(links, formats=formats, json_path=export_base)

    mirrored = mirror_exports_to_repo_data(exports, export_base)
    for path in exports + mirrored:
        print(f"Wrote {path}")

    clear_mapping_cache()

    print(f"Built {len(links)} links, method={method}")
