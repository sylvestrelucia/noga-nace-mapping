import csv
from pathlib import Path

from noga_nace_mapping.export import (
    CSV_COLUMNS,
    PACKAGE_DATA_DIR,
    REPO_DATA_DIR,
    export_from_mapping_file,
    mirror_exports_to_repo_data,
    skos_mapping_relation,
)
from noga_nace_mapping.locales import NACE_EXPORT_LOCALES, NOGA_EXPORT_LOCALES
from noga_nace_mapping.official_ids import (
    NOGA_SCHEME_URI,
    nace_uri_for_code,
    noga_uri_for_code,
    noga_uri_for_slug,
)
from noga_nace_mapping.mapping import all_links, mapping_path


def test_csv_export_row_count_matches_mapping():
    exports = export_from_mapping_file(formats={"csv"})
    csv_path = next(path for path in exports if path.suffix == ".csv")
    with csv_path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 996
    assert list(rows[0].keys()) == list(CSV_COLUMNS)


def test_csv_export_includes_labels_for_known_link():
    exports = export_from_mapping_file(formats={"csv"})
    csv_path = next(path for path in exports if path.suffix == ".csv")
    with csv_path.open(encoding="utf-8", newline="") as handle:
        rows = {row["nace_slug"]: row for row in csv.DictReader(handle)}
    row = rows["nace-62-01"]
    assert row["noga_slug"] == "noga-j-62"
    assert row["noga_code"] == "62"
    assert row["nace_code"] == "62.01"
    assert row["noga_uri"] == f"{NOGA_SCHEME_URI}/62"
    assert row["nace_uri"] == "http://data.europa.eu/ux2/nace2/6201"
    assert row["noga_uri"] != row["nace_uri"]
    assert row["section"] == "J"
    assert row["noga_level"] == "division"
    assert row["nace_level"] == "class"
    assert "Computer programming" in row["nace_label_en"]
    assert row["noga_label_de"]
    assert row["nace_label_de"]
    assert row["nace_label_fr"]


def test_csv_export_includes_all_locale_columns():
    assert tuple(f"noga_label_{locale}" for locale in NOGA_EXPORT_LOCALES) == tuple(
        column for column in CSV_COLUMNS if column.startswith("noga_label_")
    )
    assert tuple(f"nace_label_{locale}" for locale in NACE_EXPORT_LOCALES) == tuple(
        column for column in CSV_COLUMNS if column.startswith("nace_label_")
    )


def test_rdf_export_parses_and_contains_skos_links():
    exports = export_from_mapping_file(formats={"rdf"})
    ttl_path = next(path for path in exports if path.suffix == ".ttl")
    content = ttl_path.read_text(encoding="utf-8")

    assert "@prefix skos:" in content
    assert "a nnm:CrosswalkLink" in content
    assert content.count("a nnm:CrosswalkLink") == 996
    assert "http://data.europa.eu/ux2/nace2/6201" in content
    assert "skos:exactMatch" in content
    assert "skos:relatedMatch" in content


def test_nace_uri_and_skos_relation_conventions():
    assert nace_uri_for_code("J") == "http://data.europa.eu/ux2/nace2/J"
    assert nace_uri_for_code("62") == "http://data.europa.eu/ux2/nace2/62"
    assert nace_uri_for_code("62.01") == "http://data.europa.eu/ux2/nace2/6201"
    assert noga_uri_for_code("J") == f"{NOGA_SCHEME_URI}/J"
    assert noga_uri_for_code("62") == f"{NOGA_SCHEME_URI}/62"
    assert noga_uri_for_slug("noga-j-62") == f"{NOGA_SCHEME_URI}/62"
    assert skos_mapping_relation("division", "division") == "skos:exactMatch"
    assert skos_mapping_relation("division", "class") == "skos:relatedMatch"


def test_export_paths_follow_mapping_json_location(tmp_path: Path):
    mapping_copy = tmp_path / "custom_mapping.json"
    mapping_copy.write_text(mapping_path().read_text(encoding="utf-8"), encoding="utf-8")
    exports = export_from_mapping_file(mapping_copy, formats={"all"})
    assert (tmp_path / "custom_mapping.csv") in exports
    assert (tmp_path / "custom_mapping.ttl") in exports


def test_all_links_still_load_from_package_mapping():
    assert len(all_links()) == 996


def test_mirror_exports_to_repo_data_copies_package_artifacts(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(
        "noga_nace_mapping.export.REPO_DATA_DIR",
        tmp_path / "data",
    )
    json_path = PACKAGE_DATA_DIR / "noga_nace_mapping.json"
    csv_path = PACKAGE_DATA_DIR / "noga_nace_mapping.csv"
    mirrored = mirror_exports_to_repo_data([csv_path], json_path)
    assert (tmp_path / "data" / "noga_nace_mapping.json") in mirrored
    assert (tmp_path / "data" / "noga_nace_mapping.csv") in mirrored


def test_mirror_skips_non_package_paths(tmp_path: Path):
    custom_json = tmp_path / "custom.json"
    custom_json.write_text("{}", encoding="utf-8")
    assert mirror_exports_to_repo_data([], custom_json) == []
