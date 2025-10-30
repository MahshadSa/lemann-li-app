__version__ = "0.1.0"

import streamlit as st
import pandas as pd
from typing import Dict, Any, List

st.set_page_config(page_title="Lémann Index (updated)", layout="wide")
st.title("Lémann Index (updated) – prototype calculator")
st.caption(
    "Research/educational use only – NOT for clinical decisions. "
    "Implements the updated Organ and Global Lémann Index from Pariente et al., Gastroenterology 2021."
)

# CONFIG
COEFS = {
    "upper":        {("str", 1): 0.0, ("str", 2): 3.5, ("str", 3): 5.0,
                     ("pen", 1): 1.0, ("pen", 2): 1.5, ("pen", 3): 2.0},
    "small_bowel":  {("str", 1): 0.0, ("str", 2): 3.0, ("str", 3): 5.0,
                     ("pen", 1): 0.0, ("pen", 2): 1.5, ("pen", 3): 4.0},
    "colon_rectum": {("str", 1): 0.5, ("str", 2): 2.0, ("str", 3): 5.0,
                     ("pen", 1): 1.0, ("pen", 2): 2.5, ("pen", 3): 4.5},
    "anus":         {("str", 1): 0.0, ("str", 2): 2.0, ("str", 3): 3.5,
                     ("pen", 1): 0.0, ("pen", 2): 2.5, ("pen", 3): 3.0},
}

GLOBAL_WEIGHTS = {
    "upper": 2.0,
    "small_bowel": 4.0,
    "colon_rectum": 3.0,
    "anus": 2.5,
}

SEGMENTS = {
    "upper": ["oesophagus", "stomach", "duodenum"],          # 3
    "small_bowel": [f"bin_{i+1:02d}" for i in range(20)],    # 20
    "colon_rectum": ["caecum", "ascending", "transverse", "descending", "sigmoid", "rectum"],  # 6
    "anus": ["anus"],                                        # treat anus as one unit
}

# explicit denominators (to avoid /2 for anus)
DENOM = {
    "upper": 3,
    "small_bowel": 20,
    "colon_rectum": 6,
    "anus": 1,
}

# STATE
if "rows" not in st.session_state:
    st.session_state.rows: List[Dict[str, Any]] = []
if "form_prefill" not in st.session_state:
    st.session_state.form_prefill = None
if "results" not in st.session_state:
    st.session_state.results: List[Dict[str, Any]] = []
if "id_set" not in st.session_state:
    st.session_state.id_set = set()
if "form_nonce" not in st.session_state:
    st.session_state.form_nonce = 0


# HELPERS
def _reset_organ_widget_state(reset_segment: bool = False) -> None:
    """Bump nonce so all widget keys refresh; optionally clear current segment."""
    st.session_state.form_nonce += 1
    st.session_state.form_prefill = None
    if reset_segment:
        st.session_state.pop("ui_segment", None)

# Organ-specific input widgets
def organ_inputs(organ: str, pref: Dict[str, Any] | None, nonce: int) -> Dict[str, Any]:
    f: Dict[str, Any] = {}

    def get_pref(key: str, default: Any) -> Any:
        return (pref or {}).get(key, default)

    if organ in ("upper", "small_bowel", "colon_rectum"):
        st.markdown("**Stricturing**")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            f["has_str"] = st.checkbox(
                "Stricture present",
                get_pref("has_str", False),
                key=f"{organ}_{nonce}_has_str",
            )
            f["thick_mm"] = st.number_input(
                "Wall thick. (mm)", 0.0, 30.0,
                float(get_pref("thick_mm", 0.0)), 0.5,
                key=f"{organ}_{nonce}_thick",
            )
        with c2:
            f["seg_enh"] = st.checkbox(
                "Segmental enh.",
                get_pref("seg_enh", False),
                key=f"{organ}_{nonce}_seg_enh",
            )
            f["mural_strat"] = st.checkbox(
                "Mural strat.",
                get_pref("mural_strat", False),
                key=f"{organ}_{nonce}_mural",
            )
        with c3:
            f["stricture"] = st.checkbox(
                "Stricture confirmed",
                get_pref("stricture", False),
                key=f"{organ}_{nonce}_stric",
            )
            f["has_pd"] = st.checkbox(
                "PD",
                get_pref("has_pd", False),
                key=f"{organ}_{nonce}_pd",
            )
        with c4:
            f["lumen_red_pct"] = st.number_input(
                "Lumen red. (%) (colon)",
                0, 100,
                int(get_pref("lumen_red_pct", 0)), 5,
                key=f"{organ}_{nonce}_lumen",
            )

        st.markdown("**Penetrating**")
        p1, p2, p3 = st.columns(3)
        with p1:
            f["has_pen"] = st.checkbox(
                "Pen. present",
                get_pref("has_pen", False),
                key=f"{organ}_{nonce}_has_pen",
            )
        with p2:
            f["deep_ulc"] = st.checkbox(
                "Deep / transmural ulcer.",
                get_pref("deep_ulc", False),
                key=f"{organ}_{nonce}_deep",
            )
        with p3:
            f["phlegmon"] = st.checkbox(
                "Phlegmon / mass",
                get_pref("phlegmon", False),
                key=f"{organ}_{nonce}_phleg",
            )
            f["any_fistula"] = st.checkbox(
                "Any fistula",
                get_pref("any_fistula", False),
                key=f"{organ}_{nonce}_fist",
            )

        # placeholders for anus-only fields
        f.setdefault("anus_str_grade", 0)
        f.setdefault("anus_pen_mri_grade", 0)

    elif organ == "anus":
        # stricturing
        str_options = [
            "0: None",
            "1: Mild stricture",
            "2: Frank, passable",
            "3: Frank, non-passable",
        ]
        str_default = int(get_pref("anus_str_grade", 0))
        sel_str = st.selectbox(
            "Anus — stricturing (clinical)",
            str_options,
            index=str_default,
            key=f"anus_{nonce}_str_g",
        )
        f["anus_str_grade"] = int(sel_str.split(":")[0])
        f["has_str"] = f["anus_str_grade"] > 0

        # penetrating
        pen_options = [
            "0: None",
            "1: Simple fistula",
            "2: Branching/multiple / abscess >1 cm",
            "3: Extensive / horseshoe / above levator",
        ]
        pen_default = int(get_pref("anus_pen_mri_grade", 0))
        sel_pen = st.selectbox(
            "Anus — penetrating (MRI)",
            pen_options,
            index=pen_default,
            key=f"anus_{nonce}_pen_mri_g",
        )
        f["anus_pen_mri_grade"] = int(sel_pen.split(":")[0])

        # safe defaults
        defaults = {
            "thick_mm": 0.0,
            "seg_enh": False,
            "mural_strat": False,
            "stricture": False,
            "has_pd": False,
            "lumen_red_pct": 0,
            "has_pen": f["anus_pen_mri_grade"] > 0,
            "deep_ulc": False,
            "phlegmon": False,
            "any_fistula": False,
        }
        for k, v in defaults.items():
            f.setdefault(k, v)

    return f

# GRADERS
def grade_upper_str(f: Dict[str, Any]) -> int:
    if f.get("has_pd"):
        return 3
    if (f.get("thick_mm", 0) >= 3) or f.get("mural_strat"):
        return 2
    if (0 < f.get("thick_mm", 0) < 3) or f.get("seg_enh"):
        return 1
    return 0

def grade_sb_str(f: Dict[str, Any]) -> int:
    if f.get("has_pd"):
        return 3
    if (f.get("thick_mm", 0) >= 3) or f.get("mural_strat"):
        return 2
    if (0 < f.get("thick_mm", 0) < 3) or f.get("seg_enh"):
        return 1
    return 0

def grade_col_str(f: Dict[str, Any]) -> int:
    if f.get("has_pd") or (f.get("lumen_red_pct", 0) > 50):
        return 3
    if (f.get("thick_mm", 0) >= 3) or f.get("mural_strat") or (0 < f.get("lumen_red_pct", 0) <= 50):
        return 2
    if (0 < f.get("thick_mm", 0) < 3) or f.get("seg_enh"):
        return 1
    return 0

def grade_upper_pen(f: Dict[str, Any]) -> int:
    if not f.get("has_pen"):
        return 0
    if f.get("phlegmon") or f.get("any_fistula"):
        return 3
    if f.get("deep_ulc"):
        return 2
    return 0

def grade_sb_pen(f: Dict[str, Any]) -> int:
    if not f.get("has_pen"):
        return 0
    if f.get("phlegmon") or f.get("any_fistula"):
        return 3
    if f.get("deep_ulc"):
        return 2
    return 0

def grade_col_pen(f: Dict[str, Any]) -> int:
    if not f.get("has_pen"):
        return 0
    if f.get("phlegmon") or f.get("any_fistula"):
        return 3
    if f.get("deep_ulc"):
        return 2
    return 0

def grade_anus_str(f: Dict[str, Any]) -> int:
    g = int(f.get("anus_str_grade", 0))
    return g if g in (1, 2, 3) else 0

def grade_anus_pen(f: Dict[str, Any]) -> int:
    g = int(f.get("anus_pen_mri_grade", 0))
    return g if g in (1, 2, 3) else 0

GRADERS = {
    "upper":        {"str": grade_upper_str, "pen": grade_upper_pen},
    "small_bowel":  {"str": grade_sb_str,    "pen": grade_sb_pen},
    "colon_rectum": {"str": grade_col_str,   "pen": grade_col_pen},
    "anus":         {"str": grade_anus_str,  "pen": grade_anus_pen},
}

# SCORING
def score_segment(organ: str, f: Dict[str, Any]) -> float:
    pts = 0.0
    # surgery as percentage → 100% = 10
    resect_pct = max(0, min(100, int(f.get("resect_pct", 0))))
    pts += resect_pct / 10.0
    # lesions
    s = GRADERS[organ]["str"](f)
    p = GRADERS[organ]["pen"](f)
    if s > 0:
        pts += COEFS[organ].get(("str", s), 0.0)
    if p > 0:
        pts += COEFS[organ].get(("pen", p), 0.0)
    return pts

def organ_li(organ: str, rows: List[Dict[str, Any]]) -> float:
    total = sum(score_segment(organ, r) for r in rows)
    denom = DENOM.get(organ, len(SEGMENTS[organ]))
    return round(total / denom, 2) if denom else 0.0

def global_li(organ_scores: Dict[str, float]) -> float:
    return round(sum(GLOBAL_WEIGHTS[o] * v for o, v in organ_scores.items()), 2)

# SIDEBAR: ID
st.sidebar.header("Patient ID")
patient_id = st.sidebar.text_input("Enter unique ID", value="").strip()

# FORM: ADD / EDIT
with st.expander("Add / Edit segment (worst lesion)"):
    pref = st.session_state.form_prefill
    organs_list = list(SEGMENTS.keys())
    org_default = organs_list.index(pref["organ"]) if pref and pref.get("organ") in organs_list else 1
    organ = st.selectbox(
        "Organ",
        organs_list,
        index=org_default,
        key="ui_organ",
        on_change=lambda: _reset_organ_widget_state(True),
    )

    seg_list = SEGMENTS[organ]
    seg_default = seg_list.index(pref["segment"]) if pref and pref.get("organ") == organ and pref.get("segment") in seg_list else 0
    segment = st.selectbox(
        "Segment",
        seg_list,
        index=seg_default,
        key="ui_segment",
        on_change=_reset_organ_widget_state,
    )

    resect_default = int(pref.get("resect_pct", 0)) if pref else 0
    resect_pct = st.number_input(
        "Percent resected (0–100)",
        0,
        100,
        resect_default,
        5,
        key=f"ui_resect_pct_{st.session_state.form_nonce}",
    )

    feat = organ_inputs(organ, pref, st.session_state.form_nonce)

    # auto-infer flags so users don't forget to tick
    if organ != "anus":
        feat["has_str"] = feat.get("has_str", False) or any([
            feat.get("thick_mm", 0) > 0,
            feat.get("seg_enh", False),
            feat.get("mural_strat", False),
            feat.get("stricture", False),
        ])
        feat["has_pen"] = feat.get("has_pen", False) or any([
            feat.get("deep_ulc", False),
            feat.get("phlegmon", False),
            feat.get("any_fistula", False),
        ])

    label = "✅ Update" if pref else "➕ Add"
    if st.button(label):
        # upsert: only one row per (organ, segment)
        st.session_state.rows = [
            r for r in st.session_state.rows
            if not (r["organ"] == organ and r["segment"] == segment)
        ]
        st.session_state.rows.append({
            **feat,
            "organ": organ,
            "segment": segment,
            "resect_pct": resect_pct,
        })
        st.session_state.form_prefill = None
        st.success("Saved.")

# TABLE + CONTROLS
st.subheader("Entered segments")
if not st.session_state.rows:
    st.info("No segments yet.")
else:
    df = pd.DataFrame(st.session_state.rows)
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.markdown("**Edit or delete a segment:**")
    for i, r in enumerate(st.session_state.rows):
        cols = st.columns([3, 3, 1, 1])
        cols[0].write(f"**{r['organ']}** — {r['segment']}")
        cols[1].write(f"Resected: {r.get('resect_pct', 0)}%")
        if cols[2].button("✏️ Edit", key=f"edit_{i}"):
            st.session_state.form_prefill = r
            st.rerun()
        if cols[3].button("🗑️ Delete", key=f"del_{i}"):
            st.session_state.rows.pop(i)
            st.rerun()

    # SCORES
    organ_scores: Dict[str, float] = {}
    for org in SEGMENTS.keys():
        rows = [r for r in st.session_state.rows if r["organ"] == org]
        organ_scores[org] = organ_li(org, rows)

    st.subheader("Organ scores (normalised)")
    st.table(pd.DataFrame([{"Organ": k, "Organ LI": v} for k, v in organ_scores.items()]))

    st.subheader("Global Lémann Index")
    gli = global_li(organ_scores)
    st.metric("Global LI", gli)

st.markdown("### Save this result")
if st.button("💾 Save current result"):
    if not patient_id:
        st.error("Please enter a Patient ID in the sidebar first.")
    elif patient_id.lower() in st.session_state.id_set:
        st.error("This Patient ID already exists. Use a new ID.")
    else:
        st.session_state.results.append({
            "ID": patient_id,
            "LI_upper": organ_scores.get("upper", 0.0),
            "LI_small_bowel": organ_scores.get("small_bowel", 0.0),
            "LI_colon_rectum": organ_scores.get("colon_rectum", 0.0),
            "LI_anus": organ_scores.get("anus", 0.0),
            "Global_LI": gli,
        })
        st.session_state.id_set.add(patient_id.lower())
        st.success(f"Saved results for ID: {patient_id}")

    # SAVE RESULT
st.subheader("Saved results")
from pathlib import Path
CSV_PATH = Path("lemann_index_results.csv")

if st.session_state.results:
    res_df = pd.DataFrame(st.session_state.results)
    st.dataframe(res_df, use_container_width=True, hide_index=True)

    # Download directly (client-side)
    csv_bytes = res_df.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Download CSV", data=csv_bytes, file_name="lemann_index_results.csv", mime="text/csv")

    # Server-side save / delete controls
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("💾 Save CSV (server)"):
            res_df.to_csv(CSV_PATH, index=False, encoding="utf-8")
            st.success(f"Saved to {CSV_PATH.resolve()}")
    with c2:
        if st.button("🗑️ Delete CSV (server)"):
            if CSV_PATH.exists():
                CSV_PATH.unlink()
                st.success("Server CSV deleted.")
            else:
                st.info("No server CSV to delete.")
    with c3:
        if st.button("🧽 Clear saved results (memory)"):
            st.session_state.results = []
            st.session_state.id_set = set()
            st.success("Cleared in-memory saved results.")

    # Show server file status
    if CSV_PATH.exists():
        st.caption(f"Server CSV: ✅ {CSV_PATH.resolve()}")
    else:
        st.caption("Server CSV: ❌ none")
else:
    st.info("No saved results yet.")


# REFERENCES
with st.expander("Reference (original index)"):
    st.markdown(
        """
Pariente B, *et al.* **Validation and Update of the Lémann Index to Measure Cumulative Structural Bowel Damage in Crohn’s Disease.** *Gastroenterology.* 2021;161(3):853-864.e13. doi:10.1053/j.gastro.2021.05.049.

Pariente B, *et al.* **Development of the Lémann Index to Assess Digestive Tract Damage in Patients With Crohn’s Disease.** *Gastroenterology.* 2015;148(1):52-63.e3. doi:10.1053/j.gastro.2014.09.015.
"""
    )
