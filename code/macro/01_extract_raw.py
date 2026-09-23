"""
Stap 1: inputreeksen overnemen uit de werkboeken -> data/raw/*.csv

Wat dit script doet
-------------------
1. Het leest elke reeks uit bronspec.REEKSEN op de plaats waar ze in het
   werkboek staat (blad, rij, kolommen).
2. Het schrijft per thema één CSV-bestand met één rij per jaar.
3. Het schrijft data/raw/codebook.csv met per variabele de volledige
   herkomst (bron -> werkboek -> CSV).

Waarom een apart extractiescript?
---------------------------------
De CSV-bestanden zijn de inputs van alle verdere berekeningen. Door ze met
code uit het werkboek te halen (in plaats van met de hand te kopiëren), is de
overname zelf reproduceerbaar en controleerbaar. Formules uit het werkboek
worden hier NIET overgenomen: enkel ingevoerde waarden. Alle berekeningen
gebeuren opnieuw in 03_indicators.py.

Uitvoeren:  python code/macro/01_extract_raw.py
"""

import openpyxl
import pandas as pd

from bronspec import REEKSEN
from common import DATA_RAW, DATA_SOURCES, WERKBOEK, zorg_voor_mappen

RSVZ_WERKBOEK = DATA_SOURCES / "rsvz" / "rsvz_samenstelling_zelfstandigen_2000-2024.xlsx"


def lees_rij(blad, rij: int, kol_eerste_jaar: int, eerste_jaar: int, laatste_jaar: int) -> pd.Series:
    """Lees een reeks jaarwaarden uit één rij van een werkblad.

    `data_only=True` bij het openen zorgt dat we de WAARDEN krijgen die Excel
    laatst heeft opgeslagen, niet de formules.
    """
    waarden = {}
    for i, jaar in enumerate(range(eerste_jaar, laatste_jaar + 1)):
        cel = blad.cell(row=rij, column=kol_eerste_jaar + i).value
        # Sommige cellen bevatten een getal als tekst met spaties (bv. '58 759').
        if isinstance(cel, str):
            cel = cel.replace("\xa0", "").replace(" ", "")
            # In de FOD SZ-tabellen betekent '-' dat er geen bedrag is
            cel = 0.0 if cel == "-" else float(cel)
        waarden[jaar] = cel
    return pd.Series(waarden, name="waarde", dtype="float64")


def main() -> None:
    zorg_voor_mappen()

    # Beide werkboeken één keer openen (read_only maakt het sneller).
    werkboeken = {
        "willem": openpyxl.load_workbook(WERKBOEK, data_only=True, read_only=False),
        "rsvz": openpyxl.load_workbook(RSVZ_WERKBOEK, data_only=True, read_only=False),
        # aanvullende reeksen die niet in het werkboek staan: rechtstreeks uit de bron
        "fodsz_z": openpyxl.load_workbook(DATA_SOURCES / "fodsz" / "fodsz_zelfstandigen_2000-2025.xlsm", data_only=True),
        "fodsz_w": openpyxl.load_workbook(DATA_SOURCES / "fodsz" / "fodsz_werknemers_2000-2025.xlsm", data_only=True),
    }

    # Verzamel de reeksen per doel-CSV
    per_csv: dict[str, dict[str, pd.Series]] = {}
    for r in REEKSEN:
        blad = werkboeken[r.werkboek][r.blad]
        s = lees_rij(blad, r.rij, r.kol_eerste_jaar, *r.jaren)

        # Controle: een lege cel in het midden van een reeks wijst op een
        # verkeerde rij of kolom in de specificatie.
        if s.isna().any():
            ontbrekend = s[s.isna()].index.tolist()
            raise ValueError(f"{r.variabele}: lege cellen voor jaren {ontbrekend} in {r.werkboek_locatie}")

        per_csv.setdefault(r.csv, {})[r.variabele] = s

    # Schrijf één CSV per thema. Jaren zonder waarde blijven leeg.
    for naam, kolommen in per_csv.items():
        df = pd.DataFrame(kolommen)
        df.index.name = "jaar"
        df = df.sort_index()
        pad = DATA_RAW / f"{naam}.csv"
        df.to_csv(pad, float_format="%.15g")
        print(f"geschreven: {pad.relative_to(DATA_RAW.parents[1])}  ({df.shape[0]} jaren, {df.shape[1]} reeksen)")

    # Codeboek: één rij per variabele, met de volledige herkomst
    codeboek = pd.DataFrame([
        {
            "bestand": f"data/raw/{r.csv}.csv",
            "variabele": r.variabele,
            "label": r.label,
            "eenheid": r.eenheid,
            "jaren": f"{r.jaren[0]}-{r.jaren[1]}",
            "overgenomen_uit": r.werkboek_locatie,
            "oorspronkelijke_bron": r.bron_organisatie,
            "bronbestand": r.bron_bestand if "GEEN" in r.bron_bestand or "Geen" in r.bron_bestand
            else f"data/sources/{r.bron_bestand}",
            "locatie_in_bron": r.bron_locatie,
            "geraadpleegd": r.geraadpleegd,
            "automatisch_geverifieerd": ("ja" if r.verificatie else
                                         "n.v.t. (rechtstreeks uit bronbestand)" if r.werkboek.startswith("fodsz")
                                         else "nee (geen bronbestand)"),
            "opmerking": r.opmerking,
        }
        for r in REEKSEN
    ])
    codeboek.to_csv(DATA_RAW / "codebook.csv", index=False)
    print(f"geschreven: data/raw/codebook.csv  ({len(codeboek)} variabelen)")


if __name__ == "__main__":
    main()
