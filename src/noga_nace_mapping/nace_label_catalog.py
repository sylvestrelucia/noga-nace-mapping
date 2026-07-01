"""NACE Rev. 2 multilingual label and description catalog."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Final

from noga_nace_mapping.locales import NACE_LABEL_LOCALES

_CATALOG_PATH = Path(__file__).resolve().parent / "data" / "nace_labels.json"
SUPPORTED_LOCALES: Final = NACE_LABEL_LOCALES
NACE_LEVELS: Final = ("section", "division", "group", "class")


@lru_cache(maxsize=1)
def _load_raw_catalog() -> dict:
    if not _CATALOG_PATH.exists():
        return {"sections": [], "entries": {}}
    with _CATALOG_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)


def catalog_path() -> Path:
    return _CATALOG_PATH


def entry(slug: str) -> dict | None:
    return _load_raw_catalog().get("entries", {}).get(slug)


def section_slugs() -> list[str]:
    return list(_load_raw_catalog().get("sections", []))


def all_slugs(*, levels: tuple[str, ...] = NACE_LEVELS) -> list[str]:
    allowed = set(levels)
    return [
        slug
        for slug, data in _load_raw_catalog().get("entries", {}).items()
        if data.get("level") in allowed
    ]


def labels(slug: str) -> dict[str, str]:
    data = entry(slug)
    if data and data.get("labels"):
        return dict(data["labels"])
    return {}


def descriptions(slug: str) -> dict[str, str]:
    data = entry(slug)
    if data and data.get("descriptions"):
        return dict(data["descriptions"])
    label = labels(slug).get("en", "")
    return {"en": label} if label else {}


def label(slug: str, *, locale: str = "en") -> str:
    label_map = labels(slug)
    return label_map.get(locale) or label_map.get("en") or slug


def localized_text(label_map: dict[str, str], locale: str) -> str:
    return label_map.get(locale) or label_map.get("en") or next(iter(label_map.values()), "")


def division_slug_for_code(division: str) -> str:
    return f"nace-{division}"


def section_slug_for_letter(section: str) -> str:
    return f"nace-{section.lower()}"


def child_slugs(parent_slug: str) -> list[str]:
    entries = _load_raw_catalog().get("entries", {})
    return [
        slug
        for slug, data in entries.items()
        if data.get("parent_slug") == parent_slug
    ]


def build_embedding_descriptor(slug: str, *, locale: str = "en") -> str:
    data = entry(slug)
    if data is None:
        return slug

    level = data["level"]
    code = data["code"]
    section = data["section"]
    label_map = labels(slug)
    description_map = descriptions(slug)
    localized_label = localized_text(label_map, locale)
    localized_description = localized_text(description_map, locale)

    if level == "section":
        parts = [
            f"NACE section {code}: {localized_label}",
            localized_description,
        ]
    elif level == "division":
        parts = [
            f"NACE division {code} (section {section}): {localized_label}",
            localized_description,
        ]
        parent = data.get("parent_slug")
        if parent:
            parent_label = localized_text(labels(parent), locale)
            if parent_label:
                parts.append(f"Parent section: {parent_label}")
    elif level == "group":
        division = code.split(".", 1)[0]
        parts = [
            f"NACE group {code} (division {division}, section {section}): {localized_label}",
            localized_description,
        ]
    else:
        group_code = ".".join(code.split(".")[:2])
        division = code.split(".", 1)[0]
        parts = [
            f"NACE class {code} (group {group_code}, division {division}, section {section}): {localized_label}",
            localized_description,
        ]

    return "\n".join(part for part in parts if part.strip())
