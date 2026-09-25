"""Assemble the integrated-assessment XLSX workbook (openpyxl, live formulas + charts)."""

from __future__ import annotations

import numpy as np
import pandas as pd
from openpyxl import Workbook
from openpyxl.chart import BarChart, LineChart, Reference, ScatterChart, Series
from openpyxl.drawing.image import Image as XLImage
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from model import DATA_STATUS, DOSES_UGL, POLYMER, VERSION

ARIAL = "Arial"
H_FILL = PatternFill("solid", start_color="1F3B2C")
SUB_FILL = PatternFill("solid", start_color="E7EDE4")
YELLOW = PatternFill("solid", start_color="FFF3B0")
BLUE = Font(name=ARIAL, size=10, color="0000FF")
BLACK = Font(name=ARIAL, size=10, color="000000")
GREEN = Font(name=ARIAL, size=10, color="008000")
TITLE = Font(name=ARIAL, size=13, bold=True, color="1F3B2C")
HEAD = Font(name=ARIAL, size=10, bold=True, color="FFFFFF")
THIN = Side(style="thin", color="D9D9D9")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)

NUM0 = '#,##0;(#,##0);-'
NUM2 = '#,##0.00;(#,##0.00);-'
NUM3 = '#,##0.000;(#,##0.000);-'
PCT = '0.0%'


def _sheet_title(ws, title, subtitle):
    ws["A1"] = title
    ws["A1"].font = TITLE
    ws["A2"] = subtitle
    ws["A2"].font = Font(name=ARIAL, size=9, italic=True, color="555555")
    ws["A3"] = f"Data status: {DATA_STATUS}"
    ws["A3"].font = Font(name=ARIAL, size=9, bold=True, color="B4653A")
    ws.sheet_view.showGridLines = False


def write_table(ws, df: pd.DataFrame, start_row: int, start_col: int = 1,
                number_formats: dict | None = None) -> tuple[int, int]:
    """Write a dataframe as a formatted table. Returns (header_row, last_row)."""
    number_formats = number_formats or {}
    for j, col in enumerate(df.columns, start=start_col):
        c = ws.cell(row=start_row, column=j, value=str(col))
        c.font = HEAD
        c.fill = H_FILL
        c.alignment = Alignment(wrap_text=True, vertical="center", horizontal="center")
        c.border = BORDER
        width = max(10, min(34, int(df[col].astype(str).str.len().max() if len(df) else 10) + 2,
                            ))
        width = max(width, min(26, len(str(col)) + 2))
        ws.column_dimensions[get_column_letter(j)].width = width
    for i, (_, row) in enumerate(df.iterrows(), start=start_row + 1):
        for j, col in enumerate(df.columns, start=start_col):
            v = row[col]
            if isinstance(v, (np.integer,)):
                v = int(v)
            elif isinstance(v, (np.floating,)):
                v = None if pd.isna(v) else float(v)
            c = ws.cell(row=i, column=j, value=v)
            c.font = BLACK
            c.border = BORDER
            if col in number_formats:
                c.number_format = number_formats[col]
            elif isinstance(v, float):
                c.number_format = NUM3 if abs(v) < 10 else NUM2
    ws.row_dimensions[start_row].height = 30
    ws.freeze_panes = ws.cell(row=start_row + 1, column=start_col + 2)
    return start_row, start_row + len(df)


def build(path, d: dict):
    wb = Workbook()

    # ---------------------------------------------------------------- 0) README
    ws = wb.active
    ws.title = "0) README & method"
    _sheet_title(ws, f"PET nanoplastics integrated assessment - Citarum basin, West Java (v{VERSION})",
                 "Ecotoxicology + behaviour + risk assessment + EIA + screening LCA, one workbook")
    lines = [
        ("Scope", "PET nanoplastics only (polystyrene excluded, as requested)"),
        ("Test material", POLYMER),
        ("Study area", "Citarum river basin, Jawa Barat - highest composite PET pressure score of the provinces compared in sheet 2"),
        ("Test organisms", "Macrobrachium rosenbergii (small crustacean, PL-25) and Oreochromis niloticus (fish, juvenile)"),
        ("Modules", "1 exposure characterisation | 2 ecotoxicology (dose-response, biomarkers, bioaccumulation) | 3 behavioural dynamics | 4 SSD/PNEC risk assessment | 5 EIA (Leopold + RIAM) | 6 screening LCA of PET | 7 integrated scorecard"),
        ("Functional unit (LCA)", "1 kg PET bottle-grade resin, cradle-to-grave"),
        ("Impact method (LCA)", "IPCC GWP100 proxy factors, CED and water consumption; placeholder for a licensed ecoinvent dataset"),
        ("Risk method", "log-normal species sensitivity distribution -> HC5 -> PNEC = HC5 / AF(3); RQ = PEC95 / PNEC"),
        ("EIA method", "Leopold interaction matrix (magnitude x importance) and RIAM ES = (A1xA2)(B1+B2+B3)"),
        ("HONESTY NOTE", "Every number in this workbook is SYNTHETIC. It is a personal methodological demonstrator, not a field dataset. Nothing here should be cited as a measurement."),
        ("How to reuse", "Replace sheet 3 (exposure) and sheet 4 (dose-response) with real data; all downstream sheets recompute through live formulas."),
        ("Colour convention", "blue = editable input, black = formula, green = cross-sheet link, yellow = key assumption to check"),
        ("Generated by", "pet-nano-citarum/run.py (seeded, reproducible)"),
    ]
    r = 5
    for k, v in lines:
        ws.cell(row=r, column=1, value=k).font = Font(name=ARIAL, size=10, bold=True)
        c = ws.cell(row=r, column=2, value=v)
        c.font = BLACK
        c.alignment = Alignment(wrap_text=True, vertical="top")
        if k == "HONESTY NOTE":
            c.fill = YELLOW
        ws.row_dimensions[r].height = 30 if len(v) > 110 else 16
        r += 1
    ws.column_dimensions["A"].width = 24
    ws.column_dimensions["B"].width = 118

    # ---------------------------------------------------------------- 1) parameters
    ws = wb.create_sheet("1) Parameters & sources")
    _sheet_title(ws, "Parameters, assumptions and status", "status column says whether a value is dummy, assumption, literature-anchored or derived")
    hr, lr = write_table(ws, d["params"], 5)
    for row in ws.iter_rows(min_row=hr + 1, max_row=lr, min_col=2, max_col=2):
        for c in row:
            c.font = BLUE
    for row in ws.iter_rows(min_row=hr + 1, max_row=lr, min_col=5, max_col=5):
        for c in row:
            if c.value in ("assumption", "dummy"):
                c.fill = YELLOW

    # ---------------------------------------------------------------- 2) provinces
    ws = wb.create_sheet("2) Province ranking")
    _sheet_title(ws, "Province-level PET exposure pressure - why West Java",
                 "score = 0.40 river plastic flux + 0.30 PET in waste + 0.20 converter plants + 0.10 population density")
    prov = d["prov"]
    hr, lr = write_table(ws, prov, 5, number_formats={"exposure_pressure_score": NUM2,
                                                      "pet_in_waste_kt_yr": NUM2})
    ch = BarChart()
    ch.type = "bar"
    ch.title = "Composite PET exposure-pressure score by province"
    ch.y_axis.title = "score (0-100)"
    ch.add_data(Reference(ws, min_col=list(prov.columns).index("exposure_pressure_score") + 1,
                          min_row=hr, max_row=lr), titles_from_data=True)
    ch.set_categories(Reference(ws, min_col=2, min_row=hr + 1, max_row=lr))
    ch.height, ch.width = 8, 17
    ws.add_chart(ch, f"A{lr + 3}")

    # ---------------------------------------------------------------- 3) stations & exposure
    ws = wb.create_sheet("3) Stations & exposure")
    _sheet_title(ws, "Sampling stations and measured PET nanoplastic exposure",
                 "8 stations from Situ Cisanti to Muara Gembong x 3 seasons x 3 field replicates")
    hr_s, lr_s = write_table(ws, d["stations"], 5)
    start = lr_s + 3
    ws.cell(row=start - 1, column=1, value="Exposure records (blue = replace with measured data)").font = Font(
        name=ARIAL, size=10, bold=True, color="1F3B2C")
    hr_e, lr_e = write_table(ws, d["exposure"], start)
    ecol = list(d["exposure"].columns).index("pet_np_water_ug_L") + 1
    for row in ws.iter_rows(min_row=hr_e + 1, max_row=lr_e, min_col=ecol, max_col=ecol):
        for c in row:
            c.font = BLUE
    # station x season pivot with live AVERAGEIFS
    piv_row = lr_e + 3
    ws.cell(row=piv_row - 1, column=1,
            value="Mean PET NP in water per station and season (µg/L) - live AVERAGEIFS over the table above").font = Font(
        name=ARIAL, size=10, bold=True, color="1F3B2C")
    seasons = list(d["exposure"].season.unique())
    stations = list(d["stations"].station_code)
    ws.cell(row=piv_row, column=1, value="station_code").font = HEAD
    ws.cell(row=piv_row, column=1).fill = H_FILL
    for j, s in enumerate(seasons, start=2):
        c = ws.cell(row=piv_row, column=j, value=s)
        c.font, c.fill = HEAD, H_FILL
        c.alignment = Alignment(wrap_text=True, horizontal="center")
    scol = get_column_letter(list(d["exposure"].columns).index("station_code") + 1)
    sscol = get_column_letter(list(d["exposure"].columns).index("season") + 1)
    vcol = get_column_letter(ecol)
    rng = f"${hr_e + 1}:${lr_e}"
    for i, st in enumerate(stations, start=piv_row + 1):
        ws.cell(row=i, column=1, value=st).font = BLACK
        for j, s in enumerate(seasons, start=2):
            f = (f'=AVERAGEIFS({vcol}{hr_e + 1}:{vcol}{lr_e},'
                 f'{scol}{hr_e + 1}:{scol}{lr_e},$A{i},'
                 f'{sscol}{hr_e + 1}:{sscol}{lr_e},{get_column_letter(j)}${piv_row})')
            c = ws.cell(row=i, column=j, value=f)
            c.font, c.number_format = BLACK, NUM2
    ch = LineChart()
    ch.title = "Mean PET nanoplastics per station and season (µg/L)"
    ch.y_axis.title = "µg/L"
    ch.x_axis.title = "station (upstream -> estuary)"
    ch.add_data(Reference(ws, min_col=2, max_col=1 + len(seasons), min_row=piv_row,
                          max_row=piv_row + len(stations)), titles_from_data=True)
    ch.set_categories(Reference(ws, min_col=1, min_row=piv_row + 1, max_row=piv_row + len(stations)))
    ch.height, ch.width = 8, 18
    ws.add_chart(ch, f"F{piv_row}")
    exposure_pivot = (piv_row, len(stations))

    # ---------------------------------------------------------------- 4) dose-response
    ws = wb.create_sheet("4) Ecotox dose-response")
    _sheet_title(ws, "Dose-response, 96 h, PET nanoplastics",
                 "LC50 / EC50 are computed with Excel formulas (log-logit regression), not hardcoded")
    hr, lr = write_table(ws, d["dr"], 5)
    dose_col = get_column_letter(list(d["dr"].columns).index("dose_pet_np_ug_L") + 1)
    sp_col = get_column_letter(list(d["dr"].columns).index("species") + 1)
    mort_col = get_column_letter(list(d["dr"].columns).index("mortality_96h_pct") + 1)
    grow_col = get_column_letter(list(d["dr"].columns).index("growth_inhibition_pct") + 1)
    third_col = get_column_letter(list(d["dr"].columns).index("third_endpoint_pct") + 1)
    for col in (mort_col, grow_col, third_col):
        ci = ws[f"{col}{hr}"].column
        for row in ws.iter_rows(min_row=hr + 1, max_row=lr, min_col=ci, max_col=ci):
            for c in row:
                c.font = BLUE

    species = list(d["dr"].species.unique())
    block = lr + 3
    fit_anchor = {}
    for sp in species:
        ws.cell(row=block, column=1, value=f"Regression block - {sp}").font = Font(
            name=ARIAL, size=10, bold=True, color="1F3B2C")
        heads = ["dose (µg/L)", "log10(dose)", "mean mortality %", "logit(mortality)",
                 "mean growth inhib. %", "logit(growth)", "mean 3rd endpoint %", "logit(3rd)"]
        for j, h in enumerate(heads, start=1):
            c = ws.cell(row=block + 1, column=j, value=h)
            c.font, c.fill = HEAD, H_FILL
            c.alignment = Alignment(wrap_text=True, horizontal="center")
            ws.column_dimensions[get_column_letter(j)].width = max(
                ws.column_dimensions[get_column_letter(j)].width or 10, 15)
        r0 = block + 2
        doses = [x for x in DOSES_UGL if x > 0]
        for i, dose in enumerate(doses):
            rr = r0 + i
            ws.cell(row=rr, column=1, value=dose).font = BLUE
            ws.cell(row=rr, column=1).number_format = NUM0
            ws.cell(row=rr, column=2, value=f"=LOG10(A{rr})").font = BLACK
            ws.cell(row=rr, column=2).number_format = NUM3
            for k, (src, out_mean, out_logit, cap) in enumerate([
                    (mort_col, 3, 4, 100), (grow_col, 5, 6, 82), (third_col, 7, 8, 70)]):
                fm = (f'=AVERAGEIFS({src}${hr + 1}:{src}${lr},'
                      f'{sp_col}${hr + 1}:{sp_col}${lr},"{sp}",'
                      f'{dose_col}${hr + 1}:{dose_col}${lr},$A{rr})')
                c = ws.cell(row=rr, column=out_mean, value=fm)
                c.font, c.number_format = GREEN, NUM2
                mc = get_column_letter(out_mean)
                lg = (f'=LN(MAX(MIN({mc}{rr},{cap}-0.5),0.5)/'
                      f'({cap}-MAX(MIN({mc}{rr},{cap}-0.5),0.5)))')
                c = ws.cell(row=rr, column=out_logit, value=lg)
                c.font, c.number_format = BLACK, NUM3
        rl = r0 + len(doses) - 1
        stat_row = rl + 2
        labels = [("LC50 mortality (µg/L)", 4), ("EC50 growth (µg/L)", 6),
                  ("EC50 3rd endpoint (µg/L)", 8)]
        for i, (lab, lcol) in enumerate(labels):
            rr = stat_row + i
            ws.cell(row=rr, column=1, value=lab).font = Font(name=ARIAL, size=10, bold=True)
            L = get_column_letter(lcol)
            slope = f"SLOPE({L}{r0}:{L}{rl},$B${r0}:$B${rl})"
            icept = f"INTERCEPT({L}{r0}:{L}{rl},$B${r0}:$B${rl})"
            c = ws.cell(row=rr, column=3, value=f"=10^(-{icept}/{slope})")
            c.font, c.number_format = BLACK, NUM0
            ws.cell(row=rr, column=4, value=f"=RSQ({L}{r0}:{L}{rl},$B${r0}:$B${rl})").number_format = NUM3
            ws.cell(row=rr, column=5, value="Hill slope").font = Font(name=ARIAL, size=9, italic=True)
            ws.cell(row=rr, column=6, value=f"={slope}").number_format = NUM3
            if i == 0:
                fit_anchor[sp] = f"'4) Ecotox dose-response'!$C${rr}"
        ws.cell(row=stat_row + 3, column=1,
                value="Method: log-logistic linearised as logit(response) = a*log10(dose) + b; EC50 = 10^(-b/a).").font = Font(
            name=ARIAL, size=9, italic=True, color="555555")
        ch = ScatterChart()
        ch.title = f"Dose-response - {sp}"
        ch.x_axis.title = "log10 dose (µg/L)"
        ch.y_axis.title = "response (%)"
        xref = Reference(ws, min_col=2, min_row=r0, max_row=rl)
        for lcol, name in ((3, "mortality %"), (5, "growth inhibition %"), (7, "3rd endpoint %")):
            s = Series(Reference(ws, min_col=lcol, min_row=r0, max_row=rl), xref, title=name)
            s.marker.symbol = "circle"
            ch.series.append(s)
        ch.height, ch.width = 8, 14
        ws.add_chart(ch, f"J{block + 1}")
        block = stat_row + 6

    # ---------------------------------------------------------------- 5) biomarkers
    ws = wb.create_sheet("5) Biomarkers")
    _sheet_title(ws, "Oxidative stress and neurotoxicity biomarkers",
                 "hepatopancreas (crustacean) / liver (fish); fold change relative to the unexposed control")
    write_table(ws, d["bio"], 5)

    ws = wb.create_sheet("5b) Biomarker summary")
    _sheet_title(ws, "Biomarker means per dose", "mean of 3 analytical replicates")
    bsum = (d["bio"].groupby(["species", "biomarker", "dose_pet_np_ug_L"])
            [["value", "fold_change_vs_control"]].mean().round(3).reset_index())
    write_table(ws, bsum, 5)

    # ---------------------------------------------------------------- 6) behaviour
    ws = wb.create_sheet("6) Behaviour dynamics")
    _sheet_title(ws, "Behavioural dynamics, 0-96 h open-field tracking",
                 "six traits x 6 doses x 7 time points x 3 replicates, both species")
    write_table(ws, d["bsum"], 5)
    hr = 5
    lr = 5 + len(d["bsum"])
    sub = d["bsum"][(d["bsum"].species == "Macrobrachium rosenbergii")
                    & (d["bsum"].trait == "thigmotaxis_pct_time_wall_zone")]
    tpiv = sub.pivot(index="time_h", columns="dose_pet_np_ug_L", values="mean_value")
    start = lr + 3
    ws.cell(row=start - 1, column=1,
            value="Thigmotaxis (% time in wall zone), Macrobrachium - dose x time").font = Font(
        name=ARIAL, size=10, bold=True, color="1F3B2C")
    tp = tpiv.reset_index()
    tp.columns = ["time_h"] + [f"{c:,.0f} µg/L" for c in tpiv.columns]
    hr2, lr2 = write_table(ws, tp, start)
    ch = LineChart()
    ch.title = "Thigmotaxis over exposure time (Macrobrachium)"
    ch.x_axis.title = "time (h)"
    ch.y_axis.title = "% time in wall zone"
    ch.add_data(Reference(ws, min_col=2, max_col=1 + len(tpiv.columns), min_row=hr2, max_row=lr2),
                titles_from_data=True)
    ch.set_categories(Reference(ws, min_col=1, min_row=hr2 + 1, max_row=lr2))
    ch.height, ch.width = 9, 18
    ws.add_chart(ch, f"J{hr2}")

    # ---------------------------------------------------------------- 7) bioaccumulation
    ws = wb.create_sheet("7) Bioaccumulation")
    _sheet_title(ws, "Tissue burden and bioconcentration factors",
                 "96 h exposure, 48 h depuration removal reported per tissue")
    write_table(ws, d["bioacc"], 5)

    # ---------------------------------------------------------------- 8) SSD
    ws = wb.create_sheet("8) SSD & HC5")
    _sheet_title(ws, "Species sensitivity distribution and PNEC",
                 "log-normal SSD over 12 taxa; HC5 confidence interval from 2000 bootstrap resamples")
    ssd = d["ssd"]
    hr, lr = write_table(ws, ssd, 5)
    lcol = get_column_letter(list(ssd.columns).index("log10_conc") + 1)
    rr = lr + 3
    stats_rows = [
        ("mu of log10(NOEC)", f"=AVERAGE({lcol}{hr + 1}:{lcol}{lr})", NUM3, False),
        ("sigma of log10(NOEC)", f"=STDEV({lcol}{hr + 1}:{lcol}{lr})", NUM3, False),
        ("HC50 (µg/L)", f"=10^B{rr}", NUM0, False),
        ("HC5 (µg/L)", f"=10^(B{rr}+NORM.S.INV(0.05)*B{rr + 1})", NUM0, False),
        ("Assessment factor (editable)", d["ssd_fit"]["assessment_factor"], NUM0, True),
        ("PNEC (µg/L)", f"=B{rr + 3}/B{rr + 4}", NUM3, False),
        ("HC5 95 % CI low (bootstrap, µg/L)", d["ssd_fit"]["hc5_ci95_low_ug_L"], NUM2, True),
        ("HC5 95 % CI high (bootstrap, µg/L)", d["ssd_fit"]["hc5_ci95_high_ug_L"], NUM2, True),
    ]
    for i, (lab, val, fmt, is_input) in enumerate(stats_rows):
        r_ = rr + i
        ws.cell(row=r_, column=1, value=lab).font = Font(name=ARIAL, size=10, bold=True)
        c = ws.cell(row=r_, column=2, value=val)
        c.number_format = fmt
        c.font = BLUE if is_input else BLACK
        if is_input:
            c.fill = YELLOW
    pnec_ref = f"'8) SSD & HC5'!$B${rr + 5}"
    ch = ScatterChart()
    ch.title = "SSD: cumulative fraction affected vs log10 concentration"
    ch.x_axis.title = "log10 NOEC/EC10 (µg/L)"
    ch.y_axis.title = "cumulative probability"
    s = Series(Reference(ws, min_col=list(ssd.columns).index("cumulative_probability") + 1,
                         min_row=hr + 1, max_row=lr),
               Reference(ws, min_col=list(ssd.columns).index("log10_conc") + 1,
                         min_row=hr + 1, max_row=lr), title="taxa")
    s.marker.symbol = "circle"
    s.graphicalProperties.line.noFill = True
    ch.series.append(s)
    ch.height, ch.width = 9, 16
    ws.add_chart(ch, f"J{rr}")

    # ---------------------------------------------------------------- 9) risk
    ws = wb.create_sheet("9) Risk (PEC-PNEC)")
    _sheet_title(ws, "Risk characterisation per station and season",
                 "PEC from sheet 3, PNEC linked from sheet 8; RQ and class are live formulas")
    risk = d["risk"]
    hr, lr = write_table(ws, risk, 5, number_formats={"rq_mean": NUM3,
                                                      "rq_reasonable_worst_case": NUM3})
    cols = list(risk.columns)
    c_pnec = get_column_letter(cols.index("pnec_ug_L") + 1)
    c_pecm = get_column_letter(cols.index("pec_mean_ug_L") + 1)
    c_pec95 = get_column_letter(cols.index("pec_95th_ug_L") + 1)
    c_hc5 = get_column_letter(cols.index("hc5_ug_L") + 1)
    c_af = get_column_letter(cols.index("assessment_factor") + 1)
    c_rqm = get_column_letter(cols.index("rq_mean") + 1)
    c_rqw = get_column_letter(cols.index("rq_reasonable_worst_case") + 1)
    c_clm = get_column_letter(cols.index("risk_class_mean") + 1)
    c_clw = get_column_letter(cols.index("risk_class_rwc") + 1)
    for i in range(hr + 1, lr + 1):
        ws[f"{c_hc5}{i}"] = f"='8) SSD & HC5'!$B${rr + 3}"
        ws[f"{c_hc5}{i}"].font = GREEN
        ws[f"{c_hc5}{i}"].number_format = NUM2
        ws[f"{c_pnec}{i}"] = f"={c_hc5}{i}/{c_af}{i}"
        ws[f"{c_pnec}{i}"].font = BLACK
        ws[f"{c_pnec}{i}"].number_format = NUM3
        ws[f"{c_rqm}{i}"] = f"={c_pecm}{i}/{c_pnec}{i}"
        ws[f"{c_rqw}{i}"] = f"={c_pec95}{i}/{c_pnec}{i}"
        for cc, src in ((c_clm, c_rqm), (c_clw, c_rqw)):
            ws[f"{cc}{i}"] = (f'=IF({src}{i}<0.1,"negligible",IF({src}{i}<1,"low",'
                              f'IF({src}{i}<10,"moderate","high")))')
            ws[f"{cc}{i}"].font = BLACK
        for cc in (c_rqm, c_rqw):
            ws[f"{cc}{i}"].number_format = NUM3
            ws[f"{cc}{i}"].font = BLACK
    ch = BarChart()
    ch.title = "Risk quotient (PEC95 / PNEC) per station-season record"
    ch.y_axis.title = "RQ (-)"
    ch.add_data(Reference(ws, min_col=cols.index("rq_reasonable_worst_case") + 1,
                          min_row=hr, max_row=lr), titles_from_data=True)
    ch.set_categories(Reference(ws, min_col=1, min_row=hr + 1, max_row=lr))
    ch.height, ch.width = 9, 22
    ws.add_chart(ch, f"A{lr + 3}")

    # ---------------------------------------------------------------- 10-11) EIA
    ws = wb.create_sheet("10) EIA Leopold matrix")
    _sheet_title(ws, "Leopold interaction matrix",
                 "magnitude (-5..+5) x importance (1..5); only interacting cells are listed")
    leo = d["leopold"]
    hr, lr = write_table(ws, leo, 5)
    cols = list(leo.columns)
    cm = get_column_letter(cols.index("magnitude_minus5_to_plus5") + 1)
    ci = get_column_letter(cols.index("importance_1_to_5") + 1)
    cs = get_column_letter(cols.index("interaction_score") + 1)
    cd = get_column_letter(cols.index("direction") + 1)
    for i in range(hr + 1, lr + 1):
        ws[f"{cm}{i}"].font = BLUE
        ws[f"{ci}{i}"].font = BLUE
        ws[f"{cs}{i}"] = f"={cm}{i}*{ci}{i}"
        ws[f"{cs}{i}"].font = BLACK
        ws[f"{cd}{i}"] = f'=IF({cm}{i}<0,"adverse","beneficial")'
    ws.cell(row=lr + 2, column=1, value="Sum of adverse interaction scores").font = Font(
        name=ARIAL, size=10, bold=True)
    ws.cell(row=lr + 2, column=cols.index("interaction_score") + 1,
            value=f"=SUMIF({cs}{hr + 1}:{cs}{lr},\"<0\")").font = BLACK

    ws = wb.create_sheet("11) EIA RIAM scoring")
    _sheet_title(ws, "Rapid Impact Assessment Matrix (RIAM)",
                 "ES = (A1 x A2) x (B1 + B2 + B3); range classes follow Pastakia & Jensen (1998)")
    riam = d["riam"]
    hr, lr = write_table(ws, riam, 5)
    cols = list(riam.columns)
    a1 = get_column_letter(cols.index("A1_importance_of_condition") + 1)
    a2 = get_column_letter(cols.index("A2_magnitude_of_change") + 1)
    b1 = get_column_letter(cols.index("B1_permanence") + 1)
    b2 = get_column_letter(cols.index("B2_reversibility") + 1)
    b3 = get_column_letter(cols.index("B3_cumulative") + 1)
    at = get_column_letter(cols.index("AT_A1xA2") + 1)
    bt = get_column_letter(cols.index("BT_B1plusB2plusB3") + 1)
    es = get_column_letter(cols.index("ES_environmental_score") + 1)
    for i in range(hr + 1, lr + 1):
        for c in (a1, a2, b1, b2, b3):
            ws[f"{c}{i}"].font = BLUE
        ws[f"{at}{i}"] = f"={a1}{i}*{a2}{i}"
        ws[f"{bt}{i}"] = f"={b1}{i}+{b2}{i}+{b3}{i}"
        ws[f"{es}{i}"] = f"={at}{i}*{bt}{i}"
        for c in (at, bt, es):
            ws[f"{c}{i}"].font = BLACK
    ch = BarChart()
    ch.type = "bar"
    ch.title = "RIAM environmental score per component"
    ch.add_data(Reference(ws, min_col=cols.index("ES_environmental_score") + 1,
                          min_row=hr, max_row=lr), titles_from_data=True)
    ch.set_categories(Reference(ws, min_col=1, min_row=hr + 1, max_row=lr))
    ch.height, ch.width = 10, 18
    ws.add_chart(ch, f"A{lr + 3}")

    # ---------------------------------------------------------------- 12-13) LCA
    ws = wb.create_sheet("12) LCA inventory")
    _sheet_title(ws, "Screening LCI - 1 kg PET bottle-grade resin, cradle-to-grave",
                 "proxy characterisation factors; replace with a licensed ecoinvent 3.10 dataset")
    inv = d["inv"]
    hr, lr = write_table(ws, inv, 5, number_formats={"gwp100_kgCO2e": NUM3, "ced_MJ": NUM2})
    cols = list(inv.columns)
    cg = get_column_letter(cols.index("gwp100_kgCO2e") + 1)
    ws.cell(row=lr + 2, column=1, value="Total cradle-to-grave (before EOL scenario)").font = Font(
        name=ARIAL, size=10, bold=True)
    ws.cell(row=lr + 2, column=cols.index("gwp100_kgCO2e") + 1,
            value=f"=SUM({cg}{hr + 1}:{cg}{lr})").number_format = NUM3
    lci_total = f"'12) LCA inventory'!${cg}${lr + 2}"

    ws = wb.create_sheet("13) LCA impacts & EOL")
    _sheet_title(ws, "Impact results by stage and end-of-life scenario",
                 "shares are live formulas; nanoplastic release links climate results to the exposure module")
    imp = d["imp"]
    hr, lr = write_table(ws, imp, 5, number_formats={"gwp100_kgCO2e": NUM3,
                                                     "share_of_gwp_pct": NUM2})
    cols = list(imp.columns)
    cg = get_column_letter(cols.index("gwp100_kgCO2e") + 1)
    csh = get_column_letter(cols.index("share_of_gwp_pct") + 1)
    for i in range(hr + 1, lr + 1):
        ws[f"{csh}{i}"] = f"=100*{cg}{i}/SUM({cg}${hr + 1}:{cg}${lr})"
        ws[f"{csh}{i}"].number_format = NUM2
        ws[f"{csh}{i}"].font = BLACK
    ch = BarChart()
    ch.type = "bar"
    ch.title = "GWP100 contribution by life cycle stage (kg CO2e / kg PET)"
    ch.add_data(Reference(ws, min_col=cols.index("gwp100_kgCO2e") + 1, min_row=hr, max_row=lr),
                titles_from_data=True)
    ch.set_categories(Reference(ws, min_col=1, min_row=hr + 1, max_row=lr))
    ch.height, ch.width = 8, 17
    ws.add_chart(ch, f"H{hr}")

    eol = d["eol"]
    start = lr + 20
    ws.cell(row=start - 1, column=1, value="End-of-life scenarios").font = Font(
        name=ARIAL, size=11, bold=True, color="1F3B2C")
    hr2, lr2 = write_table(ws, eol, start, number_formats={
        "gwp100_kgCO2e_per_kg": NUM3, "pet_np_release_mg_per_kg_resin": NUM2})
    ecols = list(eol.columns)
    c_leak = get_column_letter(ecols.index("river_leakage_frac") + 1)
    c_fac = get_column_letter(ecols.index("np_release_factor_mg_per_kg_leaked") + 1)
    c_rel = get_column_letter(ecols.index("pet_np_release_mg_per_kg_resin") + 1)
    c_pet = get_column_letter(ecols.index("pet_to_river_g_per_kg") + 1)
    for i in range(hr2 + 1, lr2 + 1):
        ws[f"{c_leak}{i}"].font = BLUE
        ws[f"{c_fac}{i}"].font = BLUE
        ws[f"{c_pet}{i}"] = f"={c_leak}{i}*1000"
        ws[f"{c_rel}{i}"] = f"={c_leak}{i}*{c_fac}{i}"
        ws[f"{c_rel}{i}"].number_format = NUM2
        ws[f"{c_pet}{i}"].font = BLACK
        ws[f"{c_rel}{i}"].font = BLACK
    ch = BarChart()
    ch.title = "PET nanoplastic release per kg resin, by end-of-life scenario"
    ch.y_axis.title = "mg PET NP / kg resin"
    ch.add_data(Reference(ws, min_col=ecols.index("pet_np_release_mg_per_kg_resin") + 1,
                          min_row=hr2, max_row=lr2), titles_from_data=True)
    ch.set_categories(Reference(ws, min_col=1, min_row=hr2 + 1, max_row=lr2))
    ch.height, ch.width = 8, 17
    ws.add_chart(ch, f"H{hr2}")

    # ---------------------------------------------------------------- 14) scorecard
    ws = wb.create_sheet("14) Integrated scorecard")
    _sheet_title(ws, "Integrated scorecard per station",
                 "weighted combination of ecotoxicity, risk, EIA significance and exposure; weights are editable")
    sc = d["score"]
    hr, lr = write_table(ws, sc, 7, number_formats={"integrated_index_0_100": NUM2})
    cols = list(sc.columns)
    w_cells = {}
    for i, k in enumerate(["ecotox", "risk", "eia", "exposure"]):
        col = 1 + i * 2
        ws.cell(row=5, column=col, value=f"w_{k}").font = Font(name=ARIAL, size=10, bold=True)
        c = ws.cell(row=5, column=col + 1, value=float(sc[f"w_{k}"].iloc[0]))
        c.font, c.fill, c.number_format = BLUE, YELLOW, NUM2
        w_cells[k] = f"${get_column_letter(col + 1)}$5"
    ws.cell(row=6, column=1, value="weights must sum to 1 ->").font = Font(
        name=ARIAL, size=9, italic=True)
    ws.cell(row=6, column=2, value="=" + "+".join(w_cells.values())).number_format = NUM2
    c_eco = get_column_letter(cols.index("ecotox_index_0_100") + 1)
    c_rsk = get_column_letter(cols.index("risk_index_0_100") + 1)
    c_eia = get_column_letter(cols.index("eia_index_0_100") + 1)
    c_exp = get_column_letter(cols.index("exposure_index_0_100") + 1)
    c_int = get_column_letter(cols.index("integrated_index_0_100") + 1)
    c_cls = get_column_letter(cols.index("priority_class") + 1)
    for i in range(hr + 1, lr + 1):
        ws[f"{c_int}{i}"] = (f"={w_cells['ecotox']}*{c_eco}{i}+{w_cells['risk']}*{c_rsk}{i}"
                             f"+{w_cells['eia']}*{c_eia}{i}+{w_cells['exposure']}*{c_exp}{i}")
        ws[f"{c_int}{i}"].number_format = NUM2
        ws[f"{c_int}{i}"].font = BLACK
        ws[f"{c_cls}{i}"] = (f'=IF({c_int}{i}<25,"low",IF({c_int}{i}<50,"moderate",'
                             f'IF({c_int}{i}<75,"high","very high")))')
        ws[f"{c_cls}{i}"].font = BLACK
    ch = BarChart()
    ch.title = "Integrated concern index per station (0-100)"
    ch.y_axis.title = "index"
    ch.add_data(Reference(ws, min_col=cols.index("integrated_index_0_100") + 1,
                          min_row=hr, max_row=lr), titles_from_data=True)
    ch.set_categories(Reference(ws, min_col=1, min_row=hr + 1, max_row=lr))
    ch.height, ch.width = 8, 17
    ws.add_chart(ch, f"A{lr + 3}")

    # ---------------------------------------------------------------- 15) charts
    ws = wb.create_sheet("15) Charts")
    _sheet_title(ws, "Figure gallery", "same figures as /figures/*.png, generated from the tables in this workbook")
    row = 5
    for fig_path, caption in d["figures"]:
        ws.cell(row=row, column=1, value=caption).font = Font(
            name=ARIAL, size=11, bold=True, color="1F3B2C")
        img = XLImage(fig_path)
        scale = min(1.0, 980 / img.width)
        img.width, img.height = int(img.width * scale), int(img.height * scale)
        ws.add_image(img, f"A{row + 1}")
        row += int(img.height / 19) + 4

    # ---------------------------------------------------------------- change-log
    ws = wb.create_sheet("Change-log")
    _sheet_title(ws, "Change-log", "version history of this workbook")
    cl = pd.DataFrame([
        dict(version=VERSION, date="2026-09-04",
             change="First release: exposure, ecotoxicology, behaviour, bioaccumulation, SSD/PNEC risk, "
                    "Leopold + RIAM EIA, screening PET LCA with EOL scenarios, integrated scorecard, 11 figures.",
             author="Robby Fajrino Nugraha (built with the pet-nano-citarum runner)")])
    write_table(ws, cl, 5)

    wb.save(path)
    return path
