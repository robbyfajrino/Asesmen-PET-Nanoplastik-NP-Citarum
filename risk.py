"""Risk assessment: SSD / HC5, PNEC and PEC-PNEC risk quotients (synthetic)."""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from model import DATA_STATUS, RNG

# taxa-level chronic NOEC / EC10 values for PET nanoplastics used to build the SSD.
# 'source_status' makes explicit which rows are dummy and which are anchored to a
# literature range for the polymer class (still re-generated, never quoted as a fact).
SSD_TAXA = [
    ("Chlorella vulgaris", "green algae", "growth rate EC10", 320.0, "literature-anchored range"),
    ("Scenedesmus obliquus", "green algae", "growth rate EC10", 410.0, "literature-anchored range"),
    ("Daphnia magna", "cladoceran", "reproduction NOEC", 95.0, "literature-anchored range"),
    ("Ceriodaphnia dubia", "cladoceran", "reproduction NOEC", 130.0, "dummy"),
    ("Macrobrachium rosenbergii", "decapod crustacean", "growth EC10 (this study)", 165.0, "dummy - this study"),
    ("Moina macrocopa", "cladoceran", "survival NOEC", 220.0, "dummy"),
    ("Brachionus plicatilis", "rotifer", "population growth EC10", 480.0, "dummy"),
    ("Chironomus riparius", "insect larva", "emergence NOEC", 760.0, "dummy"),
    ("Oreochromis niloticus", "fish", "growth EC10 (this study)", 640.0, "dummy - this study"),
    ("Danio rerio", "fish", "behaviour EC10", 540.0, "literature-anchored range"),
    ("Lemna minor", "macrophyte", "frond number EC10", 1250.0, "dummy"),
    ("Corbicula fluminea", "bivalve", "filtration EC10", 380.0, "dummy"),
]

ASSESSMENT_FACTOR = 3.0  # applied to HC5 (SSD available, >=8 taxa, >=8 species groups)
RQ_CLASSES = [(0.1, "negligible"), (1.0, "low"), (10.0, "moderate"), (float("inf"), "high")]


def ssd_df() -> pd.DataFrame:
    df = pd.DataFrame(SSD_TAXA, columns=["species", "taxonomic_group", "endpoint",
                                         "noec_or_ec10_ug_L", "source_status"])
    df = df.sort_values("noec_or_ec10_ug_L").reset_index(drop=True)
    n = len(df)
    df["rank"] = df.index + 1
    df["cumulative_probability"] = ((df["rank"] - 0.5) / n).round(4)
    df["log10_conc"] = np.log10(df.noec_or_ec10_ug_L).round(4)
    df["data_status"] = DATA_STATUS
    return df


def ssd_fit(ssd: pd.DataFrame) -> dict:
    x = np.log10(ssd.noec_or_ec10_ug_L.to_numpy(float))
    mu, sigma = float(x.mean()), float(x.std(ddof=1))
    hc5 = float(10 ** (mu + stats.norm.ppf(0.05) * sigma))
    hc50 = float(10 ** mu)
    boot = [10 ** (np.mean(s := RNG.choice(x, len(x), replace=True))
                   + stats.norm.ppf(0.05) * np.std(s, ddof=1)) for _ in range(2000)]
    return dict(n_species=len(x), mu_log10=round(mu, 4), sigma_log10=round(sigma, 4),
                hc5_ug_L=round(hc5, 2), hc50_ug_L=round(hc50, 2),
                hc5_ci95_low_ug_L=round(float(np.percentile(boot, 2.5)), 2),
                hc5_ci95_high_ug_L=round(float(np.percentile(boot, 97.5)), 2),
                assessment_factor=ASSESSMENT_FACTOR,
                pnec_ug_L=round(hc5 / ASSESSMENT_FACTOR, 3),
                distribution="log-normal SSD, HC5 at 5th percentile",
                data_status=DATA_STATUS)


def _rq_class(rq: float) -> str:
    for thr, label in RQ_CLASSES:
        if rq < thr:
            return label
    return "high"


def risk_df(exposure: pd.DataFrame, fit: dict) -> pd.DataFrame:
    pnec = fit["pnec_ug_L"]
    g = (exposure.groupby(["station_code", "station_name", "regency", "river_km", "season"])
         .agg(pec_mean_ug_L=("pet_np_water_ug_L", "mean"),
              pec_max_ug_L=("pet_np_water_ug_L", "max"),
              pec_sd_ug_L=("pet_np_water_ug_L", "std"))
         .reset_index())
    g["pec_95th_ug_L"] = (g.pec_mean_ug_L + 1.645 * g.pec_sd_ug_L).round(2)
    g["hc5_ug_L"] = fit["hc5_ug_L"]
    g["assessment_factor"] = ASSESSMENT_FACTOR
    g["pnec_ug_L"] = pnec
    g["rq_mean"] = (g.pec_mean_ug_L / pnec).round(3)
    g["rq_reasonable_worst_case"] = (g.pec_95th_ug_L / pnec).round(3)
    g["risk_class_mean"] = g.rq_mean.map(_rq_class)
    g["risk_class_rwc"] = g.rq_reasonable_worst_case.map(_rq_class)
    for c in ["pec_mean_ug_L", "pec_max_ug_L", "pec_sd_ug_L"]:
        g[c] = g[c].round(2)
    g["data_status"] = DATA_STATUS
    return g
