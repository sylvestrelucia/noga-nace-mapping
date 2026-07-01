#!/usr/bin/env python3
"""Download official NACE Rev. 2 labels from EU Vocabularies and rebuild catalog JSON."""

from __future__ import annotations

import argparse
import json
import re
import urllib.parse
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

from noga_nace_mapping.locales import (
    NACE_DESCRIPTION_LOCALES,
    NACE_LABEL_LOCALES,
    NOGA_LABEL_LOCALES,
)
from noga_nace_mapping.noga_verticals import NOGA_SECTION_SLUGS, VERTICALS

ROOT = Path(__file__).resolve().parents[2]
PACKAGE_DATA = Path(__file__).resolve().parent / "data"
SOURCES_DIR = ROOT / "data" / "sources"

SPARQL_ENDPOINT = "https://publications.europa.eu/webapi/rdf/sparql"
SPARQL_LABELS_QUERY = """\
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
SELECT ?uri ?notation ?broaderUri ?label ?lang WHERE {
  ?uri skos:inScheme <http://data.europa.eu/ux2/nace2/nace2> .
  ?uri skos:notation ?notation .
  ?uri skos:prefLabel ?label .
  BIND(LANG(?label) AS ?lang)
  OPTIONAL { ?uri skos:broader ?broaderUri . }
  FILTER(?lang != "")
  FILTER(!REGEX(STR(?uri), "/nace2/A[0-9]+_"))
  FILTER(!REGEX(STR(?uri), "/nace2/MIG_"))
}
"""

SPARQL_NOTES_QUERY = """\
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX xkos: <http://rdf-vocabulary.ddialliance.org/xkos#>
SELECT ?uri ?coreNote ?noteLang WHERE {
  ?uri skos:inScheme <http://data.europa.eu/ux2/nace2/nace2> .
  ?uri xkos:coreContentNote ?coreNote .
  BIND(LANG(?coreNote) AS ?noteLang)
  FILTER(?noteLang != "")
  FILTER(!REGEX(STR(?uri), "/nace2/A[0-9]+_"))
  FILTER(!REGEX(STR(?uri), "/nace2/MIG_"))
}
"""

AGGREGATE_URI_RE = re.compile(r"/nace2/(?:A[0-9]+_|MIG_)")


def _clean_label(notation: str, label: str) -> str:
    text = label.strip()
    if len(notation) == 1 and notation.isalpha():
        prefix = f"{notation.upper()} "
        if text.upper().startswith(prefix):
            text = text[len(prefix) :]
    elif notation.replace(".", "").isdigit():
        if text.startswith(notation):
            text = text[len(notation) :].lstrip(" -–—")
    return text.strip()


def _nace_level(notation: str) -> str | None:
    if re.fullmatch(r"[A-U]", notation):
        return "section"
    if re.fullmatch(r"\d{2}", notation):
        return "division"
    if re.fullmatch(r"\d{2}\.\d", notation):
        return "group"
    if re.fullmatch(r"\d{2}\.\d{2}", notation):
        return "class"
    return None


def _slug_for_notation(notation: str) -> str:
    if len(notation) == 1:
        return f"nace-{notation.lower()}"
    return "nace-" + notation.replace(".", "-")


def _section_for_notation(notation: str, concepts: dict[str, dict]) -> str:
    if len(notation) == 1:
        return notation.upper()
    if re.fullmatch(r"\d{2}", notation):
        return _division_section(notation, concepts)
    if "." in notation:
        return _division_section(notation.split(".", 1)[0], concepts)
    return ""


def _division_section(division: str, concepts: dict[str, dict]) -> str:
    for concept in concepts.values():
        if concept["level"] == "division" and concept["notation"] == division:
            return concept.get("section", "")
    return ""


def _fetch_sparql_rows(query: str) -> list[dict[str, str]]:
    encoded = urllib.parse.urlencode({"format": "json", "query": query})
    request = urllib.request.Request(
        f"{SPARQL_ENDPOINT}?{encoded}",
        headers={"User-Agent": "noga-nace-mapping/1.0"},
    )
    with urllib.request.urlopen(request, timeout=300) as response:
        payload = json.load(response)

    rows: list[dict[str, str]] = []
    for binding in payload.get("results", {}).get("bindings", []):
        rows.append({key: binding[key]["value"] for key in binding})
    return rows


def _fetch_official_rows() -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    label_rows = _fetch_sparql_rows(SPARQL_LABELS_QUERY)
    note_rows = _fetch_sparql_rows(SPARQL_NOTES_QUERY)
    return label_rows, note_rows


def _build_concepts(
    label_rows: list[dict[str, str]],
    note_rows: list[dict[str, str]],
) -> dict[str, dict]:
    concepts: dict[str, dict] = {}
    for row in label_rows:
        uri = row["uri"]
        if AGGREGATE_URI_RE.search(uri):
            continue
        notation = row["notation"]
        level = _nace_level(notation)
        if level is None:
            continue

        concept = concepts.setdefault(
            uri,
            {
                "uri": uri,
                "notation": notation,
                "level": level,
                "labels": {},
                "descriptions": {},
                "broader_uri": None,
            },
        )
        lang = row.get("lang")
        if lang in NACE_LABEL_LOCALES:
            concept["labels"][lang] = _clean_label(notation, row["label"])
        if row.get("broaderUri"):
            concept["broader_uri"] = row["broaderUri"]

    for row in note_rows:
        uri = row["uri"]
        if uri not in concepts:
            continue
        note_lang = row.get("noteLang")
        if note_lang in NACE_DESCRIPTION_LOCALES and row.get("coreNote"):
            concepts[uri]["descriptions"][note_lang] = row["coreNote"].strip()

    uri_to_notation = {data["uri"]: data["notation"] for data in concepts.values()}
    level_order = {"section": 0, "division": 1, "group": 2, "class": 3}
    for concept in sorted(
        concepts.values(),
        key=lambda item: (level_order[item["level"]], item["notation"]),
    ):
        broader_uri = concept.pop("broader_uri", None)
        parent_notation = uri_to_notation.get(broader_uri or "")
        concept["parent_notation"] = parent_notation
        if concept["level"] == "division" and parent_notation:
            concept["section"] = parent_notation.upper()
        elif concept["level"] in {"group", "class"}:
            concept["section"] = _section_for_notation(concept["notation"], concepts)
        elif concept["level"] == "section":
            concept["section"] = concept["notation"].upper()
        else:
            concept["section"] = ""

    return concepts


def build_nace_catalog(concepts: dict[str, dict]) -> dict:
    entries: dict[str, dict] = {}
    sections: list[str] = []

    ordered = sorted(
        concepts.values(),
        key=lambda item: (item["level"], item["notation"]),
    )
    for concept in ordered:
        slug = _slug_for_notation(concept["notation"])
        parent_slug = None
        parent_notation = concept.get("parent_notation")
        if parent_notation:
            parent_slug = _slug_for_notation(parent_notation)

        entry = {
            "level": concept["level"],
            "code": concept["notation"],
            "uri": concept["uri"],
            "section": concept.get("section", ""),
            "parent_slug": parent_slug,
            "labels": concept["labels"],
        }
        if concept["descriptions"]:
            entry["descriptions"] = concept["descriptions"]
        entries[slug] = entry
        if concept["level"] == "section":
            sections.append(slug)

    return {
        "source": "Eurostat NACE Rev. 2 (EU Vocabularies / Publications Office SPARQL)",
        "source_url": "https://op.europa.eu/en/web/eu-vocabularies/dataset/-/resource?uri=http://publications.europa.eu/resource/dataset/nace2",
        "fetched_at": datetime.now(UTC).isoformat(),
        "sections": sections,
        "entries": entries,
    }


def build_noga_catalog(nace_catalog: dict) -> dict:
    nace_entries = nace_catalog["entries"]
    sections: dict[str, dict] = {}
    divisions: dict[str, dict] = {}

    for section_slug in NOGA_SECTION_SLUGS:
        nace_section_slug = section_slug.replace("noga", "nace")
        nace_section = nace_entries.get(nace_section_slug)
        if nace_section is None:
            continue
        section_entry = {
            "noga_section": VERTICALS[section_slug].noga_section,
            "labels": {
                locale: nace_section["labels"][locale]
                for locale in NOGA_LABEL_LOCALES
                if locale in nace_section["labels"]
            },
        }
        if nace_section.get("descriptions"):
            section_entry["descriptions"] = {
                locale: nace_section["descriptions"][locale]
                for locale in NOGA_LABEL_LOCALES
                if locale in nace_section["descriptions"]
            }
        sections[section_slug] = section_entry

        for division in VERTICALS[section_slug].noga_divisions:
            nace_division = nace_entries.get(f"nace-{division}")
            if nace_division is None:
                continue
            division_entry = {
                "section_slug": section_slug,
                "labels": {
                    locale: nace_division["labels"][locale]
                    for locale in NOGA_LABEL_LOCALES
                    if locale in nace_division["labels"]
                },
            }
            if nace_division.get("descriptions"):
                division_entry["descriptions"] = {
                    locale: nace_division["descriptions"][locale]
                    for locale in NOGA_LABEL_LOCALES
                    if locale in nace_division["descriptions"]
                }
            divisions[division] = division_entry

    return {
        "source": (
            "NOGA 2008 sections/divisions aligned with NACE Rev. 2 levels 1–4 "
            "(Swiss Federal Statistical Office; labels from Eurostat EU Vocabularies)"
        ),
        "source_url": "https://www.bfs.admin.ch/bfs/en/home/statistics/industry-services/nomenclatures/noga.html",
        "fetched_at": datetime.now(UTC).isoformat(),
        "sections": sections,
        "divisions": divisions,
    }


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--sources-only",
        action="store_true",
        help="Only write the raw SPARQL snapshot under data/sources/",
    )
    args = parser.parse_args()

    label_rows, note_rows = _fetch_official_rows()
    SOURCES_DIR.mkdir(parents=True, exist_ok=True)
    snapshot_path = SOURCES_DIR / "nace_r2_eurostat_sparql.json"
    write_json(
        snapshot_path,
        {
            "fetched_at": datetime.now(UTC).isoformat(),
            "endpoint": SPARQL_ENDPOINT,
            "label_row_count": len(label_rows),
            "note_row_count": len(note_rows),
            "label_rows": label_rows,
            "note_rows": note_rows,
        },
    )

    concepts = _build_concepts(label_rows, note_rows)
    manifest_path = SOURCES_DIR / "manifest.json"
    existing_manifest: dict = {}
    if manifest_path.is_file():
        with manifest_path.open(encoding="utf-8") as handle:
            existing_manifest = json.load(handle)

    manifest = {
        "nace_rev2": {
            "provider": "Eurostat / Publications Office of the EU",
            "endpoint": SPARQL_ENDPOINT,
            "dataset": "http://publications.europa.eu/resource/dataset/nace2",
            "snapshot": str(snapshot_path.relative_to(ROOT)),
            "concept_count": len(concepts),
            "fetched_at": datetime.now(UTC).isoformat(),
            "license": {
                "name": "EU Commission reuse policy / CC BY 4.0 (editorial content)",
                "url": "https://ec.europa.eu/eurostat/en/help/copyright-notice",
                "attribution": "Source: Eurostat / EU Vocabularies (NACE Rev. 2)",
                "commercial_use": (
                    "permitted with source acknowledgement; indicate modifications"
                ),
                "modifications": (
                    "Labels and notes reformatted to JSON; "
                    "NOGA catalog is a subset at levels 1–4"
                ),
            },
        },
        "noga_2008": {
            "provider": "Swiss Federal Statistical Office (BFS/OFS)",
            "note": (
                "NOGA 2008 levels 1–4 are identical to NACE Rev. 2; "
                "labels in this repo are sourced from Eurostat EU Vocabularies, "
                "not copied from BFS publications."
            ),
            "url": (
                "https://www.bfs.admin.ch/bfs/en/home/statistics/"
                "industry-services/nomenclatures/noga.html"
            ),
            "license": {
                "name": (
                    "BFS reproduction terms (structural alignment); "
                    "Eurostat terms (bundled labels)"
                ),
                "url": "https://www.bfs.admin.ch/bfsstatic/dam/assets/344621/master",
                "attribution": "Swiss Federal Statistical Office (BFS/OFS), NOGA 2008",
                "commercial_use": (
                    "BFS publications: reproduction with source mention authorized "
                    "except commercial purposes; contact BFS for commercial "
                    "republication of BFS text"
                ),
            },
        },
    }
    for key in ("noga2002_noga2008_conversion_keys", "repository_mapping"):
        if key in existing_manifest:
            manifest[key] = existing_manifest[key]
    write_json(manifest_path, manifest)

    if args.sources_only:
        print(
            f"Wrote {snapshot_path} "
            f"({len(label_rows)} label rows, {len(note_rows)} note rows, {len(concepts)} concepts)"
        )
        return

    nace_catalog = build_nace_catalog(concepts)
    noga_catalog = build_noga_catalog(nace_catalog)
    write_json(PACKAGE_DATA / "nace_labels.json", nace_catalog)
    write_json(PACKAGE_DATA / "noga_labels.json", noga_catalog)
    print(
        f"Wrote official labels: {len(nace_catalog['entries'])} NACE entries, "
        f"{len(noga_catalog['sections'])} NOGA sections, "
        f"{len(noga_catalog['divisions'])} NOGA divisions"
    )


if __name__ == "__main__":
    main()
