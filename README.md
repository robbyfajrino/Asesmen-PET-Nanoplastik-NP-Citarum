# PET nanoplastics in the Citarum basin — integrated assessment (synthetic demonstrator)

Personal methodological project: an integrated assessment of **PET nanoplastics** (polystyrene
deliberately excluded) in the **Citarum river basin, Jawa Barat, Indonesia**, on two local test
organisms — *Macrobrachium rosenbergii* (small crustacean) and *Oreochromis niloticus* (Nile
tilapia).

> **All data in this project is synthetic (dummy).** Values are generated from seeded random
> numbers and calibrated to sit inside plausible published ranges. Nothing here is a field
> measurement and nothing here should be cited as one. See `METHOD-NOTES.md`.

## Run it

```bash
python pet-nano-citarum/run.py            # writes to /mnt/documents/PET-Nano-Citarum
python pet-nano-citarum/run.py <outdir>   # or a directory of your choice
```

Deterministic: seed `20260904`, so every run reproduces the same numbers.

## What you get

```
<outdir>/
  PET-Nanoplastics-Citarum-Integrated-Assessment.xlsx   18 sheets, live formulas, native charts
  csv/    19 tidy CSV tables (one per analytical step)
  figures/ 11 PNG figures
```

## Modules

| File | Contents |
| --- | --- |
| `model.py` | seed, 8 sampling stations (Situ Cisanti → Muara Gembong), 3 seasons, species and dose design, province ranking, palette |
| `ecotox.py` | 96 h dose-response (mortality, growth inhibition, third endpoint), log-logistic LC50/EC50 fit, 5 biomarkers, tissue burden and BCF |
| `behavior.py` | 6 behavioural traits × 6 doses × 7 time points × 3 replicates, both species |
| `risk.py` | species sensitivity distribution, HC5 with bootstrap CI, PNEC (HC5/AF), PEC/PNEC risk quotients and classes |
| `eia.py` | Leopold interaction matrix and RIAM scoring `ES = (A1×A2)(B1+B2+B3)` with mitigation measures |
| `lca.py` | screening cradle-to-grave LCA of 1 kg bottle-grade PET resin, plus 4 end-of-life scenarios linking climate results to nanoplastic release |
| `integrate.py` | integrated 0–100 scorecard per station (ecotoxicity / risk / EIA / exposure, weighted) and the parameter table |
| `figures.py` | the 11 figures, Forest & Moss palette |
| `build_workbook.py` | the XLSX assembly: formatted tables, Excel-side regressions, native charts, figure gallery |
| `run.py` | one entry point |

## Workbook sheets

`0) README & method` · `1) Parameters & sources` · `2) Province ranking` ·
`3) Stations & exposure` · `4) Ecotox dose-response` · `5) Biomarkers` · `5b) Biomarker summary` ·
`6) Behaviour dynamics` · `7) Bioaccumulation` · `8) SSD & HC5` · `9) Risk (PEC-PNEC)` ·
`10) EIA Leopold matrix` · `11) EIA RIAM scoring` · `12) LCA inventory` ·
`13) LCA impacts & EOL` · `14) Integrated scorecard` · `15) Charts` · `Change-log`

The workbook is **live**, not a value dump: LC50/EC50 come from Excel `SLOPE`/`INTERCEPT`
regressions on logit-transformed means, HC5 and PNEC from `NORM.S.INV` on the SSD, risk quotients
and classes from PEC/PNEC formulas, RIAM scores from the A/B inputs, LCA shares from stage sums,
and the integrated index from editable weights in row 5 of sheet 14. Replace the blue input cells
and everything downstream recomputes.

Colour convention: **blue** = editable input, **black** = formula, **green** = cross-sheet link,
**yellow** = assumption worth checking.

## Verified before delivery

- LibreOffice recalculation: 460 formulas, **0 formula errors** (no `#REF!`, `#DIV/0!`, `#VALUE!`, `#NAME?`)
- all 11 figures rendered and visually inspected
- every table carries a `data_status` column stating that it is synthetic
