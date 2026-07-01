# NOGA–NACE Mapping: Swiss NOGA 2008 ↔ EU NACE Rev. 2 Industry Classification Crosswalk

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

> Machine-readable **NOGA ↔ NACE crosswalk** for Switzerland and the EU — JSON, CSV, RDF/SKOS, and a Python library.

**NOGA–NACE Mapping** packages the **official structural correspondence** between [**NOGA 2008**](https://www.bfs.admin.ch/bfs/en/home/statistics/industry-services/nomenclatures/noga.html) (Swiss industry classification, [BFS](https://www.bfs.admin.ch)/OFS) and [**NACE Rev. 2**](https://ec.europa.eu/eurostat/web/nace) (EU economic statistics taxonomy, [Eurostat](https://ec.europa.eu/eurostat)). Labels come from [Eurostat EU Vocabularies](https://op.europa.eu/en/web/eu-vocabularies/dataset/-/resource?uri=http://publications.europa.eu/resource/dataset/nace2); mappings follow the BFS-documented alignment of NOGA 2008 levels 1–4 with NACE Rev. 2. Use it for **NOGA to NACE conversion**, correspondence tables, Swiss–EU statistical harmonization, and job allocation across industry classifications.

*Keywords: NOGA, NACE, NACE Rev. 2, NOGA 2008, Switzerland, Swiss statistics, BFS, Eurostat, industry classification, economic statistics, crosswalk, correspondence table, SKOS, RDF, taxonomy, Python.*

Repository: [github.com/sylvestrelucia/noga-nace-mapping](https://github.com/sylvestrelucia/noga-nace-mapping)

## See also (official sources)

- [BFS NOGA 2008 portal](https://www.bfs.admin.ch/bfs/en/home/statistics/industry-services/nomenclatures/noga.html) — Swiss Federal Statistical Office industry nomenclature
- [Eurostat NACE Rev. 2](https://ec.europa.eu/eurostat/web/nace) — EU statistical classification of economic activities
- [EU Vocabularies — NACE Rev. 2 dataset](https://op.europa.eu/en/web/eu-vocabularies/dataset/-/resource?uri=http://publications.europa.eu/resource/dataset/nace2) — multilingual labels and RDF concepts
- [KUBB 2008](https://www.kubb-tool.bfs.admin.ch/en/noga/2008) — BFS interactive NOGA coding and lookup tool

## Table of contents

- [See also (official sources)](#see-also-official-sources)
- [The problem](#the-problem)
- [Solution space](#solution-space)
- [Why this repository](#why-this-repository)
- [Use cases](#use-cases)
- [Data](#data)
- [Python library](#python-library)
- [Regenerate the mapping](#regenerate-the-mapping)
- [Slug conventions](#slug-conventions)
- [FAQ](#faq)
- [License](#license)
- [Data sources & legal notice](#data-sources--legal-notice)
- [References and sources](#references-and-sources)

## The problem

Switzerland and the EU classify businesses by economic activity, but they use different nomenclatures:

| | **NOGA 2008** | **NACE Rev. 2** |
|---|---------------|-----------------|
| Issuer | BFS/OFS (Switzerland) | Eurostat (EU) |
| Used in | Swiss business register, federal statistics, cantonal data | Eurostat, EU member states, cross-country research |
| Depth | Up to 6 digits (Swiss-specific detail at levels 5–6) | 4 levels: section → division → group → class |

In practice this creates friction whenever you need to **compare or combine** Swiss and European datasets:

- A firm coded `NOGA 62` in the Swiss business register may need to align with `NACE 62.01` in an EU labour-market survey.
- Employment totals published at NOGA division level must sometimes be broken down to NACE class level (or the reverse).
- Dashboards, research pipelines, and ETL jobs need a **stable, machine-readable crosswalk** — not a one-off manual lookup.

The official relationship is well documented: BFS states that **NOGA 2008 levels 1–4 are identical to NACE Rev. 2**. What is harder to find is that relationship packaged for developers — as JSON, with multilingual labels, and with a small API you can import.

## Solution space

Several approaches exist, each with trade-offs:

| Approach | Strengths | Limitations |
|----------|-----------|-------------|
| **Identity at levels 1–4** (official BFS position) | Correct for sections, divisions, groups, and classes; no ambiguity | Not published as a single downloadable crosswalk file; you must derive it from the classification trees |
| **[KUBB 2008](https://www.kubb-tool.bfs.admin.ch/en/noga/2008)** (BFS coding tool) | Authoritative lookup, keyword search, NOGA 2008 ↔ NOGA 2002 | Interactive web UI; not designed for batch pipelines |
| **BFS conversion keys** ([NOGA 2002 ↔ NOGA 2008](https://www.bfs.admin.ch/bfsstatic/dam/assets/348788/master)) | Official version-migration tables, empirical keys from double coding | Covers *version change*, not a standalone NOGA↔NACE product; Excel/PDF format |
| **Eurostat correspondence tables** ([EU Vocabularies](https://op.europa.eu/en/web/eu-vocabularies/dataset/-/resource?uri=http://publications.europa.eu/resource/dataset/nace2)) | NACE Rev. 1.1 ↔ Rev. 2, ISIC links, full hierarchy with notes | NACE-centric; no Swiss 5th/6th digit NOGA codes |
| **Manual concordance / ad-hoc rules** | Quick for one-off projects | Error-prone, hard to audit, not reproducible |
| **Label-similarity matching** (algorithmic) | Can propose multiple ranked targets | Not official; confidence scores are heuristic, not statistical |

There is **no separate BFS correspondence table for NOGA 2008 ↔ NACE Rev. 2** at levels 1–4, because the codes are the same. The gap is in **delivery**: turning that official alignment into something pipelines can consume.

## Why this repository

This project fills the gap between official statistics publications and everyday data engineering:

1. **Machine-readable output** — [`data/noga_nace_mapping.json`](data/noga_nace_mapping.json) is a flat, filterable link table (996 links) usable from Python, R, SQL, or any JSON-aware tool.
2. **Faithful to official sources** — mappings follow the documented BFS alignment (levels 1–4 identical to NACE Rev. 2); labels are fetched from [Eurostat EU Vocabularies](https://op.europa.eu/en/web/eu-vocabularies/dataset/-/resource?uri=http://publications.europa.eu/resource/dataset/nace2), with snapshots under [`data/sources/`](data/sources/).
3. **Small Python library** — `links_for_nace()`, `top_noga_matches_for_nace()`, `allocate_noga_jobs_to_nace()` for common crosswalk operations without reimplementing hierarchy logic.
4. **Reproducible pipeline** — `fetch-official-labels` and `build-noga-nace-mapping` regenerate everything from primary sources; no opaque hand-editing.
5. **Open and citeable** — MIT license, [`CITATION.cff`](CITATION.cff), and documented references to BFS/Eurostat publications.

It is **not** a replacement for BFS or Eurostat publications when legal or methodological authority is required. It is a practical bridge for analysts and developers who already know the codes should match and want that fact encoded in their toolchain.

## Use cases

- **Convert NOGA codes to NACE** (and vice versa) via the official 1:1 alignment at section and division level
- **Crosswalk employment or firm counts** from Swiss NOGA reporting to Eurostat NACE aggregates
- **Allocate jobs** from a NOGA division total to underlying NACE classes proportionally
- **Harmonize datasets** that mix Swiss (NOGA 2008) and EU (NACE Rev. 2) industry labels
- **Build analytics pipelines** that need a machine-readable NOGA↔NACE correspondence table

## Data

The pre-built mapping is in [`data/noga_nace_mapping.json`](data/noga_nace_mapping.json):

- **996 links** between NOGA and NACE concepts
- **109 level-aligned links** — section ↔ section and division ↔ division (same official code)
- **887 fine-level links** — NACE groups and classes linked to their parent NOGA division
- Method: `official-structural` per [BFS NOGA 2008](https://www.bfs.admin.ch/bfs/en/home/statistics/industry-services/nomenclatures/noga.html) (levels 1–4 identical to NACE Rev. 2)
- Labels: [Eurostat EU Vocabularies](https://op.europa.eu/en/web/eu-vocabularies/dataset/-/resource?uri=http://publications.europa.eu/resource/dataset/nace2) — NACE in all 26 EU SPARQL languages; NOGA sections/divisions in Swiss locales (de, fr, it, en); snapshot in [`data/sources/`](data/sources/)

### Link schema

```json
{
  "noga_slug": "noga-j-62",
  "nace_slug": "nace-62-01",
  "noga_level": "division",
  "nace_level": "class",
  "noga_code": "62",
  "nace_code": "62.01",
  "noga_uri": "https://register.ld.admin.ch/i14y/concept/nogaCode/62",
  "nace_uri": "http://data.europa.eu/ux2/nace2/6201"
}
```

| Field | Description |
|-------|-------------|
| `noga_slug` | Project slug for NOGA (`noga-j`, `noga-j-62`, …); kept for backward compatibility |
| `nace_slug` | Project slug for NACE (`nace-j`, `nace-62`, `nace-62-01`, …) |
| `noga_code` | Official NOGA notation (`J`, `62`, …) — levels 1–4 identical to NACE Rev. 2 |
| `nace_code` | Official NACE Rev. 2 notation (`J`, `62`, `62.0`, `62.01`, …) |
| `noga_uri` | Swiss I14Y/LINDAS NOGA concept URI ([`nogaCode`](https://register.ld.admin.ch/i14y/concept/nogaCode) + official notation) |
| `nace_uri` | EU Vocabularies NACE Rev. 2 concept URI (`http://data.europa.eu/ux2/nace2/…`) |
| `noga_level` | `section` or `division` |
| `nace_level` | `section`, `division`, `group`, or `class` |

**Official IDs vs slugs:** Use `noga_code` / `nace_code` and `noga_uri` / `nace_uri` for external systems. `noga_uri` uses the Swiss I14Y register ([`register.ld.admin.ch`](https://register.ld.admin.ch/i14y/concept/nogaCode)); `nace_uri` uses EU Vocabularies. Even when codes match at levels 1–4, the two URI namespaces differ. Slugs remain stable internal keys. NOGA 2008 levels 5–6 (Swiss 6-digit detail) are not in this mapping; only levels 1–4 are covered.

Flat exports are also available:

| File | Format | Description |
|------|--------|-------------|
| [`data/noga_nace_mapping.csv`](data/noga_nace_mapping.csv) | CSV | All 996 links — **39 columns**: 9 base fields + 4 NOGA label columns + 26 NACE label columns |
| [`data/noga_nace_mapping.ttl`](data/noga_nace_mapping.ttl) | Turtle RDF | SKOS crosswalk: NOGA concepts use official I14Y `nogaCode` URIs; NACE concepts use `http://data.europa.eu/ux2/nace2/`; link relations are `skos:exactMatch` (same level) or `skos:relatedMatch` (NACE group/class → NOGA division) |

Regenerate exports with `build-noga-nace-mapping` (default: JSON + CSV + RDF, mirrored to repo `data/`) or `export-noga-nace-mapping` from an existing JSON file.

### CSV columns (39)

| Column group | Columns |
|--------------|---------|
| **Base (9)** | `noga_slug`, `nace_slug`, `noga_level`, `nace_level`, `noga_code`, `nace_code`, `noga_uri`, `nace_uri`, `section` |
| **NOGA labels (4)** | `noga_label_en`, `noga_label_de`, `noga_label_fr`, `noga_label_it` |
| **NACE labels (26)** | `nace_label_en`, then `nace_label_{locale}` for each remaining EU SPARQL locale (alphabetical): `bg`, `cs`, `da`, `de`, `el`, `es`, `et`, `fi`, `fr`, `hr`, `hu`, `it`, `lt`, `lv`, `mt`, `nl`, `no`, `pl`, `pt`, `ro`, `ru`, `sk`, `sl`, `sv`, `tr` |

### Supported locales

| Side | Locales | Source |
|------|---------|--------|
| **NACE** (EU) | `bg`, `cs`, `da`, `de`, `el`, `en`, `es`, `et`, `fi`, `fr`, `hr`, `hu`, `it`, `lt`, `lv`, `mt`, `nl`, `no`, `pl`, `pt`, `ro`, `ru`, `sk`, `sl`, `sv`, `tr` | [EU Vocabularies NACE Rev. 2 SPARQL](https://publications.europa.eu/webapi/rdf/sparql) `skos:prefLabel` |
| **NOGA** (Swiss) | `de`, `fr`, `it`, `en` | Same Eurostat labels at levels 1–4 (BFS alignment); Romansh (`rm`) is not published in EU Vocabularies |

Explanatory notes (`xkos:coreContentNote`) are stored for NACE where available: `bg`, `cs`, `de`, `en`, `es`, `fr`, `hr`, `hu`, `lt`, `pl`, `ru`, `tr`.

## Python library

```bash
pip install noga-nace-mapping
```

```python
from noga_nace_mapping import top_noga_matches_for_nace, links_for_nace

# Top NOGA divisions for a NACE class
for link in top_noga_matches_for_nace("nace-62-01"):
    print(link.noga_slug, link.noga_uri, link.nace_uri)

# All links for a NACE code
links_for_nace("nace-62-01")
```

### Allocate job counts from NOGA to NACE

```python
from noga_nace_mapping import allocate_noga_jobs_to_nace

allocated = allocate_noga_jobs_to_nace({"noga-j-62": 100})
# → {"nace-62-01": 45.2, "nace-62-02": 32.1, ...}
```

## Regenerate the mapping

```bash
git clone https://github.com/sylvestrelucia/noga-nace-mapping.git
cd noga-nace-mapping
pip install -e ".[dev]"

# 1. Fetch official NACE Rev. 2 labels from EU Vocabularies (requires network)
fetch-official-labels
# or: python scripts/fetch_official_labels.py

# 2. Build the official NOGA ↔ NACE mapping (JSON + CSV + RDF)
build-noga-nace-mapping
# Writes src/noga_nace_mapping/data/ and mirrors JSON, CSV, and RDF to data/
pytest
```

The builder applies the official BFS alignment:

1. Maps NOGA sections/divisions to NACE sections/divisions with the same letter or two-digit code.
2. Maps each NACE group and class to its parent NOGA division, reflecting that NOGA 2008 levels 1–4 match NACE Rev. 2.

Package data lives under `src/noga_nace_mapping/data/`; `build-noga-nace-mapping` auto-mirrors artifacts to the repo-root [`data/`](data/) directory. Re-export CSV/RDF only with `export-noga-nace-mapping`.

## Slug conventions

Project slugs are stable internal keys. **Prefer `*_code` and `*_uri` for external systems** — `noga_uri` from the Swiss I14Y register, `nace_uri` from EU Vocabularies.

| Taxonomy | Section example | Division example | Fine level | Concept URI example |
|----------|-----------------|------------------|------------|---------------------|
| NOGA | `noga-j` → `J` | `noga-j-62` → `62` | — (levels 5–6 not mapped) | `https://register.ld.admin.ch/i14y/concept/nogaCode/62` |
| NACE | `nace-j` → `J` | `nace-62` → `62` | `nace-62-01` → `62.01` | `http://data.europa.eu/ux2/nace2/6201` |

NACE URIs drop dots from notations (`62.01` → `…/6201`, `62.0` → `…/620`). Section letters are uppercase in both schemes (`…/J`). NOGA URIs use the official notation as the path segment (`62` → `…/nogaCode/62`).

## FAQ

### How do I convert a NOGA code to NACE?

Use `top_nace_matches_for_noga("noga-j-62")` to get the matching NACE division, or read the JSON mapping directly.

### How do I convert a NACE code to NOGA?

Use `top_noga_matches_for_nace("nace-62-01")` — the parent NOGA division (`noga-j-62`) per the official hierarchy.

### What is the difference between NOGA and NACE?

**NOGA** (Nomenclature Générale des Activités économiques) is Switzerland's industry classification, derived from but not identical to the EU's **NACE** (Nomenclature statistique des activités économiques). At levels 1–4, NOGA 2008 and NACE Rev. 2 share the same codes; Switzerland adds detail at levels 5–6. This repository encodes that official alignment in machine-readable form.

### Is there a BFS correspondence table for NOGA ↔ NACE?

Not as a separate product. BFS documents that levels 1–4 are identical to NACE Rev. 2. For **version migration** (NOGA 2002 ↔ NOGA 2008), see the [conversion keys report](https://www.bfs.admin.ch/bfsstatic/dam/assets/348788/master).

### Which NOGA and NACE versions are covered?

NOGA 2008 and NACE Rev. 2 (the version used by Eurostat).

### Can I use the JSON file without Python?

Yes. [`data/noga_nace_mapping.json`](data/noga_nace_mapping.json) is a standalone dataset — filter by `noga_slug` or `nace_slug` in any language or tool.

## License

The **software** (Python library, build scripts, and derived mapping compilation) is released under the [MIT License](LICENSE).

Bundled **official labels and reference documents** remain subject to their upstream terms — see [Data sources & legal notice](#data-sources--legal-notice). The MIT license does not override third-party data licenses.

## Data sources & legal notice

> **This is not legal advice.** The notes below summarize our practical understanding of upstream terms as of 2026. Verify suitability and compliance for your own use case, especially for commercial redistribution.

### Disclaimer

- This project is **not affiliated with, endorsed by, or sponsored by** the Swiss Federal Statistical Office (BFS/OFS), Eurostat, the European Commission, or the Publications Office of the EU.
- The mapping, labels, and software are provided **“as is”**, without warranty. Maintainers are not liable for errors, omissions, or downstream use.
- **You are responsible** for confirming that this crosswalk meets your regulatory, statistical, or business requirements. For authoritative definitions, consult [BFS NOGA publications](https://www.bfs.admin.ch/bfs/en/home/statistics/industry-services/nomenclatures/noga.html) and [Eurostat NACE materials](https://ec.europa.eu/eurostat/web/nace).

### What this repository uses

| Source | Role in this repo | License / terms | Attribution |
|--------|-------------------|-----------------|-------------|
| **Eurostat NACE Rev. 2** ([EU Vocabularies](https://op.europa.eu/en/web/eu-vocabularies/dataset/-/resource?uri=http://publications.europa.eu/resource/dataset/nace2), [SPARQL](https://publications.europa.eu/webapi/rdf/sparql)) | Multilingual labels and explanatory notes in `nace_labels.json`, `noga_labels.json` (levels 1–4), and `data/sources/nace_r2_eurostat_sparql.json` | [Eurostat copyright & reuse](https://ec.europa.eu/eurostat/en/help/copyright-notice): free reuse (commercial and non-commercial) with **source acknowledgement**; indicate **modifications** (reformatted JSON snapshots, subset for NOGA sections/divisions). Editorial EU content is generally [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). | Source: Eurostat / EU Vocabularies (NACE Rev. 2). |
| **BFS NOGA 2008 structural alignment** | Mapping logic in `builder.py`: levels 1–4 are treated as identical to NACE Rev. 2 (documented BFS position); **no BFS label text is copied** for levels 1–4 | BFS publications state *“Reproduction with mention of source authorized (except for commercial purposes)”* — see [NOGA 2008 titles (ISBN 978-3-303-00372-5)](https://www.bfs.admin.ch/bfsstatic/dam/assets/344621/master). The crosswalk itself is an **algorithmic derivation** of publicly documented code correspondence, not a republished BFS correspondence table. | Swiss Federal Statistical Office (BFS/OFS), NOGA 2008. |
| **BFS conversion keys report** | Reference only: [Use of conversion keys for NOGA 2002–2008](https://www.bfs.admin.ch/bfsstatic/dam/assets/348788/master) (NOGA 2002 ↔ NOGA 2008, not NOGA ↔ NACE); linked, not bundled | Same BFS reproduction policy as above; obtain the PDF from BFS directly | Jann Potterat, Swiss Federal Statistical Office (BFS/OFS), 2012, FSO order no. 338-0067-05. |
| **This repository’s mapping exports** | `noga_nace_mapping.json` / `.csv` / `.ttl` — compiled crosswalk with project NOGA URIs, EU NACE URIs, and Eurostat labels | **MIT** for the compilation and software; embedded Eurostat label text remains under Eurostat terms. | Cite this repository ([`CITATION.cff`](CITATION.cff)) **and** upstream sources above. |

Metadata for bundled snapshots: [`data/sources/manifest.json`](data/sources/manifest.json).

### Practical compliance assessment

| Practice | Assessment |
|----------|------------|
| Fetching NACE labels via official SPARQL and bundling JSON snapshots | **Generally permitted** under Eurostat reuse policy, with attribution and a note that labels were reformatted/repackaged. |
| Publishing an open-source NOGA ↔ NACE crosswalk derived from documented structural identity | **Generally reasonable**: the alignment at levels 1–4 is an official, public fact; this repo encodes it rather than copying proprietary tables. |
| CSV/RDF exports including official Eurostat labels | **Permitted with attribution** to Eurostat; state that labels were extracted from EU Vocabularies and may have been reformatted. |
| Commercial use of the **Python library and mapping JSON** with Eurostat labels | **Generally permitted** under Eurostat terms. |
| Linking to official BFS publications (e.g. conversion keys PDF) | **Generally fine**; this repository links rather than bundles BFS PDFs. |

**Gaps to be aware of:** Swiss law ([Art. 5 Federal Copyright Act](https://www.fedlex.admin.ch/eli/cc/1992/19_1992_1011/en#art_5)) exempts certain official works from copyright, but BFS still publishes explicit reproduction terms — when in doubt, contact BFS ([noga@bfs.admin.ch](mailto:noga@bfs.admin.ch)). Do not imply official endorsement. NOGA and NACE are statistical classifications, not trademarks of this project.

### Recommended actions for downstream users

1. **Attribute Eurostat** when you redistribute labels or exports that include NACE text.
2. **Attribute BFS** when you refer to NOGA structural alignment or Swiss classification authority.
3. **State modifications** if you alter labels, codes, or mappings.
4. **Commercial products** that embed substantial BFS document text or redistribute BFS PDFs: review [BFS conditions of use](https://www.bfs.admin.ch/bfs/en/home/services/geostat/conditions-use.html) and seek written permission if needed.
5. **Consult qualified counsel** for high-stakes regulatory, legal, or commercial deployments.

## References and sources

### Official classifications

| Source | What it provides | Link |
|--------|------------------|------|
| **NOGA 2008** (Swiss Federal Statistical Office, BFS/OFS) | Switzerland's national industry classification; levels 1–4 align with NACE Rev. 2 | [BFS NOGA portal](https://www.bfs.admin.ch/bfs/en/home/statistics/industry-services/nomenclatures/noga.html) |
| **NOGA 2008 — titles** (BFS, 2008) | Official section and division titles (de/fr/en); ISBN 978-3-303-00372-5 | [PDF](https://www.bfs.admin.ch/bfsstatic/dam/assets/344621/master) |
| **NOGA 2008 — explanatory notes** (BFS) | Definitions and scope of NOGA codes | [BFS publications](https://www.bfs.admin.ch/bfs/en/home/statistics/industry-services/nomenclatures/noga.html) |
| **NACE Rev. 2** (Eurostat) | EU statistical classification of economic activities | [Eurostat NACE](https://ec.europa.eu/eurostat/web/nace) |
| **Regulation (EC) No 1893/2006** | Legal basis for NACE Rev. 2 (in force from 1 Jan 2008) | [EUR-Lex](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A32006R1893) |
| **NACE Rev. 2 manual** (Eurostat, 2008) | Structure, concepts, and item descriptions; ISBN 978-92-79-04741-1 | [Eurostat publication KS-RA-07-015](https://ec.europa.eu/eurostat/web/products-manuals-and-guidelines/-/KS-RA-07-015) |
| **Eurostat classifications** | Correspondence tables and code lists (successor to RAMON) | [EU Vocabularies](https://op.europa.eu/en/web/eu-vocabularies/dataset/-/resource?uri=http://publications.europa.eu/resource/dataset/nace2) · [Euro SDMX Registry](https://sdmx.org/?page_id=3045) |
| **Use of conversion keys for NOGA 2002–2008** (BFS, 2012) | Official NOGA 2002 ↔ NOGA 2008 conversion keys (empirical & official); FSO order no. 338-0067-05; ISBN 978-3-303-00473-9 | [PDF](https://www.bfs.admin.ch/bfsstatic/dam/assets/348788/master) |

BFS also publishes **official correspondence tables** between classification versions (e.g. NACE Rev. 1.1 ↔ Rev. 2, NOGA 2002 ↔ NOGA 2008). See the [NOGA 2008 methodological manual](https://dam-api.bfs.admin.ch/hub/api/dam/assets/344669/master) (ch. 4–5) and [**Use of conversion keys for NOGA 2002–2008**](https://www.bfs.admin.ch/bfsstatic/dam/assets/348788/master) (BFS, 2012; FSO order no. 338-0067-05, ISBN 978-3-303-00473-9).

### This repository

| Asset | Origin | Notes |
|-------|--------|-------|
| [`data/noga_nace_mapping.json`](data/noga_nace_mapping.json) | **Official BFS alignment** (BFS/OFS) | Section/division 1:1; NACE groups/classes linked to parent NOGA division |
| [`data/sources/nace_r2_eurostat_sparql.json`](data/sources/nace_r2_eurostat_sparql.json) | **Eurostat EU Vocabularies** (SPARQL snapshot) | Raw official NACE Rev. 2 labels and explanatory notes |
| [`src/noga_nace_mapping/data/noga_labels.json`](src/noga_nace_mapping/data/noga_labels.json) | **NOGA 2008** sections/divisions (levels 1–4 = NACE Rev. 2) | Labels from Eurostat; see BFS NOGA portal |
| [`src/noga_nace_mapping/data/nace_labels.json`](src/noga_nace_mapping/data/nace_labels.json) | **Eurostat NACE Rev. 2** | Official multilingual titles and explanatory notes |

### Mapping methodology

1. **Level-aligned links** (109) — NOGA sections/divisions mapped to NACE sections/divisions with the same letter or two-digit code, per the official NOGA 2008 ↔ NACE Rev. 2 alignment at levels 1–4.
2. **Fine-level links** (887) — Each NACE group and class maps to its parent NOGA division.

The JSON schema stores levels and official codes only (no `match_kind` or `match_pct`). RDF exports express alignment via `skos:exactMatch` when `noga_level == nace_level`, otherwise `skos:relatedMatch`.

Fetch labels with `fetch-official-labels`, then regenerate with `build-noga-nace-mapping` (see [Regenerate the mapping](#regenerate-the-mapping)).

### Citing this project

```bibtex
@software{lucia_noga_nace_mapping,
  author  = {Lucia, Sylvestre},
  title   = {{NOGA–NACE Mapping: Swiss NOGA 2008 ↔ EU NACE Rev. 2 Industry Classification Crosswalk}},
  year    = {2026},
  url     = {https://github.com/sylvestrelucia/noga-nace-mapping},
  version = {1.0.0}
}
```

Or use the machine-readable [`CITATION.cff`](CITATION.cff) at the repository root.
