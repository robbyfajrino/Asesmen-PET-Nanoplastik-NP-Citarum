# Method notes, assumptions and limitations

The purpose of this project is to demonstrate that the methodological chain — exposure characterisation → ecotoxicology → behaviour → risk assessment →
EIA → LCA → integrated prioritisation | can be built, documented and audited end to end. So treat it as a working demonstrator, not as evidence about the Citarum.

Values were chosen so that orders of magnitude are defensible: nanoplastic effect concentrations in the hundreds to thousands of µg/L, ambient river concentrations in the tens of µg/L, PET cradle-to-grave GWP around 4–5 kg CO2e per kg resin. That calibration is a plausibility constraint, not a citation.

## 1. Scope

- **Stressor:** PET nanoplastics, d50 ≈ 120 nm, spherical, no PS (out of the requested scope).
- **Area:** Citarum basin, Jawa Barat, 8 stations from Situ Cisanti (reference) to Muara Gembong
  (estuary), 3 hydrological seasons, 3 field replicates.
- **Organisms:** *Macrobrachium rosenbergii* PL-25 and *Oreochromis niloticus* juveniles — both
  farmed in the basin, so exposure is also a food-system question.
- **LCA functional unit:** 1 kg bottle-grade PET resin, cradle-to-grave.

West Java was selected in the workbook itself (sheet 2), through a composite pressure score
(0.40 river plastic flux index + 0.30 PET in municipal waste + 0.20 converter/textile plants +
0.10 population density). The inputs to that score are synthetic too, but the decision rule is
explicit and editable rather than asserted.

## 2. Ecotoxicology

- Responses are generated from a log-logistic model `E = top / (1 + (EC50/C)^slope)` with
  lognormal replicate noise, 4 replicates × 20 organisms.
- Effect concentrations are reported twice: a Python `curve_fit` reference fit (CSV 05) and an
  Excel-side logit linear regression in sheet 4. The two differ by a few per cent because the
  Excel route linearises against a fixed asymptote — that difference is left visible on purpose,
  as a reminder that a fitted EC50 depends on the model, not only on the data.
- The crustacean is set more sensitive than the fish, consistent with the general pattern for
  small crustaceans versus juvenile fish. That is an assumption, not a finding.
- Biomarkers: SOD, CAT and GST biphasic (induction then exhaustion), MDA monotonic increase,
  AChE inhibited — a conventional oxidative-stress plus neurotoxicity narrative.
- Bioaccumulation uses tissue affinity factors (gut > gill > hepatopancreas/liver >> muscle) and
  a fixed uptake coefficient, so BCF is dose-independent by construction. Real BCFs are not.

## 3. Behavioural dynamics

Six traits, effect scaled by `log10(dose)` and saturating in time as `1 - exp(-3.1 t)`. Direction
of effect is fixed a priori: locomotion, feeding and aggression down; thigmotaxis and freezing up.
No dose × time interaction beyond that separable form, and no recovery phase.

## 4. Risk assessment

- SSD: log-normal fit over 12 taxa (algae, macrophyte, rotifer, cladocerans, insect larva, mussel,
  prawn, fish). HC5 = 5th percentile; 95 % CI from 2000 bootstrap resamples.
- PNEC = HC5 / AF, AF = 3 because an SSD with ≥8 species from ≥8 groups is available. The AF is an
  editable yellow cell — a reviewer who wants AF = 5 changes one cell.
- PEC = station-season mean; the reasonable worst case uses `mean + 1.645 × SD`. With only 3
  replicates that 95th percentile is weak; with real data use the full distribution.
- RQ banding: <0.1 negligible, <1 low, <10 moderate, ≥10 high.
- **Limitation:** an SSD built on mass concentration (µg/L) for a particulate stressor is
  contested. Particle number, specific surface area and size distribution may be better dose
  metrics; the exposure sheet therefore also carries particle count, d50 and zeta potential so an
  alternative dose metric can be tested later.

## 5. EIA

- Leopold: magnitude −5…+5 × importance 1…5, only interacting cells listed, both inputs editable.
- RIAM: `ES = (A1 × A2) × (B1 + B2 + B3)` with the Pastakia & Jensen range bands. Scoring is
  expert-judgement by construction; here the "expert" is the author, so the scores are a worked
  illustration of the method rather than a stakeholder-validated assessment. A real RIAM needs a
  panel and documented reasoning per cell.
- Mitigation measures are attached to every component so the matrix is decision-oriented.

## 6. Screening LCA

- Proxy characterisation factors, not ecoinvent. `A1` dominates (~48 % of GWP), which is the
  expected shape for virgin PET, but the absolute value should not be quoted.
- Grid factor 0.79 kg CO2e/kWh for the Jamali system — literature-anchored order of magnitude,
  still to be replaced with a dataset value.
- Recycling credit is a simple avoided-burden memo (1.85 kg CO2e per kg recycled resin) applied
  outside a formal system-expansion framework; a cut-off calculation would remove it.
- End-of-life scenarios link the LCA to the exposure module through a release factor
  (mg PET nanoplastics per kg PET reaching the river). That coupling is the interesting part
  methodologically and the weakest part empirically: fragmentation-to-nanoplastic yields in
  tropical rivers are essentially unquantified.

## 7. Integrated scorecard

Four sub-indices (ecotoxicity potential, risk, EIA-weighted significance, exposure level), each
min-max normalised to 0–100 across the 8 stations, then combined with weights 0.30 / 0.35 / 0.20 /
0.15. Two consequences to keep in mind:

- The index is **relative**, not absolute: the least-pressured station scores 0 by construction,
  which does not mean zero concern.
- The weights are a value judgement. They live in editable yellow cells so an alternative
  weighting can be tried in seconds.

## 8. How to turn this into real work

1. Replace sheet 3 with measured water and sediment concentrations (with method, LOD and recovery).
2. Replace sheet 4 with laboratory dose-response, keeping the raw replicate rows.
3. Replace the SSD rows in sheet 8 with sourced NOEC/EC10 values, one citation per row.
4. Swap the LCA factors in sheet 12 for a licensed ecoinvent 3.10 dataset and re-run.
5. Have the RIAM matrix scored by a panel, not one person.
6. Only then change the `data_status` column — and change it row by row, not globally.
