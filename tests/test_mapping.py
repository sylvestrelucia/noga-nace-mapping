from noga_nace_mapping import (
    allocate_noga_jobs_to_nace,
    all_links,
    links_for_nace,
    mapping_path,
    top_noga_matches_for_nace,
)
from noga_nace_mapping.builder import structural_noga_division_for_nace
from noga_nace_mapping.noga_verticals import child_vertical_slug


def test_mapping_file_exists_with_level_aligned_links():
    assert mapping_path().exists()
    links = all_links()
    assert len(links) == 996
    level_aligned = [link for link in links if link.noga_level == link.nace_level]
    assert len(level_aligned) == 109


def test_hierarchical_links_map_nace_fine_levels_to_parent_noga_division():
    class_links = links_for_nace("nace-62-01")
    assert class_links == [
        next(
            link
            for link in all_links()
            if link.noga_slug == "noga-j-62" and link.nace_slug == "nace-62-01"
        )
    ]
    assert class_links[0].noga_level == "division"
    assert class_links[0].nace_level == "class"


def test_top_noga_matches_for_nace_section_and_division():
    section_matches = top_noga_matches_for_nace("nace-j")
    assert section_matches == [
        next(
            link
            for link in all_links()
            if link.noga_slug == "noga-j" and link.nace_slug == "nace-j"
        )
    ]

    division_matches = top_noga_matches_for_nace("nace-61")
    assert division_matches == [
        next(
            link
            for link in all_links()
            if link.noga_slug == "noga-j-61" and link.nace_slug == "nace-61"
        )
    ]


def test_hierarchical_links_normalize_to_noga_targets():
    class_links = links_for_nace("nace-62-01")
    assert class_links
    assert all(link.nace_level in ("group", "class") for link in class_links)
    assert structural_noga_division_for_nace("nace-62-01") == "noga-j-62"
    noga_slugs = {link.noga_slug for link in class_links}
    assert noga_slugs == {"noga-j-62"}


def test_allocate_noga_jobs_to_nace_distributes_by_weight():
    allocated = allocate_noga_jobs_to_nace({child_vertical_slug("noga-j", "62"): 100})
    class_slugs = [slug for slug in allocated if slug.startswith("nace-62-")]
    assert class_slugs
    assert abs(sum(allocated[slug] for slug in class_slugs) - 100.0) < 0.01


def test_links_include_official_ids():
    link = next(
        link
        for link in all_links()
        if link.noga_slug == "noga-j-62" and link.nace_slug == "nace-62-01"
    )
    assert link.noga_code == "62"
    assert link.nace_code == "62.01"
    assert link.noga_uri == "https://register.ld.admin.ch/i14y/concept/nogaCode/62"
    assert link.nace_uri == "http://data.europa.eu/ux2/nace2/6201"
    assert link.noga_uri != link.nace_uri


def test_section_link_official_ids():
    link = next(
        link for link in all_links()
        if link.noga_slug == "noga-j" and link.nace_slug == "nace-j"
    )
    assert link.noga_code == "J"
    assert link.nace_code == "J"
    assert link.noga_uri == "https://register.ld.admin.ch/i14y/concept/nogaCode/J"
    assert link.nace_uri == "http://data.europa.eu/ux2/nace2/J"
    assert link.noga_uri != link.nace_uri


def test_division_class_link_noga_and_nace_uris_differ():
    link = next(
        link
        for link in all_links()
        if link.noga_slug == "noga-a-01" and link.nace_slug == "nace-01-25"
    )
    assert link.noga_code == "01"
    assert link.nace_code == "01.25"
    assert link.noga_uri == "https://register.ld.admin.ch/i14y/concept/nogaCode/01"
    assert link.nace_uri == "http://data.europa.eu/ux2/nace2/0125"
    assert link.noga_uri != link.nace_uri
