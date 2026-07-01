"""Build official NOGA ↔ NACE mapping (BFS structural alignment)."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from noga_nace_mapping.mapping import NogaNaceLink
from noga_nace_mapping.official_ids import official_ids_for_slugs
from noga_nace_mapping.nace_label_catalog import (
    all_slugs,
    child_slugs,
    division_slug_for_code,
    entry as nace_entry,
    section_slug_for_letter,
)
from noga_nace_mapping.noga_verticals import (
    NOGA_SECTION_SLUGS,
    VERTICALS,
    child_vertical_slug,
)

DEFAULT_OUTPUT_PATH = Path(__file__).resolve().parent / "data" / "noga_nace_mapping.json"
METHOD = "official-structural"
NACE_FINE_LEVELS = ("group", "class")


def _link(
    *,
    noga_slug: str,
    nace_slug: str,
    noga_level: str,
    nace_level: str,
) -> NogaNaceLink:
    noga_code, nace_code, noga_uri, nace_uri = official_ids_for_slugs(noga_slug, nace_slug)
    return NogaNaceLink(
        noga_slug=noga_slug,
        nace_slug=nace_slug,
        noga_level=noga_level,
        nace_level=nace_level,
        noga_code=noga_code,
        nace_code=nace_code,
        noga_uri=noga_uri,
        nace_uri=nace_uri,
    )


def structural_noga_division_for_nace(nace_slug: str) -> str | None:
    data = nace_entry(nace_slug)
    if data is None:
        return None
    level = str(data["level"])
    if level == "section":
        letter = str(data["section"])
        for section_slug in NOGA_SECTION_SLUGS:
            if VERTICALS[section_slug].noga_section == letter:
                return section_slug
        return None
    code = str(data["code"])
    division = code.split(".", 1)[0] if level in NACE_FINE_LEVELS else code
    section_letter = str(data["section"])
    for section_slug in NOGA_SECTION_SLUGS:
        if VERTICALS[section_slug].noga_section != section_letter:
            continue
        if division in VERTICALS[section_slug].noga_divisions:
            return child_vertical_slug(section_slug, division)
    return None


def build_links() -> tuple[list[NogaNaceLink], str]:
    """Build links from the official NOGA 2008 ↔ NACE Rev. 2 alignment.

    BFS documents that NOGA 2008 levels 1–4 match NACE Rev. 2. Section and
    division codes map 1:1; NACE groups and classes inherit their parent
    division's NOGA code.
    """
    links: list[NogaNaceLink] = []

    for section_slug in NOGA_SECTION_SLUGS:
        letter = VERTICALS[section_slug].noga_section
        nace_slug = section_slug_for_letter(letter)
        links.append(
            _link(
                noga_slug=section_slug,
                nace_slug=nace_slug,
                noga_level="section",
                nace_level="section",
            )
        )

    for section_slug in NOGA_SECTION_SLUGS:
        for division in VERTICALS[section_slug].noga_divisions:
            noga_slug = child_vertical_slug(section_slug, division)
            nace_slug = division_slug_for_code(division)
            links.append(
                _link(
                    noga_slug=noga_slug,
                    nace_slug=nace_slug,
                    noga_level="division",
                    nace_level="division",
                )
            )

    for nace_slug in all_slugs(levels=("group", "class")):
        data = nace_entry(nace_slug)
        if data is None:
            continue
        noga_slug = structural_noga_division_for_nace(nace_slug)
        if noga_slug is None:
            continue
        links.append(
            _link(
                noga_slug=noga_slug,
                nace_slug=nace_slug,
                noga_level="division",
                nace_level=str(data["level"]),
            )
        )

    return links, METHOD


def write_mapping(
    links: list[NogaNaceLink],
    *,
    method: str,
    output_path: Path | None = None,
) -> Path:
    destination = output_path or DEFAULT_OUTPUT_PATH
    payload = {
        "version": 3,
        "generated_at": datetime.now(UTC).isoformat(),
        "method": method,
        "source": (
            "Official NOGA 2008 ↔ NACE Rev. 2 structural alignment "
            "(BFS/OFS; levels 1–4 identical to NACE Rev. 2)"
        ),
        "source_url": "https://www.bfs.admin.ch/bfs/en/home/statistics/industry-services/nomenclatures/noga.html",
        "link_count": len(links),
        "links": [link.as_dict() for link in links],
    }
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    return destination
