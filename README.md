# Lémann Index (Updated) — Streamlit Calculator

*A lightweight Streamlit app implementing the updated Organ and Global Lémann Index (Pariente et al.,* *Gastroenterology* *2021) for research and educational use.*

**Status:** experimental • research/educational use only • not a medical device

## What it does

* Collects worst-lesion features per organ (upper, small bowel, colon/rectum, anus).
* Maps features → grades → points per the updated Lémann Index.
* Normalises by organ segment count; computes per-organ LI.
* Computes Global LI via organ weights.
* Exports ID + per-organ LI + Global LI as CSV.

## What it does *not* do

* No image parsing; no adjudication; not validated for all edge cases.
* **Do NOT use for patient care.**


## Run

Clone this repository, install dependencies, and launch locally:

```bash
pip install -r requirements.txt
streamlit run app/app.py
```

## Reproducibility

* **Python:** 3.9–3.12 recommended
* **Install:** `pip install -r requirements.txt`
* **Run:** `streamlit run app.py`
* Dependencies are **pinned** in `requirements.txt`. A fully locked snapshot can be saved via `pip freeze > requirements.lock` and attached to the release; the Zenodo archive preserves the exact release (code + README + demo assets).

## How to cite
> Sarikhani M. Lémann Index (Updated) — Streamlit Calculator (v0.1.0). 2025.  
> DOI: **[10.5281/zenodo.17514287](https://doi.org/10.5281/zenodo.17514287)**

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.17514287.svg)](https://doi.org/10.5281/zenodo.17514287)


## Versioning

* **v0.1.0** — first public prototype (updated Organ & Global Lémann Index, CSV export, disclaimer)
* Semantic-ish versioning: patch = fixes, minor = features, major = breaking changes.

## Scope & Limitations

* Research/educational use only — **not for clinical decision-making**.
* Implements the updated Organ & Global Lémann Index per Pariente et al. (*Gastroenterology* 2021).
* No PHI is accepted or stored by this app.

## References

* Pariente B, et al. *Validation and Update of the Lémann Index to Measure Cumulative Structural Bowel Damage in Crohn’s Disease.* *Gastroenterology.* 2021;161(3):853–864.e13. doi:10.1053/j.gastro.2021.05.049.
* Pariente B, et al. *Development of the Lémann Index to assess cumulative structural bowel damage in Crohn’s disease.* *Gastroenterology.* 2015;148(1):52–63.e3. doi:10.1053/j.gastro.2014.09.015.

## License

This project is released under the **MIT License**. See [`LICENSE`](./LICENSE).
