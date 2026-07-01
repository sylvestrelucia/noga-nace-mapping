"""Locale constants for NACE (EU) and NOGA (Swiss) label catalogs and exports."""

from __future__ import annotations

from typing import Final

# All prefLabel languages in EU Vocabularies NACE Rev. 2 SPARQL (discovered 2026-07).
NACE_LABEL_LOCALES: Final = (
    "bg",
    "cs",
    "da",
    "de",
    "el",
    "en",
    "es",
    "et",
    "fi",
    "fr",
    "hr",
    "hu",
    "it",
    "lt",
    "lv",
    "mt",
    "nl",
    "no",
    "pl",
    "pt",
    "ro",
    "ru",
    "sk",
    "sl",
    "sv",
    "tr",
)

# coreContentNote languages available in the same SPARQL endpoint (subset of prefLabel langs).
NACE_DESCRIPTION_LOCALES: Final = (
    "bg",
    "cs",
    "de",
    "en",
    "es",
    "fr",
    "hr",
    "hu",
    "lt",
    "pl",
    "ru",
    "tr",
)

# Swiss official languages for NOGA/BFS statistical publications (levels 1–4 = NACE Rev. 2).
# Romansh (rm) is not published in EU Vocabularies NACE Rev. 2 SPARQL.
NOGA_LABEL_LOCALES: Final = ("de", "fr", "it", "en")

# Export column order: English first, then remaining locales alphabetically.
NACE_EXPORT_LOCALES: Final = ("en",) + tuple(
    locale for locale in NACE_LABEL_LOCALES if locale != "en"
)
NOGA_EXPORT_LOCALES: Final = ("en",) + tuple(
    locale for locale in NOGA_LABEL_LOCALES if locale != "en"
)
