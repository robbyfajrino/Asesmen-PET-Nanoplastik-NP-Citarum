"""One command builds the whole integrated assessment.

    python pet-nano-citarum/run.py [outdir]

Writes CSV exports, PNG figures and the XLSX workbook. All data is synthetic.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd

import behavior
import ecotox
import eia
import figures
import lca
import model
import risk
from build_workbook import build
from integrate import parameters_table, scorecard

OUT = sys.argv[1] if len(sys.argv) > 1 else "/mnt/documents/PET-Nano-Citarum"


def main():
    csvdir = os.path.join(OUT, "csv")
    figdir = os.path.join(OUT, "figures")
    os.makedirs(csvdir, exist_ok=True)

    stations = model.stations_df()
    prov = model.province_df()
    exposure = model.exposure_df()
    dr = ecotox.dose_response_df()
    ecx = ecotox.fit_effect_concentrations(dr)
    bio = ecotox.biomarkers_df()
    bioacc = ecotox.bioaccumulation_df()
    bdf = behavior.behavior_df()
    bsum = behavior.behavior_summary(bdf)
    ssd = risk.ssd_df()
    fit = risk.ssd_fit(ssd)
    rsk = risk.risk_df(exposure, fit)
    leopold = eia.leopold_df()
    riam = eia.riam_df()
    inv = lca.inventory_df()
    imp = lca.impacts_df(inv)
    eol = lca.eol_df(inv)
    score = scorecard(stations, rsk, ecx)
    params = parameters_table(fit)
    ssd_fit_df = pd.DataFrame([fit])

    tables = {
        "01_province_ranking": prov,
        "02_stations": stations,
        "03_exposure_water_sediment": exposure,
        "04_ecotox_dose_response": dr,
        "05_effect_concentrations": ecx,
        "06_biomarkers": bio,
        "07_bioaccumulation": bioacc,
        "08_behaviour_raw": bdf,
        "09_behaviour_summary": bsum,
        "10_ssd_species": ssd,
        "11_ssd_fit_pnec": ssd_fit_df,
        "12_risk_pec_pnec": rsk,
        "13_eia_leopold_matrix": leopold,
        "14_eia_riam": riam,
        "15_lca_inventory": inv,
        "16_lca_impacts_by_stage": imp,
        "17_lca_eol_scenarios": eol,
        "18_integrated_scorecard": score,
        "19_parameters": params,
    }
    for name, df in tables.items():
        df.to_csv(os.path.join(csvdir, f"{name}.csv"), index=False)

    figs = [
        (figures.fig_longitudinal(exposure, figdir),
         "Figure 1 - Longitudinal PET nanoplastic profile along the Citarum"),
        (figures.fig_province(prov, figdir),
         "Figure 2 - Province-level PET pressure ranking (why West Java)"),
        (figures.fig_dose_response(dr, ecx, figdir),
         "Figure 3 - Dose-response curves and LC50/EC50, both species"),
        (figures.fig_biomarkers(bio, figdir),
         "Figure 4 - Biomarker fold-change heatmap"),
        (figures.fig_behavior(bsum, figdir),
         "Figure 5 - Behavioural dynamics over 96 h"),
        (figures.fig_bioaccumulation(bioacc, figdir),
         "Figure 6 - Tissue burden and bioconcentration factors"),
        (figures.fig_ssd(ssd, fit, rsk, figdir),
         "Figure 7 - Species sensitivity distribution, HC5 and PNEC"),
        (figures.fig_risk(rsk, figdir),
         "Figure 8 - Risk quotients per station and season"),
        (figures.fig_eia(riam, leopold, figdir),
         "Figure 9 - EIA: RIAM significance and Leopold matrix"),
        (figures.fig_lca(imp, eol, figdir),
         "Figure 10 - Screening LCA of PET and end-of-life scenarios"),
        (figures.fig_scorecard(score, figdir),
         "Figure 11 - Integrated scorecard per station"),
    ]

    xlsx = os.path.join(OUT, "PET-Nanoplastics-Citarum-Integrated-Assessment.xlsx")
    build(xlsx, dict(stations=stations, prov=prov, exposure=exposure, dr=dr, ecx=ecx,
                     bio=bio, bioacc=bioacc, bsum=bsum, ssd=ssd, ssd_fit=fit, risk=rsk,
                     leopold=leopold, riam=riam, inv=inv, imp=imp, eol=eol, score=score,
                     params=params, figures=figs))

    print("workbook:", xlsx)
    print("csv     :", csvdir, f"({len(tables)} files)")
    print("figures :", figdir, f"({len(figs)} files)")
    print("\nPNEC (µg/L):", fit["pnec_ug_L"], "| HC5:", fit["hc5_ug_L"])
    print(ecx[["species", "metric", "endpoint", "value_ug_L"]].to_string(index=False))
    print(score[["station_code", "rq_worst_case", "integrated_index_0_100",
                 "priority_class"]].to_string(index=False))
    return xlsx


if __name__ == "__main__":
    main()
