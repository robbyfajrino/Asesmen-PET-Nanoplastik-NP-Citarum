"""Dose-response, biomarkers and bioaccumulation for PET nanoplastics (synthetic)."""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.optimize import curve_fit

from model import DATA_STATUS, DOSES_UGL, REPLICATES, RNG, SPECIES


def _loglogistic(c, ec50, slope, top=100.0):
    c = np.asarray(c, dtype=float)
    out = np.zeros_like(c)
    m = c > 0
    out[m] = top / (1.0 + (ec50 / c[m]) ** slope)
    return out


def dose_response_df() -> pd.DataFrame:
    rows = []
    for sp, meta in SPECIES.items():
        for dose in DOSES_UGL:
            mort = _loglogistic(dose, meta["lc50_ugL"], meta["slope"])
            grow = _loglogistic(dose, meta["ec50_growth_ugL"], 1.05, top=78.0)
            third = _loglogistic(dose, meta["ec50_growth_ugL"] * 1.4,
                                 0.95, top=64.0 if meta["group"] == "small crustacean" else 55.0)
            for rep in range(1, REPLICATES + 1):
                rows.append(dict(
                    species=sp, species_code=meta["code"], group=meta["group"],
                    life_stage=meta["stage"], dose_pet_np_ug_L=dose, replicate=rep,
                    n_organisms=20,
                    mortality_96h_pct=round(float(np.clip(mort + RNG.normal(0, 2.6 + 0.05 * mort), 0, 100)), 2),
                    growth_inhibition_pct=round(float(np.clip(grow + RNG.normal(0, 2.4), -4, 95)), 2),
                    third_endpoint_name=meta["endpoints"][2],
                    third_endpoint_pct=round(float(np.clip(third + RNG.normal(0, 2.8), -3, 95)), 2),
                    exposure_h=96, medium="dechlorinated tap water, semi-static renewal 24 h",
                    data_status=DATA_STATUS))
    return pd.DataFrame(rows)


def fit_effect_concentrations(dr: pd.DataFrame) -> pd.DataFrame:
    """Python-side reference fit; the workbook repeats this with Excel formulas."""
    out = []
    for sp, g in dr.groupby("species"):
        for endpoint in ["mortality_96h_pct", "growth_inhibition_pct", "third_endpoint_pct"]:
            m = g.groupby("dose_pet_np_ug_L")[endpoint].mean()
            x = m.index.to_numpy(float)
            y = m.to_numpy(float)
            top = max(float(y.max()) * 1.05, 5.0)
            try:
                p, cov = curve_fit(lambda c, e, s: _loglogistic(c, e, s, top), x[1:], y[1:],
                                   p0=[max(x[1:].mean(), 1.0), 1.2], maxfev=20000)
                se = float(np.sqrt(np.diag(cov))[0])
            except Exception:
                p, se = [np.nan, np.nan], np.nan
            name = ("LC50" if endpoint == "mortality_96h_pct" else "EC50")
            out.append(dict(species=sp, endpoint=endpoint,
                            endpoint_label=g["third_endpoint_name"].iloc[0] if endpoint == "third_endpoint_pct" else endpoint,
                            metric=name, value_ug_L=round(float(p[0]), 1),
                            ci95_low_ug_L=round(float(p[0] - 1.96 * se), 1) if se == se else np.nan,
                            ci95_high_ug_L=round(float(p[0] + 1.96 * se), 1) if se == se else np.nan,
                            hill_slope=round(float(p[1]), 3), asymptote_pct=round(top, 1),
                            noec_ug_L=50.0 if name == "EC50" else 250.0,
                            data_status=DATA_STATUS))
    return pd.DataFrame(out)


BIOMARKERS = {
    "SOD_U_per_mg_protein": (18.5, 1.55, "oxidative defence, biphasic"),
    "CAT_U_per_mg_protein": (24.0, 1.42, "oxidative defence"),
    "GST_nmol_per_min_mg": (32.0, 1.38, "phase II detoxification"),
    "MDA_nmol_per_mg_protein": (1.20, 2.35, "lipid peroxidation, monotonic increase"),
    "AChE_nmol_per_min_mg": (46.0, 0.52, "neurotoxicity, inhibition"),
}


def biomarkers_df() -> pd.DataFrame:
    rows = []
    for sp, meta in SPECIES.items():
        scale = 1.0 if meta["group"] == "small crustacean" else 0.62
        for dose in DOSES_UGL:
            f = 0.0 if dose == 0 else np.log10(dose / 25.0) / np.log10(20000 / 25.0)
            for marker, (ctrl, maxfold, note) in BIOMARKERS.items():
                if marker == "AChE_nmol_per_min_mg":
                    fold = 1 + (maxfold - 1) * f * scale
                elif marker == "MDA_nmol_per_mg_protein":
                    fold = 1 + (maxfold - 1) * (f ** 1.15) * scale
                else:  # biphasic: induction then exhaustion
                    fold = 1 + (maxfold - 1) * np.sin(np.pi * min(f * 1.25, 1.0)) * scale
                for rep in range(1, 4):
                    rows.append(dict(
                        species=sp, species_code=meta["code"], dose_pet_np_ug_L=dose,
                        replicate=rep, biomarker=marker,
                        value=round(float(ctrl * fold * RNG.lognormal(0, 0.07)), 3),
                        control_mean=ctrl, fold_change_vs_control=round(float(fold), 3),
                        tissue="hepatopancreas" if meta["group"] == "small crustacean" else "liver",
                        interpretation=note, data_status=DATA_STATUS))
    return pd.DataFrame(rows)


def bioaccumulation_df() -> pd.DataFrame:
    aff = {"gill": 1.00, "gut": 1.35, "hepatopancreas": 0.72, "liver": 0.64, "muscle": 0.11}
    rows = []
    for sp, meta in SPECIES.items():
        k = 0.0135 if meta["group"] == "small crustacean" else 0.0068
        for dose in DOSES_UGL[1:]:
            for tissue in meta["tissues"]:
                for rep in range(1, 4):
                    conc = dose * k * aff[tissue] * RNG.lognormal(0, 0.12)
                    rows.append(dict(
                        species=sp, species_code=meta["code"], tissue=tissue,
                        dose_pet_np_ug_L=dose, replicate=rep, exposure_h=96,
                        tissue_conc_ug_per_g_ww=round(float(conc), 4),
                        bcf_L_per_kg=round(float(conc * 1000 / dose), 2),
                        depuration_48h_removal_pct=round(float(np.clip(RNG.normal(
                            62 if tissue == "gut" else 31, 6), 5, 95)), 1),
                        data_status=DATA_STATUS))
    return pd.DataFrame(rows)
