"""
Stap 6: één Excel-bestand met alle inputs, indicatoren en controles

output/tables/macro_brondata_en_indicatoren.xlsx

Dit bestand is een GEGENEREERDE OUTPUT, geen bron. Pas het niet met de hand
aan: wijzigingen horen in data/raw/ (inputs) of in de code (berekeningen),
waarna je run_all.py opnieuw draait. Het is bedoeld voor co-auteurs die liever
in Excel kijken en voor wie de cijfers wil nalopen zonder Python.

Uitvoeren:  python code/macro/06_excel.py
"""

from datetime import date

import pandas as pd

from common import DATA_PROCESSED, DATA_RAW, OUT_CHECKS, OUT_TABLES, zorg_voor_mappen


def main() -> None:
    zorg_voor_mappen()
    pad = OUT_TABLES / "macro_brondata_en_indicatoren.xlsx"

    leesmij = pd.DataFrame({"Toelichting": [
        "GEGENEREERD BESTAND: niet met de hand aanpassen.",
        f"Aangemaakt op {date.today():%d-%m-%Y} door code/macro/06_excel.py.",
        "Inputs komen uit data/raw/*.csv; herkomst per variabele staat in het blad 'codeboek'.",
        "Alle berekeningen gebeuren in code/macro/03_indicators.py (niet in dit bestand).",
        "Bedragen FOD SZ en NBB in duizend euro. Reëel = prijzen van 2024 (consumptieprijsindex).",
        "Aandelen en ratio's als fractie (0,57 = 57%).",
        "Blad 'perioden': relatieve veranderingen (eind/begin - 1), niet het verschil in indexpunten.",
        "Blad 'bronverificatie': overgenomen waarden gecontroleerd tegen de originele bronbestanden.",
    ]})

    codeboek = pd.read_csv(DATA_RAW / "codebook.csv")
    # enkel de macroreeksen (met kolom 'jaar'); micro-invoer in data/raw/ wordt overgeslagen
    inputs = pd.concat([pd.read_csv(p, index_col="jaar") for p in sorted(DATA_RAW.glob("*.csv"))
                        if p.name != "codebook.csv" and "jaar" in pd.read_csv(p, nrows=0).columns],
                       axis=1).sort_index()

    bs = pd.read_csv(DATA_PROCESSED / "beroepssolidariteit.csv")
    bs_wide = {}
    for deflator in ("cpi", "gezondheidsindex"):
        g = bs[bs["deflator"] == deflator].copy()
        g["kolom"] = g["definitie"] + "_" + g["reeks"]
        bs_wide[deflator] = g.pivot(index="jaar", columns="kolom", values="waarde")

    bladen = {
        "LEESMIJ": (leesmij, False),
        "codeboek": (codeboek, False),
        "inputs": (inputs, True),
        "populaties": (pd.read_csv(DATA_PROCESSED / "populaties.csv", index_col="jaar"), True),
        "samenstelling": (pd.read_csv(DATA_PROCESSED / "samenstelling.csv", index_col="jaar"), True),
        "beroepssolidariteit": (bs_wide["cpi"], True),
        "robuust_gezondheidsindex": (bs_wide["gezondheidsindex"], True),
        "vennootschappen": (pd.read_csv(DATA_PROCESSED / "vennootschappen.csv", index_col="jaar"), True),
        "werknemers_opsplitsing": (pd.read_csv(DATA_PROCESSED / "werknemers_opsplitsing.csv", index_col="jaar"), True),
        "nationale_solidariteit": (pd.read_csv(DATA_PROCESSED / "nationale_solidariteit.csv", index_col="jaar"), True),
        "perioden": (pd.read_csv(DATA_PROCESSED / "perioden.csv"), False),
        "bronverificatie": (pd.read_csv(OUT_CHECKS / "bronverificatie.csv"), False),
    }
    # <!-- wijziging: publicatie | bladen 'rapportcijfers' en 'reconciliatie_werkboek' verwijderd -->
    # Die twee bladen zetten naast elke huidige waarde ook de waarde uit het oude werkboek en uit
    # de conceptversie van het rapport. Deze Excel is een publiek bestand, en daar horen verouderde
    # cijfers niet in thuis (beslissing Wim, 23 september 2026). De vergelijking zelf blijft bestaan
    # als CSV in output/checks/, geschreven door 04_reconcile.py, dat intern blijft. Zie DATA.md §2.5.

    with pd.ExcelWriter(pad, engine="openpyxl") as xl:
        for naam, (df, index) in bladen.items():
            df.to_excel(xl, sheet_name=naam, index=index)
            ws = xl.sheets[naam]
            ws.freeze_panes = "B2"
            # Kolombreedtes een beetje leesbaar maken
            for kol in ws.columns:
                breedte = max(len(str(c.value)) if c.value is not None else 0 for c in kol[:50])
                ws.column_dimensions[kol[0].column_letter].width = min(max(10, breedte + 2), 60)
    print(f"geschreven: {pad.relative_to(OUT_TABLES.parents[1])}")


if __name__ == "__main__":
    main()
