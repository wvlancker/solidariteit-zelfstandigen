"""
Controle van Tabel 7 (§5.2.2.1) tegen het werkboek (leesnota J6 en E)

Waarom?
-------
Tabel 7 somt de bedragen op waarmee de uitkeringen gesimuleerd zijn. Die bedragen zijn met de
hand in de tekst gezet; de simulaties zelf rekenen met de parameters in het werkboek
'unizo_results_final.xlsx' (bladen 'Primaire arbeidsongeschiktheid' en 'Werkloosheid').
Bij de check van de finale versie (leesnota J6) bleken twee bedragen niet overeen te komen.
Dit script legt de vergelijking vast, zodat ze herhaalbaar is en niet opnieuw met de hand moet.

Peildatum (beslissing Wim, 22 september 2026): 30 juni 2024. Dat is NA de indexering van de
sociale uitkeringen met 2% op 1 mei 2024. Waar de tabel en het werkboek verschillen, staat de
tabel telkens op het niveau van vóór die indexering en het werkboek erna; de tabel is daarom
aangepast aan het werkboek, niet omgekeerd.

Uitvoer
-------
  output/checks/tabel7_bedragen.csv    één rij per bedrag, met tabelwaarde, werkboekwaarde,
                                       verschil, de cel in het werkboek en een oordeel

Uitvoeren:  python code/tekst/controle_tabel7.py
"""

import sys
from pathlib import Path

import openpyxl
import pandas as pd

WORTEL = Path(__file__).resolve().parents[2]
WERKBOEK = WORTEL / "data" / "sources" / "micro" / "unizo_results_final.xlsx"
UIT = WORTEL / "output" / "checks" / "tabel7_bedragen.csv"

# ---------------------------------------------------------------------------
# De bedragen zoals ze in Tabel 7 staan (na de correctie van 22 september 2026),
# met de cel in het werkboek waar de simulatie hetzelfde getal vandaan haalt.
#   (rubriek, omschrijving zoals in de tabel, waarde in de tabel, blad, cel)
# Bedragen per dag staan per dag, bedragen per maand per maand.
# ---------------------------------------------------------------------------
ZIEKTE = "Primaire arbeidsongeschiktheid"
WERKL = "Werkloosheid"

BEDRAGEN = [
    # --- primaire arbeidsongeschiktheid, werknemer ---
    ("ziekte", "WN alleenstaand, maximum bruto daginkomen, maand 2", 179.5442, ZIEKTE, "C34"),
    ("ziekte", "WN alleenstaand, minimum bruto daguitkering, maand 3", 61.77, ZIEKTE, "C48"),
    ("ziekte", "WN alleenstaand, minimum bruto daguitkering, maand 4-6", 61.77, ZIEKTE, "C62"),
    ("ziekte", "WN alleenstaand, minimum bruto daguitkering, maand 7-12", 61.77, ZIEKTE, "C76"),
    ("ziekte", "WN samenwonend, minimum bruto daguitkering, maand 7-12", 52.97, ZIEKTE, "C235"),
    # --- primaire arbeidsongeschiktheid, zelfstandige (forfait per dag, x 26,07 in het werkboek) ---
    ("ziekte", "ZN alleenstaand, forfait per dag", 61.77, ZIEKTE, "C9/26.07"),
    ("ziekte", "ZN samenwonend, forfait per dag", 47.38, ZIEKTE, "C101/26.07"),
    # --- werkloosheid, werknemer ---
    ("werkloosheid", "WN alleenstaand, minimum daguitkering, maand 1-3", 54.21, WERKL, "C26"),
    ("werkloosheid", "WN alleenstaand, minimum daguitkering, maand 4-6", 54.21, WERKL, "C40"),
    ("werkloosheid", "WN alleenstaand, minimum daguitkering, maand 7-12", 54.21, WERKL, "C54"),
    ("werkloosheid", "WN alleenstaand, maximum brutomaandloon, maand 1-6", 3365.16, WERKL, "C25"),
    ("werkloosheid", "WN alleenstaand, maximum brutomaandloon, maand 7-12", 3136.39, WERKL, "C53"),
    ("werkloosheid", "WN samenwonend, minimum daguitkering, maand 1-3", 52.18, WERKL, "C142"),
    ("werkloosheid", "WN samenwonend, minimum daguitkering, maand 4-6", 49.13, WERKL, "C157"),
    ("werkloosheid", "WN samenwonend, minimum daguitkering, maand 7-12", 49.13, WERKL, "C172"),
    ("werkloosheid", "WN samenwonend, maximum brutomaandloon, maand 1-6", 3365.16, WERKL, "C141"),
    ("werkloosheid", "WN samenwonend, maximum brutomaandloon, maand 7-12", 3136.39, WERKL, "C171"),
    # --- overbruggingsrecht, zelfstandige ---
    ("werkloosheid", "ZN alleenstaand, overbruggingsrecht per maand", 1638.26, WERKL, "C12"),
    ("werkloosheid", "ZN samenwonend, overbruggingsrecht per maand", 1638.26, WERKL, "C128"),
]

# Bedrag dat in het werkboek staat maar NIET gebruikt wordt (leesnota E): het overbruggingsrecht
# met gezinslast. De simulaties gebruiken voor beide gezinstypes het bedrag zonder gezinslast,
# omdat de partner werkt.
NIET_GEBRUIKT = [("werkloosheid", "ZN met gezinslast, overbruggingsrecht per maand (niet gebruikt)",
                  None, WERKL, "C69")]

DAGEN = 26.07   # het werkboek rekent forfaits per maand om met 26,07 dagen


def waarde_uit_werkboek(wb, blad, cel):
    """Lees de cel; '<cel>/26.07' betekent: maandbedrag delen door 26,07 om een dagbedrag te krijgen."""
    deel = 1.0
    if "/" in cel:
        cel, noemer = cel.split("/")
        deel = float(noemer)
    return wb[blad][cel].value / deel


def main():
    if not WERKBOEK.exists():
        # Publieke modus: het werkboek is afgeschermde brondata (zie DATA.md). Zonder het
        # werkboek is er niets om tegen te vergelijken, maar de rest van de pijplijn draait wel.
        print(f"{WERKBOEK.name} niet aanwezig (afgeschermde brondata): controle overgeslagen.")
        return 0
    wb = openpyxl.load_workbook(WERKBOEK, data_only=True)

    rijen = []
    for rubriek, omschrijving, tabelwaarde, blad, cel in BEDRAGEN + NIET_GEBRUIKT:
        werkboekwaarde = waarde_uit_werkboek(wb, blad, cel)
        if tabelwaarde is None:
            oordeel = "staat niet in Tabel 7 (bewust)"
            verschil = None
        else:
            verschil = round(werkboekwaarde - tabelwaarde, 4)
            # afronding in de tabel: alles staat op twee decimalen
            oordeel = "gelijk" if abs(verschil) < 0.005 else "VERSCHIL"
        rijen.append(dict(rubriek=rubriek, bedrag=omschrijving, tabel_7=tabelwaarde,
                          werkboek=round(werkboekwaarde, 4), verschil=verschil,
                          blad=blad, cel=cel, oordeel=oordeel))

    df = pd.DataFrame(rijen)
    UIT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(UIT, index=False, float_format="%.4f")

    afwijkend = df[df.oordeel == "VERSCHIL"]
    print(f"Tabel 7: {len(BEDRAGEN)} bedragen vergeleken met het werkboek, "
          f"{len(afwijkend)} verschillen")
    if len(afwijkend):
        print("LET OP: Tabel 7 en het werkboek komen niet overeen:")
        print(afwijkend[["bedrag", "tabel_7", "werkboek", "verschil"]].to_string(index=False))
    print(f"geschreven: {UIT.relative_to(WORTEL)}")
    # We stoppen de pijplijn niet: de melding hierboven en het bestand volstaan.
    return 0


if __name__ == "__main__":
    sys.exit(main())
