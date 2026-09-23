"""
Gedeelde instellingen voor de micro-analyses van het UNIZO-rapport (§6.2 en §7).

Dit bestand bevat GEEN analyses. Het legt vast:
  - waar de micro-invoer staat en waar de uitvoer terechtkomt,
  - het inkomensrooster van de simulaties (34 posities),
  - de bijdrageschaal van de zelfstandigen zoals Viren ze toepaste,
  - de functies voor de (gewogen) Kakwani-index.

Alle scripts in code/micro/ importeren dit bestand met `from common_micro import ...`.
Zo staat elke keuze op precies één plaats.
"""

from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# 1. Mappen
# ---------------------------------------------------------------------------
# __file__ = <root>/code/micro/common_micro.py  ->  .parents[2] = <root>
ROOT = Path(__file__).resolve().parents[2]

SRC_MICRO = ROOT / "data" / "sources" / "micro"   # kopie van de micro-uitvoer (Viren/EUROMOD), ongewijzigd
SRC_ABC = ROOT / "data" / "sources" / "abc"       # ABC-verslag 2022/04 (publiek document)
DATA_RAW = ROOT / "data" / "raw"                  # o.a. uitvoer van de Stata-stap (BE-SILC-gewichten)
DATA_RESTRICTED = ROOT / "data" / "restricted"    # NIET in Git (Statbel ADI-histogram)
DATA_PROCESSED = ROOT / "data" / "processed"      # resultaten van de micro-scripts
OUT_CHECKS = ROOT / "output" / "checks"           # controles (reproductie, afwijkingen)

# Micro-invoer
WERKBOEK_MICRO = SRC_MICRO / "unizo_results_final.xlsx"  # 'Unizo Results Final.xlsx' (ingeplakte Viren- en EUROMOD-uitvoer)
UNIZO_DTA = SRC_MICRO / "unizo.dta"                      # bijdragen per roosterpositie (basis Kakwani in het rapport)
PENSIOENCORRECTIE = SRC_MICRO / "correctie_pensioenen.xlsx"  # herberekende pensioenen (blad 'Herberekening pensioenen', 18 september 2026, leesnota J1)

# Pensioenplafond: maximuminkomsten die in de pensioenberekening meetellen, bedragen van
# 1 januari 2024 (RSVZ, cijfers, bedragen en grenzen). Het maximale bruto pensioen onder de
# assumpties van het rapport (volledige loopbaan van 45 jaar, laatste inkomen als gemiddelde,
# alleenstaandentarief) is 60% van deze grens per maand. m05 controleert het correctieblad hierop.
PENSIOENPLAFOND_JAAR = {"WN": 80485.32, "ZN": 75977.52}
PENSIOENTARIEF = 0.60                       # alleenstaandentarief

# Uitvoer van de Stata-stap m00 (draait enkel bij wie toegang heeft tot BE-SILC 2024)
SILC_GEWICHTEN = DATA_RAW / "kakwani_gewichten_eq_besilc2024.csv"
SILC_RESULTATEN = DATA_RAW / "kakwani_resultaten_eq_besilc2024.csv"

# <!-- wijziging: publicatie | publieke afgeleide van de BE-SILC-gewichten, zonder celaantallen -->
# Publieke afgeleide van die gewichten: enkel de som van de steekproefgewichten per positie,
# zonder het aantal waarnemingen per cel. m01 schrijft dit bestand wanneer de Stata-uitvoer
# aanwezig is; zonder BE-SILC-toegang vertrekken de scripts ervan (zie DATA.md).
SILC_GEWICHTEN_PUBLIEK = DATA_RAW / "micro_silc_gewichten.csv"

# Statbel, administratief gestandaardiseerd beschikbaar inkomen 2023 (histogram, niet publiek)
ADI_HISTOGRAM = DATA_RESTRICTED / "statbel_adi_histogram_2023.xlsx"

# ---------------------------------------------------------------------------
# 2. Inkomensrooster van de simulaties
# ---------------------------------------------------------------------------
# Netto beschikbaar maandinkomen (DPI) van het individu in het typegeval.
# Stappen van 250 tot 7.000, van 500 tot 10.000, van 1.000 tot 15.000.
ROOSTER = [1550, 1800, 2000] + list(range(2250, 7001, 250)) + list(range(7500, 10001, 500)) \
          + list(range(11000, 15001, 1000))
assert len(ROOSTER) == 34

# Kolomnamen in unizo.dta en hun betekenis
TYPES = {
    "WN": "Werknemer",
    "ZE": "Eenmanszaak",
    "ZV100VAA": "Vennootschap, 100% loon, met VAA",
    "ZV100": "Vennootschap, 100% loon",
    "ZV75": "Vennootschap, 75% loon",
    "ZV50": "Vennootschap, 50% loon",
    "ZV00": "Vennootschap, 0% loon",
}

# ---------------------------------------------------------------------------
# 3. Bijdrageschaal zelfstandigen zoals toegepast in Viren (leesnota G7 en J7)
# ---------------------------------------------------------------------------
# Viren rekende met grenzen die een factor 1,0304 hoger liggen dan de officiële
# grenzen van 2024 (€72.810,94 en €107.300,29). We gebruiken hier bewust de
# Viren-grenzen, zodat de scenario's vergelijkbaar zijn met de gesimuleerde bijdragen.
TUSSENGRENS_JAAR = 75024.54      # tot hier 20,5%
MAXIMUMGRENS_JAAR = 110562.42    # tot hier 14,16%, daarboven niets (plafond)
MINIMUMDREMPEL_JAAR = 16861.46   # onder dit inkomen geldt de minimumbijdrage
TARIEF_1 = 0.205
TARIEF_2 = 0.1416
BEHEERSKOSTEN = 1.0305           # +3,05% beheerskosten sociaal verzekeringsfonds (niet gedocumenteerd, J7)


def bijdrage_zelfstandige(nbi_maand, tarief_1=TARIEF_1, tarief_2=TARIEF_2, plafond=True):
    """Maandelijkse sociale bijdrage van een zelfstandige in hoofdberoep.

    nbi_maand : netto belastbaar beroepsinkomen per maand (array of getal)
    tarief_2  : tarief tussen tussengrens en maximumgrens (huidig 14,16%)
    plafond   : False = geen maximumgrens, tarief_2 loopt door op het hele inkomen boven de tussengrens

    De minimumbijdrage is niet ingebouwd: op het rooster ligt het laagste netto
    belastbaar inkomen van de eenmanszaak (€19.956/jaar) boven de minimumdrempel.
    Het script m03 controleert dat.
    """
    nbi = np.asarray(nbi_maand, dtype=float)
    t1 = TUSSENGRENS_JAAR / 12
    t3 = MAXIMUMGRENS_JAAR / 12
    schijf_1 = np.minimum(nbi, t1)                      # deel tot de tussengrens
    schijf_2 = np.maximum(nbi - t1, 0)                  # deel boven de tussengrens
    if plafond:
        schijf_2 = np.minimum(schijf_2, t3 - t1)        # afgetopt op de maximumgrens
    return (schijf_1 * tarief_1 + schijf_2 * tarief_2) * BEHEERSKOSTEN


# ---------------------------------------------------------------------------
# 4. Gewogen concentratiecoëfficiënt en Kakwani-index
# ---------------------------------------------------------------------------
# Uitleg in woorden:
#  - Rangschik de posities van laag naar hoog inkomen.
#  - Elke positie krijgt een gewicht w (aandeel van de bevolking op die positie).
#  - De fractionele rang R van een positie = cumulatief aandeel van alle lagere
#    posities + de helft van het eigen aandeel (het "midden" van de groep).
#  - Concentratiecoëfficiënt van v:  C(v) = 2 * som[w * (v - gem_v) * (R - gem_R)] / gem_v
#    Voor v = inkomen zelf is dat de Gini-coëfficiënt.
#  - Kakwani = C(bijdragen) - Gini(inkomen).
#    > 0: bijdragen meer geconcentreerd bij hogere inkomens dan het inkomen zelf (progressief)
#    = 0: proportioneel;  < 0: regressief.
# Dezelfde formule staat in het Stata-programma `kakwani_tabel` (m00); m01 controleert
# dat Python en Stata hetzelfde uitkomen.

def concentratie(v, y, w):
    """Gewogen concentratiecoëfficiënt van v, gerangschikt naar y."""
    v, y, w = (np.asarray(a, dtype=float) for a in (v, y, w))
    orde = np.argsort(y, kind="stable")
    v, y, w = v[orde], y[orde], w[orde] / w[orde].sum()
    R = np.cumsum(w) - w / 2
    gem_v = (w * v).sum()
    gem_R = (w * R).sum()
    return 2 * (w * (v - gem_v) * (R - gem_R)).sum() / gem_v


def kakwani(bijdragen, inkomen, w):
    """Kakwani-index = concentratie(bijdragen) - Gini(inkomen)."""
    return concentratie(bijdragen, inkomen, w) - concentratie(inkomen, inkomen, w)


def gem_ratio(bijdragen, inkomen, w):
    """Gewogen gemiddelde van bijdrage / draagkracht over de posities."""
    b, y, w = (np.asarray(a, dtype=float) for a in (bijdragen, inkomen, w))
    return (w * b / y).sum() / w.sum()


# ---------------------------------------------------------------------------
# 5. Kleine hulpfuncties
# ---------------------------------------------------------------------------
def lees_unizo():
    """unizo.dta: één rij per roosterpositie, gesorteerd op inkomen."""
    d = pd.read_stata(UNIZO_DTA).sort_values("INKOMEN").reset_index(drop=True)
    assert d.INKOMEN.tolist() == ROOSTER, "unizo.dta volgt het rooster niet"
    return d


# <!-- wijziging: publicatie | gewichten uit de Stata-uitvoer of uit de publieke afgeleide -->
def lees_silc_gewichten():
    """BE-SILC-gewichten per roosterpositie: kolommen variant, groep, pos, w.

    Eerst de uitvoer van de Stata-stap m00 (met celaantallen, niet publiek), en als die er
    niet is de publieke afgeleide zonder celaantallen. De kolom w is in beide identiek, dus
    alle resultaten die op w steunen zijn ook zonder BE-SILC-toegang reproduceerbaar.
    Geeft None als geen van beide bestanden aanwezig is.
    """
    if SILC_GEWICHTEN.exists():
        return pd.read_csv(SILC_GEWICHTEN, sep=";")[["variant", "groep", "pos", "w"]]
    if SILC_GEWICHTEN_PUBLIEK.exists():
        return pd.read_csv(SILC_GEWICHTEN_PUBLIEK, float_precision="round_trip")
    return None


def zorg_voor_mappen():
    for p in (DATA_PROCESSED, OUT_CHECKS):
        p.mkdir(parents=True, exist_ok=True)
