"""Integrated scorecard: combines ecotoxicity, risk and EIA significance per station."""

from __future__ import annotations

import numpy as np
import pandas as pd

from eia import COMPONENTS, riam_df
from model import DATA_STATUS

# weight of each module in the integrated index (editable in the workbook)
WEIGHTS = dict(ecotox=0.30, risk=0.35, eia=0.20, exposure=0.15)

# which pressure types carry which share of the (basin-wide) RIAM burden
EIA_PROFILE = {
    "reference / upstream forest": 0.20,
    "textile wastewater": 1.00,
    "urban domestic + industry": 0.92,
    "mixed urban runoff": 0.78,
    "reservoir sedimentation": 0.55,
    "reservoir + aquaculture cages": 0.66,
    "reservoir outlet / raw water intake": 0.52,
    "estuary, landfill leachate + tidal": 0.84,
}


def _norm(s: pd.Series) -> pd.Series:
    lo, hi = float(s.min()), float(s.max())
    if hi - lo < 1e-12:
        return pd.Series(np.zeros(len(s)), index=s.index)
    return 100 * (s - lo) / (hi - lo)


def scorecard(stations: pd.DataFrame, risk: pd.DataFrame, ecx: pd.DataFrame) -> pd.DataFrame:
    riam = riam_df()
    eia_pressure = float(-riam.ES_environmental_score.clip(upper=0).sum())
    ref_season = [s for s in risk.season.unique() if "Transisi" in s][0]

    r = (risk.groupby("station_code")
         .agg(rq_mean_all_seasons=("rq_mean", "mean"),
              rq_worst_case=("rq_reasonable_worst_case", "max"),
              pec_mean_ug_L=("pec_mean_ug_L", "mean"),
              pec_wet_ug_L=("pec_mean_ug_L", "max")).reset_index())
    ref = risk[risk.season == ref_season][["station_code", "pec_mean_ug_L"]].rename(
        columns={"pec_mean_ug_L": "pec_transition_ug_L"})
    df = stations.merge(r, on="station_code").merge(ref, on="station_code")

    # ecotoxicity potential: fraction of the most sensitive EC50 already reached in the field
    ec50_min = float(ecx[ecx.metric == "EC50"].value_ug_L.min())
    df["toxic_unit_most_sensitive_endpoint"] = (df.pec_wet_ug_L / ec50_min).round(4)
    df["eia_pressure_weight"] = df.pressure_type.map(EIA_PROFILE)
    df["eia_weighted_negative_ES"] = (df.eia_pressure_weight * eia_pressure).round(1)

    df["ecotox_index_0_100"] = _norm(np.log10(df.toxic_unit_most_sensitive_endpoint)).round(1)
    df["risk_index_0_100"] = _norm(np.log10(df.rq_worst_case)).round(1)
    df["eia_index_0_100"] = _norm(df.eia_weighted_negative_ES).round(1)
    df["exposure_index_0_100"] = _norm(np.log10(df.pec_mean_ug_L)).round(1)

    df["integrated_index_0_100"] = (
        WEIGHTS["ecotox"] * df.ecotox_index_0_100
        + WEIGHTS["risk"] * df.risk_index_0_100
        + WEIGHTS["eia"] * df.eia_index_0_100
        + WEIGHTS["exposure"] * df.exposure_index_0_100).round(1)
    df["priority_class"] = pd.cut(df.integrated_index_0_100, [-0.01, 25, 50, 75, 100],
                                  labels=["low", "moderate", "high", "very high"]).astype(str)
    df["w_ecotox"] = WEIGHTS["ecotox"]
    df["w_risk"] = WEIGHTS["risk"]
    df["w_eia"] = WEIGHTS["eia"]
    df["w_exposure"] = WEIGHTS["exposure"]
    df["data_status"] = DATA_STATUS
    cols = ["station_code", "station_name", "regency", "river_km", "pressure_type",
            "pec_mean_ug_L", "pec_wet_ug_L", "pec_transition_ug_L", "rq_mean_all_seasons",
            "rq_worst_case", "toxic_unit_most_sensitive_endpoint", "eia_pressure_weight",
            "eia_weighted_negative_ES", "ecotox_index_0_100", "risk_index_0_100",
            "eia_index_0_100", "exposure_index_0_100", "w_ecotox", "w_risk", "w_eia",
            "w_exposure", "integrated_index_0_100", "priority_class", "data_status"]
    return df[cols]


def parameters_table(fit: dict) -> pd.DataFrame:
    from lca import EOL_SCENARIOS
    from model import BASE_PET_UGL, DOSES_UGL, SEASONS, SPECIES
    rows = [
        ("study_area", "Citarum river basin, Jawa Barat, Indonesia", "-", "case study boundary",
         "assumption", "chosen from the province ranking sheet"),
        ("polymer", "PET nanoplastics, d50 ~120 nm, spherical, PS excluded", "nm",
         "test material", "assumption", "matches the scope requested (PET only)"),
        ("n_stations", len(BASE_PET_UGL), "count", "sampling design", "dummy", "8 stations, source to estuary"),
        ("seasons", "; ".join(SEASONS), "-", "sampling design", "dummy", "3 hydrological seasons"),
        ("dose_series", "; ".join(f"{d:,.0f}" for d in DOSES_UGL), "µg/L", "ecotox design",
         "dummy", "log-spaced, OECD-style geometric series"),
        ("exposure_duration", 96, "h", "ecotox design", "assumption", "acute, semi-static, 24 h renewal"),
        ("replicates", 4, "count", "ecotox design", "assumption", "20 organisms per replicate"),
    ]
    for sp, m in SPECIES.items():
        rows.append((f"lc50_{m['code']}", m["lc50_ugL"], "µg/L", f"{sp} nominal LC50",
                     "dummy", "generating parameter of the synthetic dose-response"))
        rows.append((f"ec50_growth_{m['code']}", m["ec50_growth_ugL"], "µg/L",
                     f"{sp} nominal growth EC50", "dummy", "generating parameter"))
    rows += [
        ("ssd_n_species", fit["n_species"], "count", "SSD", "mixed", "8 taxonomic groups"),
        ("hc5", fit["hc5_ug_L"], "µg/L", "SSD 5th percentile", "derived", "log-normal fit"),
        ("assessment_factor", fit["assessment_factor"], "-", "PNEC derivation", "assumption",
         "AF 3 because an SSD with >=8 species is available"),
        ("pnec", fit["pnec_ug_L"], "µg/L", "PNEC", "derived", "HC5 / AF"),
        ("rq_threshold", 1.0, "-", "risk classification", "convention", "ECHA R.10 style banding"),
        ("grid_emission_factor", 0.79, "kg CO2e/kWh", "LCA background", "literature-anchored",
         "Jamali grid, replace with the licensed dataset value"),
        ("lca_functional_unit", "1 kg PET bottle-grade resin, cradle-to-grave", "-", "LCA scope",
         "assumption", "screening level, proxy factors only"),
        ("eol_scenarios", "; ".join(s[0] for s in EOL_SCENARIOS), "-", "LCA scenarios", "dummy",
         "collection and leakage variants"),
        ("integrated_weights", "ecotox 0.30 / risk 0.35 / EIA 0.20 / exposure 0.15", "-",
         "scorecard", "assumption", "editable in sheet 14"),
    ]
    df = pd.DataFrame(rows, columns=["parameter", "value", "unit", "role", "status", "note"])
    df["data_status"] = DATA_STATUS
    return df
