"""NOGA 2008 / NACE Rev. 2 multilingual label and description catalog."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Final

from noga_nace_mapping.locales import NOGA_LABEL_LOCALES
from noga_nace_mapping.noga_verticals import (
    NOGA_SECTION_SLUGS,
    VERTICALS,
    child_vertical_slug,
)

_CATALOG_PATH = Path(__file__).resolve().parent / "data" / "noga_labels.json"
SUPPORTED_LOCALES: Final = NOGA_LABEL_LOCALES


@lru_cache(maxsize=1)
def _load_raw_catalog() -> dict:
    if not _CATALOG_PATH.exists():
        return {"sections": {}, "divisions": {}}
    with _CATALOG_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)


def catalog_path() -> Path:
    return _CATALOG_PATH


def section_labels(slug: str) -> dict[str, str]:
    entry = _load_raw_catalog().get("sections", {}).get(slug)
    if entry and entry.get("labels"):
        return dict(entry["labels"])
    vertical = VERTICALS.get(slug)
    if vertical is None:
        return {}
    return {"en": vertical.label_en}


def section_descriptions(slug: str) -> dict[str, str]:
    entry = _load_raw_catalog().get("sections", {}).get(slug)
    if entry and entry.get("descriptions"):
        return dict(entry["descriptions"])
    label = section_labels(slug).get("en", "")
    if not label:
        return {}
    return {"en": label}


def division_labels(division: str) -> dict[str, str]:
    entry = _load_raw_catalog().get("divisions", {}).get(division)
    if entry and entry.get("labels"):
        return dict(entry["labels"])
    return {"en": division}


def division_descriptions(division: str) -> dict[str, str]:
    entry = _load_raw_catalog().get("divisions", {}).get(division)
    if entry and entry.get("descriptions"):
        return dict(entry["descriptions"])
    label = division_labels(division).get("en", "")
    if not label:
        return {}
    return {"en": label}


def division_label(division: str, *, locale: str = "en") -> str:
    labels = division_labels(division)
    return labels.get(locale) or labels.get("en") or division


def section_label(slug: str, *, locale: str = "en") -> str:
    labels = section_labels(slug)
    return labels.get(locale) or labels.get("en") or slug


def localized_text(labels: dict[str, str], locale: str) -> str:
    return labels.get(locale) or labels.get("en") or next(iter(labels.values()), "")


def division_section_slug(division: str) -> str | None:
    entry = _load_raw_catalog().get("divisions", {}).get(division)
    if entry and entry.get("section_slug"):
        return str(entry["section_slug"])
    for slug in NOGA_SECTION_SLUGS:
        if division in VERTICALS[slug].noga_divisions:
            return slug
    return None


def all_vertical_slugs(*, include_sections: bool = True, include_divisions: bool = True) -> list[str]:
    slugs: list[str] = []
    if include_sections:
        slugs.extend(NOGA_SECTION_SLUGS)
    if include_divisions:
        for section_slug in NOGA_SECTION_SLUGS:
            for division in VERTICALS[section_slug].noga_divisions:
                slugs.append(child_vertical_slug(section_slug, division))
    return slugs


def vertical_level(slug: str) -> str | None:
    if slug in VERTICALS and slug in NOGA_SECTION_SLUGS:
        return "section"
    if slug.count("-") >= 2 and slug.rsplit("-", 1)[-1].isdigit():
        return "division"
    return None


def build_embedding_descriptor(slug: str) -> str:
    level = vertical_level(slug)
    if level == "section":
        labels = section_labels(slug)
        descriptions = section_descriptions(slug)
        section = VERTICALS[slug].noga_section
        parts = [
            f"NOGA section {section}: {labels.get('en', slug)}",
            descriptions.get("en", ""),
        ]
        return "\n".join(part for part in parts if part.strip())

    if level == "division":
        division = slug.rsplit("-", 1)[-1]
        section_slug = division_section_slug(division)
        section = VERTICALS[section_slug].noga_section if section_slug else ""
        labels = division_labels(division)
        descriptions = division_descriptions(division)
        parts = [
            f"NOGA division {division} (section {section}): {labels.get('en', division)}",
            descriptions.get("en", ""),
        ]
        if section_slug:
            section_en = section_labels(section_slug).get("en", "")
            if section_en:
                parts.append(f"Parent section: {section_en}")
        return "\n".join(part for part in parts if part.strip())

    return slug
