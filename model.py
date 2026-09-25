"""Shared parameters, stations, species and dose design for the PET nanoplastics
integrated assessment (Citarum river basin, West Java).

ALL DATA IN THIS PROJECT IS SYNTHETIC (dummy). Values are calibrated to sit inside
plausible literature ranges but they are NOT field measurements.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

SEED = 20260904
RNG = np.random.default_rng(SEED)

DATA_STATUS = "synthetic (dummy) - generated, not measured"
VERSION = "1.0"
POLYMER = "PET (polyethylene terephthalate) nanoplastics, d50 ~ 120 nm"
FUNCTIONAL_UNIT_LCA = "1 kg PET bottle-grade resin, cradle-to-grave"

# ----------------------------------------------------------------------------- stations
# river-km measured from Situ Cisanti (source) downstream to Muara Gembong (mouth)
STATIONS = [
    # code, name, regency, river_km, pressure_type, population_density_p_km2
    ("ST1", "Situ Cisanti (headwater)", "Kab. Bandung", 0, "reference / upstream forest", 420),
    ("ST2", "Majalaya (textile cluster)", "Kab. Bandung", 32, "textile wastewater", 3900),
    ("ST3", "Dayeuhkolot", "Kab. Bandung", 54, "urban domestic + industry", 8600),
    ("ST4", "Nanjung - Bandung Barat", "Kab. Bandung Barat", 71, "mixed urban runoff", 5100),
    ("ST5", "Saguling reservoir inlet", "Kab. Bandung Barat", 95, "reservoir sedimentation", 1400),
    ("ST6", "Cirata reservoir", "Kab. Purwakarta", 128, "reservoir + aquaculture cages", 1100),
    ("ST7", "Jatiluhur outlet", "Kab. Purwakarta", 158, "reservoir outlet / raw water intake", 1600),
    ("ST8", "Muara Gembong (estuary)", "Kab. Bekasi", 269, "estuary, landfill leachate + tidal", 2300),
]

SEASONS = {
    # name: (exposure multiplier, TSS multiplier, note)
    "Kemarau (dry, Jul-Sep)": (0.72, 0.55, "low flow, less dilution but less land wash-off"),
    "Transisi (Apr-Jun/Oct)": (1.00, 1.00, "reference season for PEC"),
    "Hujan (wet, Dec-Feb)": (1.46, 2.10, "runoff-driven mobilisation of PET debris"),
}

# base PET nanoplastic concentration in water, ug/L (transition season)
BASE_PET_UGL = {"ST1": 0.9, "ST2": 34.0, "ST3": 47.5, "ST4": 29.8,
                "ST5": 18.4, "ST6": 12.7, "ST7": 9.1, "ST8": 22.6}

# ----------------------------------------------------------------------------- species
SPECIES = {
    "Macrobrachium rosenbergii": dict(
        code="MRO", group="small crustacean", stage="post-larvae PL-25",
        lc50_ugL=1850.0, slope=1.35, ec50_growth_ugL=610.0, sensitivity_rank=1,
        endpoints=["mortality_96h_pct", "growth_inhibition_pct", "moulting_delay_pct"],
        tissues=["gill", "hepatopancreas", "gut", "muscle"],
    ),
    "Oreochromis niloticus": dict(
        code="ONI", group="fish", stage="juvenile 2.1 +/- 0.3 g",
        lc50_ugL=6400.0, slope=1.18, ec50_growth_ugL=1950.0, sensitivity_rank=2,
        endpoints=["mortality_96h_pct", "growth_inhibition_pct", "gill_histopathology_index"],
        tissues=["gill", "liver", "gut", "muscle"],
    ),
}

DOSES_UGL = [0.0, 50.0, 250.0, 1000.0, 5000.0, 20000.0]
REPLICATES = 4
BEHAVIOR_HOURS = [0, 6, 12, 24, 48, 72, 96]

# ----------------------------------------------------------------------------- provinces
PROVINCE_RANKING = [
    # province, waste_generation_kt_yr, plastic_share_pct, PET_share_of_plastic_pct,
    # textile+bottling plants, pop_density, river_plastic_flux_index
    ("Jawa Barat", 6520, 17.8, 22.5, 1180, 1450, 100.0),
    ("DKI Jakarta", 3180, 19.4, 24.1, 410, 15900, 88.5),
    ("Jawa Timur", 5480, 16.2, 20.3, 860, 850, 76.4),
    ("Jawa Tengah", 4720, 15.6, 19.8, 640, 1060, 68.1),
    ("Banten", 2140, 17.1, 21.6, 520, 1320, 61.7),
    ("Sumatera Utara", 2280, 14.3, 18.4, 210, 200, 44.2),
    ("Bali", 940, 18.2, 21.0, 130, 750, 39.8),
]

# ----------------------------------------------------------------------------- palette
FOREST, MOSS, CLAY, SAND, INK, PAPER = (
    "#1F3B2C", "#6B8F63", "#B4653A", "#D9CDB4", "#22201C", "#FBFAF6")


def stations_df() -> pd.DataFrame:
    df = pd.DataFrame(STATIONS, columns=[
        "station_code", "station_name", "regency", "river_km", "pressure_type",
        "population_density_p_km2"])
    df["latitude_dd"] = [-7.204, -7.048, -6.983, -6.928, -6.912, -6.703, -6.535, -5.977]
    df["longitude_dd"] = [107.663, 107.760, 107.618, 107.550, 107.380, 107.310, 107.386, 107.014]
    df["water_body"] = ["lake/spring", "river", "river", "river", "reservoir inlet",
                        "reservoir", "reservoir outlet", "estuary"]
    df["data_status"] = DATA_STATUS
    return df


def province_df() -> pd.DataFrame:
    df = pd.DataFrame(PROVINCE_RANKING, columns=[
        "province", "msw_generation_kt_yr", "plastic_share_pct", "pet_share_of_plastic_pct",
        "textile_and_bottling_plants_n", "population_density_p_km2", "river_plastic_flux_index"])
    df["pet_in_waste_kt_yr"] = (df.msw_generation_kt_yr * df.plastic_share_pct / 100
                                * df.pet_share_of_plastic_pct / 100).round(2)
    df["exposure_pressure_score"] = (
        0.40 * df.river_plastic_flux_index
        + 0.30 * 100 * df.pet_in_waste_kt_yr / df.pet_in_waste_kt_yr.max()
        + 0.20 * 100 * df.textile_and_bottling_plants_n / df.textile_and_bottling_plants_n.max()
        + 0.10 * 100 * df.population_density_p_km2 / df.population_density_p_km2.max()
    ).round(1)
    df = df.sort_values("exposure_pressure_score", ascending=False).reset_index(drop=True)
    df.insert(0, "rank", df.index + 1)
    df["data_status"] = DATA_STATUS
    return df


def exposure_df() -> pd.DataFrame:
    rows = []
    for code, name, regency, km, pressure, _dens in STATIONS:
        base = BASE_PET_UGL[code]
        for season, (mult, tss_mult, note) in SEASONS.items():
            for rep in range(1, 4):
                c = base * mult * RNG.lognormal(0, 0.16)
                d50 = float(np.clip(RNG.normal(118 if code != "ST1" else 96, 14), 60, 190))
                tss = float(np.clip(RNG.normal(48, 9) * tss_mult * (0.35 if code == "ST1" else 1), 3, 400))
                rows.append(dict(
                    station_code=code, station_name=name, regency=regency, river_km=km,
                    season=season, replicate=rep,
                    pet_np_water_ug_L=round(c, 2),
                    pet_np_particles_per_L=int(c * 1.9e6 * RNG.lognormal(0, 0.1)),
                    d50_nm=round(d50, 1),
                    zeta_potential_mV=round(RNG.normal(-24.5, 3.1), 1),
                    tss_mg_L=round(tss, 1),
                    pet_np_sediment_mg_kg=round(c * RNG.uniform(0.9, 1.6), 2),
                    dissolved_organic_carbon_mg_L=round(np.clip(RNG.normal(6.4, 1.5), 1, 20), 2),
                    water_temp_C=round(RNG.normal(27.8, 1.1), 1),
                    pH=round(RNG.normal(7.3, 0.3), 2),
                    season_note=note, data_status=DATA_STATUS))
    return pd.DataFrame(rows)
