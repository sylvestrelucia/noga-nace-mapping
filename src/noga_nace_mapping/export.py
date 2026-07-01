"""Export NOGA ↔ NACE mapping to CSV and annotated RDF (SKOS-aligned Turtle)."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Final, Literal

from noga_nace_mapping.locales import NACE_EXPORT_LOCALES, NOGA_EXPORT_LOCALES
from noga_nace_mapping.mapping import NogaNaceLink, _link_from_row, mapping_metadata, mapping_path
from noga_nace_mapping.nace_label_catalog import entry as nace_entry, labels as nace_labels
from noga_nace_mapping.noga_label_catalog import (
    division_labels,
    section_labels,
)
from noga_nace_mapping.noga_verticals import NOGA_SECTION_SLUGS, VERTICALS
from noga_nace_mapping.official_ids import (
    NOGA_SCHEME_URI,
    nace_code_from_slug,
    nace_uri_for_slug,
    noga_code_from_slug,
    noga_uri_for_slug,
)

ExportFormat = Literal["json", "csv", "rdf", "all"]

REPO_DATA_DIR = Path(__file__).resolve().parents[2] / "data"
PACKAGE_DATA_DIR = Path(__file__).resolve().parent / "data"

MAPPING_BASE_URI: Final = "https://github.com/sylvestrelucia/noga-nace-mapping/mapping#"

_CSV_BASE_COLUMNS: Final = (
    "noga_slug",
    "nace_slug",
    "noga_level",
    "nace_level",
    "noga_code",
    "nace_code",
    "noga_uri",
    "nace_uri",
    "section",
)

CSV_COLUMNS: Final = _CSV_BASE_COLUMNS + tuple(
    f"noga_label_{locale}" for locale in NOGA_EXPORT_LOCALES
) + tuple(f"nace_label_{locale}" for locale in NACE_EXPORT_LOCALES)


def noga_section_from_slug(slug: str) -> str:
    if slug in NOGA_SECTION_SLUGS:
        return VERTICALS[slug].noga_section
    code = noga_code_from_slug(slug)
    if not code:
        return ""
    for section_slug in NOGA_SECTION_SLUGS:
        if code in VERTICALS[section_slug].noga_divisions:
            return VERTICALS[section_slug].noga_section
    return ""


def nace_section_from_slug(slug: str) -> str:
    data = nace_entry(slug)
    if data is None:
        return ""
    return str(data["section"])


def section_for_link(link: NogaNaceLink) -> str:
    nace_section = nace_section_from_slug(link.nace_slug)
    if nace_section:
        return nace_section
    return noga_section_from_slug(link.noga_slug)


def noga_label_map(slug: str) -> dict[str, str]:
    if slug in NOGA_SECTION_SLUGS:
        return section_labels(slug)
    code = noga_code_from_slug(slug)
    if code:
        return division_labels(code)
    return {}


def mapping_uri(link: NogaNaceLink) -> str:
    return f"{MAPPING_BASE_URI}{link.noga_slug}__{link.nace_slug}"


def skos_mapping_relation(noga_level: str, nace_level: str) -> str:
    if noga_level == nace_level:
        return "skos:exactMatch"
    return "skos:relatedMatch"


def _localized(label_map: dict[str, str], locale: str) -> str:
    return label_map.get(locale) or label_map.get("en") or ""


def link_row(link: NogaNaceLink) -> dict[str, str | float]:
    noga_label_map_ = noga_label_map(link.noga_slug)
    nace_label_map_ = nace_labels(link.nace_slug)
    row: dict[str, str | float] = {
        "noga_slug": link.noga_slug,
        "nace_slug": link.nace_slug,
        "noga_level": link.noga_level,
        "nace_level": link.nace_level,
        "noga_code": link.noga_code or noga_code_from_slug(link.noga_slug),
        "nace_code": link.nace_code or nace_code_from_slug(link.nace_slug),
        "noga_uri": link.noga_uri or noga_uri_for_slug(link.noga_slug),
        "nace_uri": link.nace_uri or nace_uri_for_slug(link.nace_slug),
        "section": section_for_link(link),
    }
    for locale in NOGA_EXPORT_LOCALES:
        row[f"noga_label_{locale}"] = _localized(noga_label_map_, locale)
    for locale in NACE_EXPORT_LOCALES:
        row[f"nace_label_{locale}"] = _localized(nace_label_map_, locale)
    return row


def export_csv(
    links: list[NogaNaceLink],
    output_path: Path,
) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for link in links:
            writer.writerow(link_row(link))
    return output_path


def _turtle_literal(value: str, *, lang: str | None = None) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
    if lang:
        return f'"{escaped}"@{lang}'
    return f'"{escaped}"'


def export_rdf(
    links: list[NogaNaceLink],
    output_path: Path,
    *,
    metadata: dict | None = None,
) -> Path:
    meta = metadata if metadata is not None else mapping_metadata()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "@prefix skos: <http://www.w3.org/2004/02/skos/core#> .",
        "@prefix xsd: <http://www.w3.org/1999/XMLSchema#> .",
        "@prefix dct: <http://purl.org/dc/terms/> .",
        "@prefix nnm: <https://github.com/sylvestrelucia/noga-nace-mapping#> .",
        "",
        f"<{MAPPING_BASE_URI[:-1]}> a nnm:CrosswalkDataset ;",
        '    dct:title "NOGA 2008 ↔ NACE Rev. 2 structural crosswalk"@en ;',
        '    dct:description "Official structural alignment (BFS/OFS); levels 1–4 identical to NACE Rev. 2"@en ;',
        f'    nnm:method {_turtle_literal(str(meta.get("method", "")))} ;',
        f"    nnm:linkCount {len(links)} ;",
        f'    nnm:version {meta.get("version", 0)} .',
        "",
    ]

    noga_slugs = {link.noga_slug for link in links}
    nace_slugs = {link.nace_slug for link in links}

    lines.extend(
        [
            f"<{NOGA_SCHEME_URI}> a skos:ConceptScheme ;",
            '    dct:title "NOGA 2008"@en ;',
            '    dct:description "Swiss business activity nomenclature (I14Y nogaCode); levels 1–4 aligned with NACE Rev. 2"@en .',
            "",
            "<http://data.europa.eu/ux2/nace2/nace2> a skos:ConceptScheme ;",
            '    dct:title "NACE Rev. 2"@en ;',
            '    dct:description "EU statistical classification of economic activities"@en .',
            "",
        ]
    )

    for noga_slug in sorted(noga_slugs):
        noga_uri = noga_uri_for_slug(noga_slug)
        noga_label_map_ = noga_label_map(noga_slug)
        lines.append(f"<{noga_uri}> a skos:Concept ;")
        lines.append(f"    skos:notation {_turtle_literal(noga_code_from_slug(noga_slug))} ;")
        lines.append(f"    skos:inScheme <{NOGA_SCHEME_URI}> .")
        for locale in NOGA_EXPORT_LOCALES:
            label = _localized(noga_label_map_, locale)
            if label:
                lines.append(f"<{noga_uri}> skos:prefLabel {_turtle_literal(label, lang=locale)} .")
        lines.append("")

    for nace_slug in sorted(nace_slugs):
        nace_code = nace_code_from_slug(nace_slug)
        nace_uri = nace_uri_for_slug(nace_slug)
        nace_label_map_ = nace_labels(nace_slug)
        lines.append(f"<{nace_uri}> a skos:Concept ;")
        lines.append(f"    skos:notation {_turtle_literal(nace_code)} ;")
        lines.append("    skos:inScheme <http://data.europa.eu/ux2/nace2/nace2> .")
        for locale in NACE_EXPORT_LOCALES:
            label = _localized(nace_label_map_, locale)
            if label:
                lines.append(f"<{nace_uri}> skos:prefLabel {_turtle_literal(label, lang=locale)} .")
        lines.append("")

    for link in links:
        noga_uri = link.noga_uri or noga_uri_for_slug(link.noga_slug)
        nace_uri = link.nace_uri or nace_uri_for_slug(link.nace_slug)
        nace_code = link.nace_code or nace_code_from_slug(link.nace_slug)
        relation = skos_mapping_relation(link.noga_level, link.nace_level)

        lines.append(f"<{mapping_uri(link)}> a nnm:CrosswalkLink ;")
        lines.append(f"    nnm:nogaConcept <{noga_uri}> ;")
        lines.append(f"    nnm:naceConcept <{nace_uri}> ;")
        lines.append(f"    nnm:nogaSlug {_turtle_literal(link.noga_slug)} ;")
        lines.append(f"    nnm:naceSlug {_turtle_literal(link.nace_slug)} ;")
        lines.append(f"    nnm:nogaLevel {_turtle_literal(link.noga_level)} ;")
        lines.append(f"    nnm:naceLevel {_turtle_literal(link.nace_level)} ;")
        lines.append(
            f"    nnm:nogaCode {_turtle_literal(link.noga_code or noga_code_from_slug(link.noga_slug))} ;"
        )
        lines.append(f"    nnm:naceCode {_turtle_literal(nace_code)} ;")
        lines.append(f"    nnm:nogaUri <{noga_uri}> ;")
        lines.append(f"    nnm:naceUri <{nace_uri}> ;")
        lines.append(f"    nnm:section {_turtle_literal(section_for_link(link))} ;")
        lines.append(f"    nnm:mappingRelation {relation} .")
        lines.append("")

    with output_path.open("w", encoding="utf-8") as handle:
        handle.write("\n".join(lines))
        if not lines[-1].endswith("\n"):
            handle.write("\n")
    return output_path


def export_paths_for_json(json_path: Path) -> tuple[Path, Path]:
    stem = json_path.with_suffix("")
    return stem.with_suffix(".csv"), stem.with_suffix(".ttl")


def export_mapping(
    links: list[NogaNaceLink],
    *,
    formats: set[ExportFormat],
    json_path: Path | None = None,
    metadata: dict | None = None,
) -> list[Path]:
    written: list[Path] = []
    base_json = json_path or mapping_path()
    csv_path, rdf_path = export_paths_for_json(base_json)

    if "csv" in formats or "all" in formats:
        written.append(export_csv(links, csv_path))
    if "rdf" in formats or "all" in formats:
        written.append(export_rdf(links, rdf_path, metadata=metadata))

    return written


def export_from_mapping_file(
    mapping_json_path: Path | None = None,
    *,
    formats: set[ExportFormat],
) -> list[Path]:
    path = mapping_json_path or mapping_path()
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    links = [_link_from_row(row) for row in payload.get("links", [])]
    metadata = {
        key: payload[key]
        for key in ("version", "generated_at", "method", "link_count")
        if key in payload
    }
    return export_mapping(
        links,
        formats=formats,
        json_path=path,
        metadata=metadata,
    )


def mirror_exports_to_repo_data(exports: list[Path], json_path: Path | None) -> list[Path]:
    """Copy package-data artifacts to repo data/ when JSON was written there."""
    if json_path is None or json_path.parent.resolve() != PACKAGE_DATA_DIR.resolve():
        return []

    mirrored: list[Path] = []
    paths_to_mirror = list(exports)
    if json_path not in paths_to_mirror:
        paths_to_mirror.insert(0, json_path)

    REPO_DATA_DIR.mkdir(parents=True, exist_ok=True)
    for export_path in paths_to_mirror:
        destination = REPO_DATA_DIR / export_path.name
        destination.write_text(export_path.read_text(encoding="utf-8"), encoding="utf-8")
        mirrored.append(destination)
    return mirrored
