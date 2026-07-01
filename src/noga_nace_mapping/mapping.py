"""Weighted NOGA ↔ NACE Rev. 2 correspondence mappings."""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Final

from noga_nace_mapping.nace_label_catalog import (
    child_slugs,
    division_slug_for_code,
    entry as nace_entry,
    section_slug_for_letter,
)
from noga_nace_mapping.official_ids import official_ids_for_slugs
from noga_nace_mapping.noga_verticals import (
    NOGA_SECTION_SLUGS,
    VERTICALS,
)

_MAPPING_PATH = Path(__file__).resolve().parent / "data" / "noga_nace_mapping.json"

NOGA_LEVELS: Final = ("section", "division")
NACE_FINE_LEVELS: Final = ("group", "class")


@dataclass(frozen=True, slots=True)
class NogaNaceLink:
    noga_slug: str
    nace_slug: str
    noga_level: str
    nace_level: str
    noga_code: str = ""
    nace_code: str = ""
    noga_uri: str = ""
    nace_uri: str = ""

    def as_dict(self) -> dict:
        return {
            "noga_slug": self.noga_slug,
            "nace_slug": self.nace_slug,
            "noga_level": self.noga_level,
            "nace_level": self.nace_level,
            "noga_code": self.noga_code,
            "nace_code": self.nace_code,
            "noga_uri": self.noga_uri,
            "nace_uri": self.nace_uri,
        }


def _link_from_row(row: dict) -> NogaNaceLink:
    noga_slug = str(row["noga_slug"])
    nace_slug = str(row["nace_slug"])
    noga_code = str(row.get("noga_code") or "")
    nace_code = str(row.get("nace_code") or "")
    noga_uri = str(row.get("noga_uri") or "")
    nace_uri = str(row.get("nace_uri") or "")
    if not noga_code or not nace_code or not noga_uri or not nace_uri:
        derived = official_ids_for_slugs(noga_slug, nace_slug)
        noga_code = noga_code or derived[0]
        nace_code = nace_code or derived[1]
        noga_uri = noga_uri or derived[2]
        nace_uri = nace_uri or derived[3]
    return NogaNaceLink(
        noga_slug=noga_slug,
        nace_slug=nace_slug,
        noga_level=str(row["noga_level"]),
        nace_level=str(row["nace_level"]),
        noga_code=noga_code,
        nace_code=nace_code,
        noga_uri=noga_uri,
        nace_uri=nace_uri,
    )


@lru_cache(maxsize=1)
def _load_raw_mapping() -> dict:
    if not _MAPPING_PATH.exists():
        return {"version": 0, "links": []}
    with _MAPPING_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)


def mapping_path() -> Path:
    return _MAPPING_PATH


def mapping_metadata() -> dict:
    raw = _load_raw_mapping()
    return {
        key: raw[key]
        for key in ("version", "generated_at", "method", "link_count")
        if key in raw
    }


def clear_mapping_cache() -> None:
    _load_raw_mapping.cache_clear()
    _links_by_noga.cache_clear()
    _links_by_nace.cache_clear()


def all_links() -> list[NogaNaceLink]:
    return [_link_from_row(row) for row in _load_raw_mapping().get("links", [])]


@lru_cache(maxsize=1)
def _links_by_noga() -> dict[str, list[NogaNaceLink]]:
    grouped: dict[str, list[NogaNaceLink]] = {}
    for link in all_links():
        grouped.setdefault(link.noga_slug, []).append(link)
    return grouped


@lru_cache(maxsize=1)
def _links_by_nace() -> dict[str, list[NogaNaceLink]]:
    grouped: dict[str, list[NogaNaceLink]] = {}
    for link in all_links():
        grouped.setdefault(link.nace_slug, []).append(link)
    return grouped


def links_for_noga(noga_slug: str) -> list[NogaNaceLink]:
    return list(_links_by_noga().get(noga_slug, []))


def links_for_nace(nace_slug: str) -> list[NogaNaceLink]:
    return list(_links_by_nace().get(nace_slug, []))


def structural_nace_division_for_noga(noga_slug: str) -> str | None:
    if noga_slug in NOGA_SECTION_SLUGS:
        return section_slug_for_letter(VERTICALS[noga_slug].noga_section)
    if noga_slug.count("-") >= 2 and noga_slug.rsplit("-", 1)[-1].isdigit():
        division = noga_slug.rsplit("-", 1)[-1]
        return division_slug_for_code(division)
    return None


def nace_group_class_slugs_under_division(nace_division_slug: str) -> list[str]:
    slugs: list[str] = []
    for group_slug in child_slugs(nace_division_slug):
        slugs.append(group_slug)
        slugs.extend(child_slugs(group_slug))
    return slugs


def allocate_noga_jobs_to_nace(
    noga_job_counts: dict[str, int],
) -> dict[str, float]:
    """Distribute NOGA division/section job counts to NACE slugs using mapping weights."""
    allocated: dict[str, float] = {}

    for noga_slug, count in noga_job_counts.items():
        if count <= 0:
            continue

        noga_level = "section" if noga_slug in NOGA_SECTION_SLUGS else "division"
        if noga_level == "section":
            nace_slug = structural_nace_division_for_noga(noga_slug)
            if nace_slug:
                allocated[nace_slug] = allocated.get(nace_slug, 0.0) + float(count)
            continue

        nace_division_slug = structural_nace_division_for_noga(noga_slug)
        if nace_division_slug is None:
            continue

        fine_targets = nace_group_class_slugs_under_division(nace_division_slug)
        if not fine_targets:
            allocated[nace_division_slug] = allocated.get(nace_division_slug, 0.0) + float(count)
            continue

        raw_weights: dict[str, float] = {}
        for nace_slug in fine_targets:
            for link in links_for_nace(nace_slug):
                if link.noga_slug == noga_slug:
                    raw_weights[nace_slug] = 1.0
                    break

        if not raw_weights:
            allocated[nace_division_slug] = allocated.get(nace_division_slug, 0.0) + float(count)
            continue

        total_weight = sum(raw_weights.values())
        if total_weight <= 0:
            allocated[nace_division_slug] = allocated.get(nace_division_slug, 0.0) + float(count)
            continue

        for nace_slug, weight in raw_weights.items():
            share = float(count) * (weight / total_weight)
            allocated[nace_slug] = allocated.get(nace_slug, 0.0) + share

    return allocated


def top_noga_matches_for_nace(nace_slug: str, *, limit: int = 3) -> list[NogaNaceLink]:
    links = sorted(links_for_nace(nace_slug), key=lambda link: link.noga_slug)
    return links[:limit]


def top_nace_matches_for_noga(noga_slug: str, *, limit: int = 3) -> list[NogaNaceLink]:
    links = sorted(links_for_noga(noga_slug), key=lambda link: link.nace_slug)
    return links[:limit]
