"""Charts for the integrated assessment. Forest & Moss palette."""

from __future__ import annotations

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats

from model import CLAY, FOREST, INK, MOSS, SAND, SEASONS

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.edgecolor": "#999999",
                     "axes.labelcolor": INK, "text.color": INK, "figure.dpi": 160,
                     "axes.grid": True, "grid.color": "#E6E6E6", "grid.linewidth": 0.6})

SEASON_COLORS = {0: SAND, 1: MOSS, 2: FOREST}


def _save(fig, outdir, name):
    os.makedirs(outdir, exist_ok=True)
    p = os.path.join(outdir, name)
    fig.savefig(p, bbox_inches="tight")
    plt.close(fig)
    return p


def fig_longitudinal(exposure, outdir):
    fig, ax = plt.subplots(figsize=(7.6, 3.6))
    g = exposure.groupby(["season", "station_code", "river_km"])["pet_np_water_ug_L"].mean().reset_index()
    for i, season in enumerate(SEASONS):
        s = g[g.season == season].sort_values("river_km")
        ax.plot(s.river_km, s.pet_np_water_ug_L, "o-", lw=1.8, ms=5,
                color=SEASON_COLORS[i % 3], label=season)
    st = g.drop_duplicates("station_code").sort_values("river_km")
    top = ax.secondary_xaxis("top")
    top.set_xticks(st.river_km.tolist())
    top.set_xticklabels(st.station_code.tolist(), fontsize=7.5, color="#6F6F6F")
    top.tick_params(length=2)
    ax.set_xlabel("river distance from Situ Cisanti (km)")
    ax.set_ylabel("PET nanoplastics in water (µg/L)")
    ax.set_title("Longitudinal PET nanoplastic profile, Citarum basin (synthetic data)",
                 color=FOREST, fontsize=10)
    ax.legend(frameon=False, fontsize=8)
    ax.set_ylim(bottom=0)
    return _save(fig, outdir, "fig01_longitudinal_exposure.png")


def fig_province(prov, outdir):
    fig, ax = plt.subplots(figsize=(7.0, 3.4))
    p = prov.sort_values("exposure_pressure_score")
    colors = [CLAY if x == "Jawa Barat" else MOSS for x in p.province]
    ax.barh(p.province, p.exposure_pressure_score, color=colors, edgecolor=FOREST, height=0.62)
    for y, v in zip(p.province, p.exposure_pressure_score):
        ax.annotate(f"{v:.0f}", (v, y), xytext=(4, 0), textcoords="offset points",
                    va="center", fontsize=8, color=FOREST)
    ax.set_xlabel("composite PET exposure-pressure score (0-100)")
    ax.set_title("Why West Java: province-level PET pressure ranking", color=FOREST, fontsize=10)
    ax.set_xlim(0, max(p.exposure_pressure_score) * 1.12)
    ax.grid(axis="y", visible=False)
    return _save(fig, outdir, "fig02_province_ranking.png")


def fig_dose_response(dr, ecx, outdir):
    fig, axes = plt.subplots(1, 2, figsize=(7.8, 3.4), sharey=True)
    for ax, (sp, g) in zip(axes, dr.groupby("species")):
        m = g.groupby("dose_pet_np_ug_L")[["mortality_96h_pct", "growth_inhibition_pct",
                                           "third_endpoint_pct"]].agg(["mean", "std"])
        x = np.maximum(m.index.to_numpy(float), 10.0)
        labels = ["mortality 96 h", "growth inhibition", g.third_endpoint_name.iloc[0].replace("_", " ")]
        for (col, c, lab) in zip(["mortality_96h_pct", "growth_inhibition_pct", "third_endpoint_pct"],
                                 [FOREST, MOSS, CLAY], labels):
            ax.errorbar(x, m[(col, "mean")], yerr=m[(col, "std")], fmt="o-", color=c,
                        lw=1.6, ms=4, capsize=2.5, label=lab)
        lc = ecx[(ecx.species == sp) & (ecx.metric == "LC50")].value_ug_L.iloc[0]
        ax.axvline(lc, color="#8A7A5E", ls="--", lw=1.1)
        ax.annotate(f"LC50 {lc:,.0f} µg/L", (lc, 96), fontsize=7, color="#6F5F45",
                    ha="right", rotation=90, va="top")
        ax.set_xscale("log")
        ax.set_xlabel("PET nanoplastics (µg/L, log scale)")
        ax.set_title(sp, color=FOREST, fontsize=9.5, style="italic")
    axes[0].set_ylabel("response (%)")
    axes[0].set_ylim(-6, 104)
    axes[0].legend(frameon=False, fontsize=7.5, loc="upper left")
    fig.suptitle("Dose-response, 96 h semi-static exposure", color=FOREST, fontsize=10, y=1.02)
    fig.tight_layout()
    return _save(fig, outdir, "fig03_dose_response.png")


def fig_biomarkers(bio, outdir):
    piv = (bio.groupby(["species", "biomarker", "dose_pet_np_ug_L"])["fold_change_vs_control"]
           .mean().reset_index())
    species = list(piv.species.unique())
    fig, axes = plt.subplots(1, 2, figsize=(8.0, 3.2))
    for ax, sp in zip(axes, species):
        s = piv[piv.species == sp].pivot(index="biomarker", columns="dose_pet_np_ug_L",
                                         values="fold_change_vs_control")
        im = ax.imshow(s.to_numpy(), cmap="BrBG_r", vmin=0.4, vmax=2.4, aspect="auto")
        ax.set_xticks(range(len(s.columns)))
        ax.set_xticklabels([f"{c:,.0f}" for c in s.columns], fontsize=7.5, rotation=45)
        ax.set_yticks(range(len(s.index)))
        ax.set_yticklabels([i.split("_")[0] for i in s.index], fontsize=8)
        for i in range(len(s.index)):
            for j in range(len(s.columns)):
                ax.text(j, i, f"{s.iat[i, j]:.2f}", ha="center", va="center", fontsize=6.5,
                        color="white" if abs(s.iat[i, j] - 1) > 0.55 else INK)
        ax.set_title(sp, fontsize=9, color=FOREST, style="italic")
        ax.set_xlabel("dose (µg/L)")
        ax.grid(False)
    fig.colorbar(im, ax=axes, shrink=0.85, label="fold change vs control")
    fig.suptitle("Biomarker response (fold change vs control)", color=FOREST, fontsize=10, y=1.04)
    return _save(fig, outdir, "fig04_biomarkers_heatmap.png")


def fig_behavior(bsum, outdir):
    fig, axes = plt.subplots(1, 3, figsize=(8.2, 3.1))
    sp = "Macrobrachium rosenbergii"
    traits = ["swimming_speed_mm_s", "thigmotaxis_pct_time_wall_zone", "feeding_rate_items_per_min"]
    doses = sorted(bsum.dose_pet_np_ug_L.unique())
    cmap = plt.get_cmap("YlGn")
    for ax, tr in zip(axes, traits):
        s = bsum[(bsum.species == sp) & (bsum.trait == tr)]
        for k, d in enumerate(doses):
            ss = s[s.dose_pet_np_ug_L == d].sort_values("time_h")
            ax.plot(ss.time_h, ss.mean_value, "o-", ms=3, lw=1.5,
                    color=cmap(0.25 + 0.72 * k / (len(doses) - 1)),
                    label=f"{d:,.0f}")
        ax.set_title(tr.replace("_", " "), fontsize=8.5, color=FOREST)
        ax.set_xlabel("exposure time (h)")
    axes[0].set_ylabel("mean value")
    axes[2].legend(frameon=False, fontsize=6.5, title="µg/L", title_fontsize=7,
                   loc="upper right", ncol=2)
    fig.suptitle(f"Behavioural dynamics, {sp} (0-96 h)", color=FOREST, fontsize=10, y=1.03)
    fig.tight_layout()
    return _save(fig, outdir, "fig05_behaviour_timeseries.png")


def fig_bioaccumulation(bioacc, outdir):
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(8.0, 3.2))
    g = bioacc.groupby(["species", "tissue"])["tissue_conc_ug_per_g_ww"].mean().unstack()
    tissues = list(g.columns)
    colors = [FOREST, MOSS, SAND, CLAY, "#4F7A8C"][:len(tissues)]
    bottom = np.zeros(len(g))
    x = np.arange(len(g))
    for t, c in zip(tissues, colors):
        v = g[t].fillna(0).to_numpy()
        a1.bar(x, v, bottom=bottom, color=c, edgecolor="white", lw=0.4, label=t, width=0.55)
        bottom += v
    a1.set_xticks(x)
    a1.set_xticklabels([s.split()[0] for s in g.index], fontsize=8)
    a1.set_ylabel("tissue concentration (µg/g ww)")
    a1.set_title("Body burden by tissue (mean over doses)", fontsize=9, color=FOREST)
    a1.legend(frameon=False, fontsize=7, ncol=2)
    b = bioacc.groupby(["species", "tissue"])["bcf_L_per_kg"].mean().unstack()
    w = 0.36
    for i, sp in enumerate(b.index):
        a2.bar(np.arange(len(b.columns)) + (i - 0.5) * w, b.loc[sp], width=w,
               color=[FOREST, MOSS][i], edgecolor="white", label=sp.split()[0])
    a2.set_xticks(np.arange(len(b.columns)))
    a2.set_xticklabels(b.columns, fontsize=8, rotation=15)
    a2.set_ylabel("BCF (L/kg)")
    a2.set_title("Bioconcentration factor", fontsize=9, color=FOREST)
    a2.legend(frameon=False, fontsize=7.5)
    fig.tight_layout()
    return _save(fig, outdir, "fig06_bioaccumulation.png")


def fig_ssd(ssd, fit, risk, outdir):
    fig, ax = plt.subplots(figsize=(7.4, 3.7))
    x = np.log10(ssd.noec_or_ec10_ug_L.to_numpy(float))
    ax.scatter(10 ** x, ssd.cumulative_probability, color=FOREST, zorder=3, s=26)
    for _, r in ssd.iterrows():
        ax.annotate(r.species, (r.noec_or_ec10_ug_L, r.cumulative_probability),
                    xytext=(6, -3), textcoords="offset points", fontsize=6.2, color="#555555")
    xs = np.logspace(np.log10(30), np.log10(4000), 300)
    ax.plot(xs, stats.norm.cdf(np.log10(xs), fit["mu_log10"], fit["sigma_log10"]),
            color=MOSS, lw=1.8, label="log-normal SSD")
    ax.axvline(fit["hc5_ug_L"], color=CLAY, ls="--", lw=1.3,
               label=f"HC5 = {fit['hc5_ug_L']:.0f} µg/L")
    ax.axvspan(fit["hc5_ci95_low_ug_L"], fit["hc5_ci95_high_ug_L"], color=CLAY, alpha=0.12,
               label="HC5 95 % CI")
    ax.axvline(fit["pnec_ug_L"], color=FOREST, ls=":", lw=1.3,
               label=f"PNEC = {fit['pnec_ug_L']:.0f} µg/L (AF {fit['assessment_factor']:.0f})")
    pec = risk.pec_mean_ug_L.max()
    ax.axvline(pec, color="#8A7A5E", lw=1.2, label=f"max station PEC = {pec:.0f} µg/L")
    ax.set_xscale("log")
    ax.set_xlabel("PET nanoplastics, chronic NOEC / EC10 (µg/L, log scale)")
    ax.set_ylabel("cumulative fraction of species affected")
    ax.set_title("Species sensitivity distribution and PNEC derivation", color=FOREST, fontsize=10)
    ax.legend(frameon=False, fontsize=7.2, loc="upper left")
    ax.set_ylim(0, 1.02)
    return _save(fig, outdir, "fig07_ssd_hc5.png")


RISK_COLORS = {"negligible": SAND, "low": MOSS, "moderate": "#C9A227", "high": CLAY}


def fig_risk(risk, outdir):
    fig, ax = plt.subplots(figsize=(7.8, 3.6))
    seasons = [x for x in SEASONS if x in set(risk.season)]
    stations = (risk.groupby("station_code")["river_km"].first().sort_values().index.tolist())
    w = 0.26
    for i, season in enumerate(seasons):
        s = risk[risk.season == season].set_index("station_code").loc[stations]
        ax.bar(np.arange(len(stations)) + (i - 1) * w, s.rq_reasonable_worst_case, width=w,
               color=[RISK_COLORS[c] for c in s.risk_class_rwc], edgecolor=FOREST, lw=0.5)
        for j, v in enumerate(s.rq_reasonable_worst_case):
            ax.annotate(f"{v:.1f}", (j + (i - 1) * w, v), xytext=(0, 2),
                        textcoords="offset points", ha="center", fontsize=5.8, color=INK)
    ax.axhline(1.0, color=CLAY, ls="--", lw=1.2)
    ax.annotate("RQ = 1 (risk threshold)", (len(stations) - 0.6, 1.05), fontsize=7, color=CLAY,
                ha="right")
    ax.set_xticks(np.arange(len(stations)))
    ax.set_xticklabels(stations)
    ax.set_ylabel("risk quotient PEC$_{95}$ / PNEC")
    ax.set_ylim(0, risk.rq_reasonable_worst_case.max() * 1.25)
    ax.set_title("Risk characterisation per station (bars grouped "
                 + " / ".join(s.split(" ")[0] for s in seasons)
                 + "; colour = risk class)", color=FOREST, fontsize=9.5)
    handles = [plt.Rectangle((0, 0), 1, 1, color=c, ec=FOREST) for c in RISK_COLORS.values()]
    ax.legend(handles, list(RISK_COLORS), frameon=False, fontsize=7.5, ncol=4, loc="upper left")
    return _save(fig, outdir, "fig08_risk_quotient.png")


def fig_eia(riam, leopold, outdir):
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(8.4, 4.0),
                                 gridspec_kw={"width_ratios": [1.05, 1.0]})
    r = riam.sort_values("ES_environmental_score")
    colors = [CLAY if v < 0 else MOSS for v in r.ES_environmental_score]
    a1.barh(range(len(r)), r.ES_environmental_score, color=colors, edgecolor=FOREST, height=0.66)
    a1.set_yticks(range(len(r)))
    a1.set_yticklabels([c[:38] for c in r.environmental_component], fontsize=7)
    for i, (v, cls) in enumerate(zip(r.ES_environmental_score, r.riam_range_class)):
        a1.annotate(f"{v} ({cls})", (v, i), xytext=(-4 if v < 0 else 4, 0),
                    textcoords="offset points", ha="right" if v < 0 else "left",
                    va="center", fontsize=6.5, color=INK)
    a1.axvline(0, color="#888888", lw=0.9)
    a1.set_xlabel("RIAM environmental score ES = (A1×A2)(B1+B2+B3)")
    a1.set_title("RIAM significance", fontsize=9.5, color=FOREST)
    a1.grid(axis="y", visible=False)
    a1.set_xlim(min(r.ES_environmental_score) * 1.35, max(r.ES_environmental_score) * 2.2)

    piv = leopold.pivot_table(index="environmental_component", columns="activity",
                              values="interaction_score", aggfunc="sum").fillna(0)
    im = a2.imshow(piv.to_numpy(), cmap="RdYlGn", vmin=-25, vmax=25, aspect="auto")
    a2.set_xticks(range(len(piv.columns)))
    a2.set_xticklabels([c.split("(")[0][:26] for c in piv.columns], fontsize=6, rotation=60,
                       ha="right")
    a2.set_yticks(range(len(piv.index)))
    a2.set_yticklabels([i[:30] for i in piv.index], fontsize=6.5)
    for i in range(piv.shape[0]):
        for j in range(piv.shape[1]):
            v = piv.iat[i, j]
            if v:
                a2.text(j, i, int(v), ha="center", va="center", fontsize=5.6, color=INK)
    a2.set_title("Leopold matrix (magnitude × importance)", fontsize=9.5, color=FOREST)
    a2.grid(False)
    fig.colorbar(im, ax=a2, shrink=0.8, label="interaction score")
    fig.tight_layout()
    return _save(fig, outdir, "fig09_eia_riam_leopold.png")


def fig_lca(impacts, eol, outdir):
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(8.2, 3.4))
    imp = impacts.sort_values("gwp100_kgCO2e", ascending=True)
    a1.barh(range(len(imp)), imp.gwp100_kgCO2e, color=MOSS, edgecolor=FOREST, height=0.66)
    a1.set_yticks(range(len(imp)))
    a1.set_yticklabels([s[:30] for s in imp.life_cycle_stage], fontsize=7)
    for i, (v, s) in enumerate(zip(imp.gwp100_kgCO2e, imp.share_of_gwp_pct)):
        a1.annotate(f"{v:.2f} ({s:.0f} %)", (v, i), xytext=(4, 0), textcoords="offset points",
                    va="center", fontsize=6.5, color=FOREST)
    a1.set_xlabel("kg CO$_2$e / kg PET resin")
    a1.set_title(f"GWP100 by stage (total {impacts.gwp100_kgCO2e.sum():.2f})",
                 fontsize=9.5, color=FOREST)
    a1.set_xlim(0, imp.gwp100_kgCO2e.max() * 1.42)
    a1.grid(axis="y", visible=False)

    x = np.arange(len(eol))
    a2.bar(x, eol.gwp100_kgCO2e_per_kg, color=FOREST, edgecolor=FOREST, width=0.5,
           label="GWP100 (kg CO$_2$e/kg)")
    a2.set_ylabel("kg CO$_2$e / kg PET", color=FOREST)
    a2.set_xticks(x)
    a2.set_xticklabels([n.split(" ")[0] for n in eol.eol_scenario], fontsize=8)
    a3 = a2.twinx()
    a3.plot(x, eol.pet_np_release_mg_per_kg_resin, "o--", color=CLAY, lw=1.6, ms=6,
            label="PET NP release (mg/kg)")
    a3.set_ylabel("PET nanoplastic release (mg / kg resin)", color=CLAY)
    a3.grid(False)
    for xi, v in zip(x, eol.pet_np_release_mg_per_kg_resin):
        a3.annotate(f"{v:.1f}", (xi, v), xytext=(0, 6), textcoords="offset points",
                    ha="center", fontsize=7, color=CLAY)
    a2.set_title("End-of-life scenarios: climate vs nanoplastic release", fontsize=9.5,
                 color=FOREST)
    h1, l1 = a2.get_legend_handles_labels()
    h2, l2 = a3.get_legend_handles_labels()
    a2.legend(h1 + h2, l1 + l2, frameon=False, fontsize=7, loc="upper center",
              bbox_to_anchor=(0.5, -0.16), ncol=2)
    a2.set_ylim(0, eol.gwp100_kgCO2e_per_kg.max() * 1.18)
    a3.set_ylim(0, eol.pet_np_release_mg_per_kg_resin.max() * 1.25)
    fig.tight_layout()
    return _save(fig, outdir, "fig10_lca_pet.png")


def fig_scorecard(score, outdir):
    labels = ["ecotoxicity\npotential", "risk\n(RQ)", "EIA\nsignificance", "exposure\nlevel"]
    cols = ["ecotox_index_0_100", "risk_index_0_100", "eia_index_0_100", "exposure_index_0_100"]
    ang = np.linspace(0, 2 * np.pi, len(cols), endpoint=False).tolist()
    ang += ang[:1]
    fig, axes = plt.subplots(2, 4, figsize=(8.6, 4.6), subplot_kw={"polar": True})
    cmap = plt.get_cmap("YlOrBr")
    for ax, (_, r) in zip(axes.ravel(), score.sort_values("river_km").iterrows()):
        vals = [r[c] for c in cols]
        vals += vals[:1]
        col = cmap(0.25 + 0.6 * r.integrated_index_0_100 / 100)
        ax.plot(ang, vals, color=FOREST, lw=1.4)
        ax.fill(ang, vals, color=col, alpha=0.75)
        ax.set_xticks(ang[:-1])
        ax.set_xticklabels(labels, fontsize=5.8)
        ax.set_yticks([25, 50, 75, 100])
        ax.set_yticklabels(["25", "50", "75", ""], fontsize=5)
        ax.set_ylim(0, 100)
        ax.set_title(f"{r.station_code} · {r.integrated_index_0_100:.0f}\n{r.priority_class}",
                     fontsize=7.5, color=FOREST, pad=9)
        ax.grid(color="#DDDDDD", lw=0.5)
    fig.suptitle("Integrated scorecard per station (0-100, higher = more concern)",
                 color=FOREST, fontsize=10, y=1.0)
    fig.tight_layout()
    return _save(fig, outdir, "fig11_integrated_scorecard.png")
