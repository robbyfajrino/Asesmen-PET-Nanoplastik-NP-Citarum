"""Behavioural dynamics time-series under PET nanoplastic exposure (synthetic)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from model import BEHAVIOR_HOURS, DATA_STATUS, DOSES_UGL, RNG, SPECIES

TRAITS = {
    "swimming_speed_mm_s": (dict(MRO=14.2, ONI=58.0), -0.46, "locomotor depression"),
    "distance_moved_cm_per_10min": (dict(MRO=520.0, ONI=2100.0), -0.42, "activity"),
    "thigmotaxis_pct_time_wall_zone": (dict(MRO=32.0, ONI=27.5), +0.95, "anxiety-like response"),
    "freezing_time_pct": (dict(MRO=8.5, ONI=5.2), +1.60, "startle / freezing"),
    "feeding_rate_items_per_min": (dict(MRO=3.4, ONI=6.8), -0.55, "foraging efficiency"),
    "aggression_events_per_10min": (dict(MRO=1.9, ONI=2.6), -0.35, "social interaction"),
}


def behavior_df() -> pd.DataFrame:
    rows = []
    for sp, meta in SPECIES.items():
        code = meta["code"]
        sens = 1.0 if meta["group"] == "small crustacean" else 0.72
        for dose in DOSES_UGL:
            d = 0.0 if dose == 0 else np.log10(dose / 25.0) / np.log10(20000 / 25.0)
            for h in BEHAVIOR_HOURS:
                t = h / 96.0
                for rep in range(1, 4):
                    for trait, (ctrl_map, resp, note) in TRAITS.items():
                        ctrl = ctrl_map[code]
                        effect = resp * d * sens * (1 - np.exp(-3.1 * t))
                        val = ctrl * (1 + effect) * RNG.lognormal(0, 0.06)
                        rows.append(dict(
                            species=sp, species_code=code, dose_pet_np_ug_L=dose,
                            time_h=h, replicate=rep, trait=trait,
                            value=round(float(max(val, 0)), 3),
                            control_baseline=ctrl,
                            pct_change_vs_control=round(float(100 * (val / ctrl - 1)), 2),
                            tracking_method="open-field video tracking, 10 min trial, 25 fps",
                            interpretation=note, data_status=DATA_STATUS))
    return pd.DataFrame(rows)


def behavior_summary(bdf: pd.DataFrame) -> pd.DataFrame:
    g = (bdf.groupby(["species", "trait", "dose_pet_np_ug_L", "time_h"])["value"]
         .agg(["mean", "std"]).reset_index()
         .rename(columns={"mean": "mean_value", "std": "sd_value"}))
    g["mean_value"] = g.mean_value.round(3)
    g["sd_value"] = g.sd_value.round(3)
    return g
