"""Screening LCA of PET, cradle-to-grave, 1 kg bottle-grade resin (synthetic proxies).

Impact factors are proxy values in the order of magnitude reported for PET in public
LCI databases; they are placeholders for a licensed ecoinvent/ELCD dataset.
"""

from __future__ import annotations

import pandas as pd

from model import DATA_STATUS, FUNCTIONAL_UNIT_LCA

# stage, flow, amount, unit, gwp kgCO2e, CED MJ, water m3, note
INVENTORY = [
    ("A1 Raw material supply", "Crude oil / naphtha input", 1.42, "kg", 0.52, 24.0, 0.0021, "upstream extraction & refining"),
    ("A1 Raw material supply", "Purified terephthalic acid (PTA)", 0.86, "kg", 1.21, 21.5, 0.0104, "proxy factor"),
    ("A1 Raw material supply", "Monoethylene glycol (MEG)", 0.34, "kg", 0.58, 9.8, 0.0061, "proxy factor"),
    ("A2 Transport to converter", "Road freight, 18 t truck", 0.42, "t.km", 0.05, 0.7, 0.0002, "Cilegon-Bekasi average"),
    ("A3 Polymerisation & resin", "Electricity, Jamali grid", 1.05, "kWh", 0.83, 8.6, 0.0038, "0.79 kg CO2e/kWh grid factor"),
    ("A3 Polymerisation & resin", "Natural gas, process heat", 6.20, "MJ", 0.39, 6.8, 0.0004, "steam and drying"),
    ("A4 Preform & bottle moulding", "Electricity, Jamali grid", 0.62, "kWh", 0.49, 5.1, 0.0022, "injection + stretch blow"),
    ("A5 Filling & distribution", "Road freight, distribution", 0.85, "t.km", 0.10, 1.4, 0.0004, "regional distribution"),
    ("B1 Use phase", "Refrigeration & retail (allocated)", 0.18, "kWh", 0.14, 1.5, 0.0006, "allocated share"),
    ("C1 Collection & sorting", "Diesel, collection fleet", 0.031, "kg", 0.10, 1.4, 0.0001, "62 % collection rate assumed"),
    ("C2 Mechanical recycling", "Electricity + washing water", 0.28, "kWh", 0.22, 2.3, 0.0180, "applies to recycled fraction"),
    ("C3 Landfill / open dump", "PET to landfill or open dump", 0.30, "kg", 0.02, 0.1, 0.0000, "inert, slow fragmentation"),
    ("C4 Open burning", "PET burned in the open", 0.08, "kg", 0.19, 0.0, 0.0000, "uncontrolled, PM and CO co-emitted"),
    ("C5 Leakage to river", "PET debris to Citarum", 0.045, "kg", 0.00, 0.0, 0.0000, "source term for nanoplastic release"),
]

# end-of-life scenarios: name, recycling, landfill, open burning, river leakage (fractions),
# nanoplastic release factor mg PET NP per kg PET reaching the river, description
EOL_SCENARIOS = [
    ("S0 Business as usual (2024 baseline)", 0.13, 0.66, 0.16, 0.050,
     920.0, "current Jawa Barat collection and treatment mix"),
    ("S1 Improved collection (Citarum Harum target)", 0.22, 0.68, 0.08, 0.020,
     380.0, "collection to 80 %, open burning halved"),
    ("S2 EPR + bottle-to-bottle recycling", 0.45, 0.50, 0.04, 0.010,
     190.0, "deposit-return, formalised waste pickers"),
    ("S3 Full containment (upper bound)", 0.60, 0.38, 0.01, 0.002,
     40.0, "aspirational, near-zero leakage"),
]


def inventory_df() -> pd.DataFrame:
    df = pd.DataFrame(INVENTORY, columns=[
        "life_cycle_stage", "flow", "amount", "unit", "gwp100_kgCO2e",
        "ced_MJ", "water_consumption_m3", "note"])
    df["functional_unit"] = FUNCTIONAL_UNIT_LCA
    df["data_status"] = DATA_STATUS
    return df


def impacts_df(inv: pd.DataFrame) -> pd.DataFrame:
    g = (inv.groupby("life_cycle_stage")[["gwp100_kgCO2e", "ced_MJ", "water_consumption_m3"]]
         .sum().reset_index())
    total = g.gwp100_kgCO2e.sum()
    g["share_of_gwp_pct"] = (100 * g.gwp100_kgCO2e / total).round(2)
    g["gwp100_kgCO2e"] = g.gwp100_kgCO2e.round(4)
    g["ced_MJ"] = g.ced_MJ.round(3)
    g["water_consumption_m3"] = g.water_consumption_m3.round(5)
    g["data_status"] = DATA_STATUS
    return g


def eol_df(inv: pd.DataFrame) -> pd.DataFrame:
    base_gwp = float(inv.gwp100_kgCO2e.sum())
    rows = []
    for name, rec, lf, burn, leak, npf, desc in EOL_SCENARIOS:
        # credit for recycled resin substituting virgin PET (avoided burden, cut-off style memo)
        credit = rec * 1.85
        burn_gwp = burn * 2.35
        gwp = base_gwp - 0.19 - 0.02 + burn_gwp + lf * 0.06 - credit
        rows.append(dict(
            eol_scenario=name, recycling_frac=rec, landfill_frac=lf,
            open_burning_frac=burn, river_leakage_frac=leak,
            gwp100_kgCO2e_per_kg=round(gwp, 3),
            recycling_credit_kgCO2e=round(-credit, 3),
            open_burning_kgCO2e=round(burn_gwp, 3),
            pet_to_river_g_per_kg=round(leak * 1000, 1),
            np_release_factor_mg_per_kg_leaked=npf,
            pet_np_release_mg_per_kg_resin=round(leak * npf, 2),
            description=desc, functional_unit=FUNCTIONAL_UNIT_LCA, data_status=DATA_STATUS))
    return pd.DataFrame(rows)
