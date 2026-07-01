"""NOGA 2008 section-based vertical taxonomy."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

CATCH_ALL_SLUG: Final = "all"


@dataclass(frozen=True, slots=True)
class NogaVertical:
    slug: str
    label_en: str
    noga_section: str
    noga_divisions: tuple[str, ...] = ()


VERTICALS: Final[dict[str, NogaVertical]] = {
    CATCH_ALL_SLUG: NogaVertical(
        slug=CATCH_ALL_SLUG,
        label_en="All sectors",
        noga_section="",
    ),
    "noga-a": NogaVertical(
        slug="noga-a",
        label_en="Agriculture, forestry and fishing",
        noga_section="A",
        noga_divisions=("01", "02", "03"),
    ),
    "noga-b": NogaVertical(
        slug="noga-b",
        label_en="Mining and quarrying",
        noga_section="B",
        noga_divisions=("05", "06", "07", "08", "09"),
    ),
    "noga-c": NogaVertical(
        slug="noga-c",
        label_en="Manufacturing",
        noga_section="C",
        noga_divisions=tuple(f"{code:02d}" for code in range(10, 34)),
    ),
    "noga-d": NogaVertical(
        slug="noga-d",
        label_en="Electricity, gas, steam and air conditioning supply",
        noga_section="D",
        noga_divisions=("35",),
    ),
    "noga-e": NogaVertical(
        slug="noga-e",
        label_en="Water supply; sewerage, waste management and remediation",
        noga_section="E",
        noga_divisions=("36", "37", "38", "39"),
    ),
    "noga-f": NogaVertical(
        slug="noga-f",
        label_en="Construction",
        noga_section="F",
        noga_divisions=("41", "42", "43"),
    ),
    "noga-g": NogaVertical(
        slug="noga-g",
        label_en="Wholesale and retail trade",
        noga_section="G",
        noga_divisions=("45", "46", "47"),
    ),
    "noga-h": NogaVertical(
        slug="noga-h",
        label_en="Transportation and storage",
        noga_section="H",
        noga_divisions=("49", "50", "51", "52", "53"),
    ),
    "noga-i": NogaVertical(
        slug="noga-i",
        label_en="Accommodation and food service activities",
        noga_section="I",
        noga_divisions=("55", "56"),
    ),
    "noga-j": NogaVertical(
        slug="noga-j",
        label_en="Information and communication",
        noga_section="J",
        noga_divisions=("58", "59", "60", "61", "62", "63"),
    ),
    "noga-k": NogaVertical(
        slug="noga-k",
        label_en="Financial and insurance activities",
        noga_section="K",
        noga_divisions=("64", "65", "66"),
    ),
    "noga-l": NogaVertical(
        slug="noga-l",
        label_en="Real estate activities",
        noga_section="L",
        noga_divisions=("68",),
    ),
    "noga-m": NogaVertical(
        slug="noga-m",
        label_en="Professional, scientific and technical activities",
        noga_section="M",
        noga_divisions=("69", "70", "71", "72", "73", "74", "75"),
    ),
    "noga-n": NogaVertical(
        slug="noga-n",
        label_en="Administrative and support service activities",
        noga_section="N",
        noga_divisions=("77", "78", "79", "80", "81", "82"),
    ),
    "noga-o": NogaVertical(
        slug="noga-o",
        label_en="Public administration and defence",
        noga_section="O",
        noga_divisions=("84",),
    ),
    "noga-p": NogaVertical(
        slug="noga-p",
        label_en="Education",
        noga_section="P",
        noga_divisions=("85",),
    ),
    "noga-q": NogaVertical(
        slug="noga-q",
        label_en="Human health and social work activities",
        noga_section="Q",
        noga_divisions=("86", "87", "88"),
    ),
    "noga-r": NogaVertical(
        slug="noga-r",
        label_en="Arts, entertainment and recreation",
        noga_section="R",
        noga_divisions=("90", "91", "92", "93"),
    ),
    "noga-s": NogaVertical(
        slug="noga-s",
        label_en="Other service activities",
        noga_section="S",
        noga_divisions=("94", "95", "96"),
    ),
    "noga-t": NogaVertical(
        slug="noga-t",
        label_en="Activities of households as employers",
        noga_section="T",
        noga_divisions=("97", "98"),
    ),
    "noga-u": NogaVertical(
        slug="noga-u",
        label_en="Activities of extraterritorial organisations and bodies",
        noga_section="U",
        noga_divisions=("99",),
    ),
}

NOGA_SECTION_SLUGS: Final[tuple[str, ...]] = tuple(
    slug for slug in VERTICALS if slug != CATCH_ALL_SLUG
)


def child_vertical_slug(section_slug: str, division: str) -> str:
    return f"{section_slug}-{division}"
