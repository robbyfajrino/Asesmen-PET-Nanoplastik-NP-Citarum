"""EIA modules: Leopold interaction matrix and RIAM significance scoring (synthetic)."""

from __future__ import annotations

import pandas as pd

from model import DATA_STATUS

ACTIVITIES = [
    "PET resin production & preform moulding (Bekasi-Karawang industrial belt)",
    "Bottling, filling and distribution",
    "Textile / polyester fibre wet processing (Majalaya cluster)",
    "Uncollected post-consumer PET entering the river",
    "Open dumping and open burning of PET waste",
    "Mechanical recycling (washing, grinding, pelletising)",
    "Reservoir operation & aquaculture cages (Cirata)",
    "Raw water abstraction & drinking water treatment (Jatiluhur)",
]

COMPONENTS = [
    ("Physico-chemical", "Surface water quality (PET NP, TSS, DOC)"),
    ("Physico-chemical", "Sediment quality"),
    ("Physico-chemical", "Air quality (combustion by-products)"),
    ("Biological", "Small crustaceans (Macrobrachium)"),
    ("Biological", "Fish community & aquaculture stock (Oreochromis)"),
    ("Biological", "Benthic macroinvertebrates"),
    ("Socio-economic", "Fisher & fish-farmer livelihood"),
    ("Socio-economic", "Drinking water supply & public health"),
    ("Socio-economic", "Informal waste-picker occupational exposure"),
]

# magnitude (-5..+5) and importance (1..5) per activity x component; 0 = no interaction
MAGNITUDE = {
    0: [-3, -2, -2, -2, -2, -1, -1, -1, -1],
    1: [-2, -1, -1, -1, -1, -1, 0, -1, 0],
    2: [-5, -4, -1, -4, -4, -4, -3, -3, -2],
    3: [-5, -5, 0, -5, -4, -4, -3, -4, -2],
    4: [-3, -3, -5, -3, -2, -2, -2, -3, -4],
    5: [-3, -2, -2, -2, -2, -2, 2, -1, -3],
    6: [-2, -3, 0, -3, -3, -3, -2, -2, 0],
    7: [-1, 0, 0, -1, -1, -1, -1, 3, 0],
}
IMPORTANCE = {
    0: [3, 3, 3, 3, 3, 2, 2, 3, 2],
    1: [2, 2, 2, 2, 2, 2, 1, 2, 1],
    2: [5, 4, 2, 5, 5, 4, 4, 4, 3],
    3: [5, 5, 1, 5, 5, 5, 4, 5, 3],
    4: [3, 3, 5, 3, 3, 3, 3, 4, 5],
    5: [3, 3, 2, 3, 3, 3, 3, 2, 4],
    6: [3, 3, 1, 4, 5, 4, 4, 3, 1],
    7: [2, 1, 1, 2, 2, 2, 2, 5, 1],
}


def leopold_df() -> pd.DataFrame:
    rows = []
    for i, act in enumerate(ACTIVITIES):
        for j, (cat, comp) in enumerate(COMPONENTS):
            m, imp = MAGNITUDE[i][j], IMPORTANCE[i][j]
            if m == 0:
                continue
            rows.append(dict(activity=act, component_category=cat, environmental_component=comp,
                             magnitude_minus5_to_plus5=m, importance_1_to_5=imp,
                             interaction_score=m * imp,
                             direction="adverse" if m < 0 else "beneficial",
                             data_status=DATA_STATUS))
    return pd.DataFrame(rows)


# RIAM: ES = (A1 x A2) x (B1 + B2 + B3)
RIAM_ROWS = [
    # component, A1 importance(0-4), A2 magnitude(-3..3), B1 permanence(1-3),
    # B2 reversibility(1-3), B3 cumulative(1-3), mitigation
    ("Surface water quality (PET NP)", 4, -3, 3, 2, 3, "Interception booms + Majalaya WWTP nano-filtration retrofit; EPR on PET bottles"),
    ("Sediment quality", 3, -2, 3, 3, 3, "Sediment monitoring at Saguling/Cirata; dredging spoil management"),
    ("Small crustaceans (Macrobrachium)", 3, -3, 2, 2, 3, "Seasonal restocking ban during wet-season peaks; hatchery water screening"),
    ("Fish community & aquaculture stock", 4, -2, 2, 2, 3, "Cage siting away from tributary inflows; feed & tissue surveillance"),
    ("Benthic macroinvertebrates", 2, -2, 2, 2, 2, "Habitat protection in upstream reaches"),
    ("Air quality (open burning)", 3, -3, 1, 2, 2, "Close open dumps; formalise collection in Kab. Bandung"),
    ("Fisher & fish-farmer livelihood", 3, -2, 2, 2, 2, "Alternative livelihood + compensation scheme"),
    ("Drinking water supply & public health", 4, -2, 2, 2, 3, "Nano-filtration step + PET NP in raw-water monitoring protocol"),
    ("Waste-picker occupational exposure", 2, -3, 2, 2, 2, "PPE, formal cooperatives, health screening"),
    ("Reservoir operation (Cirata)", 2, -1, 2, 3, 2, "Trash rack maintenance, drawdown-timed clean-ups"),
    ("Recycling sector value creation", 3, 2, 2, 3, 2, "Support bottle-to-bottle recycling capacity"),
]

RIAM_BANDS = [(-108, -72, "-E", "major negative"), (-71, -36, "-D", "significant negative"),
              (-35, -19, "-C", "moderate negative"), (-18, -10, "-B", "negative"),
              (-9, -1, "-A", "slight negative"), (0, 0, "N", "no change"),
              (1, 9, "A", "slight positive"), (10, 18, "B", "positive"),
              (19, 35, "C", "moderate positive"), (36, 71, "D", "significant positive"),
              (72, 108, "E", "major positive")]


def _band(es: int):
    for lo, hi, cls, label in RIAM_BANDS:
        if lo <= es <= hi:
            return cls, label
    return "?", "out of range"


def riam_df() -> pd.DataFrame:
    rows = []
    for comp, a1, a2, b1, b2, b3 in [(r[0], *r[1:6]) for r in RIAM_ROWS]:
        es = (a1 * a2) * (b1 + b2 + b3)
        cls, label = _band(es)
        mit = dict((r[0], r[6]) for r in RIAM_ROWS)[comp]
        rows.append(dict(environmental_component=comp,
                         A1_importance_of_condition=a1, A2_magnitude_of_change=a2,
                         B1_permanence=b1, B2_reversibility=b2, B3_cumulative=b3,
                         AT_A1xA2=a1 * a2, BT_B1plusB2plusB3=b1 + b2 + b3,
                         ES_environmental_score=es, riam_range_class=cls,
                         significance=label, mitigation_measure=mit,
                         data_status=DATA_STATUS))
    return pd.DataFrame(rows).sort_values("ES_environmental_score").reset_index(drop=True)
