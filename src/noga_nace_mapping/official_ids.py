"""Official notation strings and EU Vocabularies URIs for NOGA / NACE concepts."""

from __future__ import annotations

from typing import Final

from noga_nace_mapping.nace_label_catalog import entry as nace_entry
from noga_nace_mapping.noga_verticals import NOGA_SECTION_SLUGS, VERTICALS

NACE2_BASE_URI: Final = "http://data.europa.eu/ux2/nace2/"
# Swiss I14Y interoperability register (LINDAS); NOGA 2008 code list concept.
# https://register.ld.admin.ch/i14y/concept/nogaCode
NOGA_SCHEME_URI: Final = "https://register.ld.admin.ch/i14y/concept/nogaCode"
NOGA_BASE_URI: Final = f"{NOGA_SCHEME_URI}/"


def noga_code_from_slug(slug: str) -> str:
    if slug in NOGA_SECTION_SLUGS:
        return VERTICALS[slug].noga_section
    if slug.count("-") >= 2 and slug.rsplit("-", 1)[-1].isdigit():
        return slug.rsplit("-", 1)[-1]
    return ""


def nace_code_from_slug(slug: str) -> str:
    data = nace_entry(slug)
    if data is None:
        return ""
    return str(data["code"])


def nace_uri_for_code(code: str) -> str:
    """Derive the EU Vocabularies NACE Rev. 2 concept URI from an official notation."""
    if len(code) == 1 and code.isalpha():
        return f"{NACE2_BASE_URI}{code.upper()}"
    return f"{NACE2_BASE_URI}{code.replace('.', '')}"


def nace_uri_for_slug(slug: str) -> str:
    data = nace_entry(slug)
    if data is not None and data.get("uri"):
        return str(data["uri"])
    code = nace_code_from_slug(slug)
    if code:
        return nace_uri_for_code(code)
    return ""


def noga_uri_for_code(code: str) -> str:
    """Derive the Swiss I14Y/LINDAS NOGA concept URI from an official notation."""
    if len(code) == 1 and code.isalpha():
        return f"{NOGA_SCHEME_URI}/{code.upper()}"
    return f"{NOGA_SCHEME_URI}/{code.replace('.', '')}"


def noga_uri_for_slug(slug: str) -> str:
    """Official NOGA concept URI from the I14Y register (distinct from EU NACE2 URIs)."""
    code = noga_code_from_slug(slug)
    if code:
        return noga_uri_for_code(code)
    return ""


def official_ids_for_slugs(noga_slug: str, nace_slug: str) -> tuple[str, str, str, str]:
    noga_code = noga_code_from_slug(noga_slug)
    nace_code = nace_code_from_slug(nace_slug)
    return (
        noga_code,
        nace_code,
        noga_uri_for_slug(noga_slug),
        nace_uri_for_slug(nace_slug),
    )
