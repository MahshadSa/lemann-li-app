# Lémann Index (Updated) — Streamlit Calculator

**Status:** experimental • research/educational use only • not a medical device

## What it does
- Collects worst-lesion features per organ (upper, small bowel, colon/rectum, anus).
- Maps features → grades → points per updated Lémann Index.
- Normalises by organ segment count; computes Global LI via organ weights.
- Exports ID + per-organ LI + Global LI as CSV.

## What it does *not* do
- No image parsing; no adjudication; not validated for all edge cases.
- **Do NOT use for patient care.**

## Run
```bash
pip install -r requirements.txt
streamlit run app/app.py
```
## Reference (original index)

Pariente B, et al. _Validation and Update of the Lémann Index to Measure Cumulative Structural Bowel Damage in Crohn’s Disease._ **Gastroenterology.** 2021;161(3):853-864.e13. doi:10.1053/j.gastro.2021.05.049.  
Also see the original development paper: Pariente B, et al. **Gastroenterology.** 2015;148(1):52-63.e3. doi:10.1053/j.gastro.2014.09.015.

