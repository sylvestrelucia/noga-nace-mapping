"""NOGA 2008 ↔ NACE Rev. 2 crosswalk — Swiss–EU industry classification mapping.

Official structural correspondence between Swiss NOGA (BFS) and EU NACE Rev. 2
(Eurostat): machine-readable JSON/CSV/RDF exports and helpers for code conversion
and statistical harmonization.
"""

from noga_nace_mapping.mapping import (
    NogaNaceLink,
    allocate_noga_jobs_to_nace,
    all_links,
    links_for_nace,
    links_for_noga,
    mapping_path,
    top_noga_matches_for_nace,
    top_nace_matches_for_noga,
)

__all__ = [
    "NogaNaceLink",
    "allocate_noga_jobs_to_nace",
    "all_links",
    "links_for_nace",
    "links_for_noga",
    "mapping_path",
    "top_noga_matches_for_nace",
    "top_nace_matches_for_noga",
]

__version__ = "1.0.0"
