"""
Gedeelde instellingen voor de macro-analyse van het UNIZO-rapport.

Dit bestand bevat GEEN berekeningen. Het legt vast:
  - waar alle mappen staan (relatief t.o.v. de root van de repository),
  - welke jaren en basisjaren we gebruiken,
  - een paar kleine hulpfuncties die in meerdere scripts terugkomen.

Alle andere scripts importeren dit bestand met `from common import ...`.
Zo staat elke keuze op precies één plaats.
"""

from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------------
# 1. Mappen
# ---------------------------------------------------------------------------
# __file__ is het pad van dit script: <root>/code/macro/common.py
# .parents[2] gaat twee mappen omhoog: macro -> code -> <root>
ROOT = Path(__file__).resolve().parents[2]

DATA_SOURCES = ROOT / "data" / "sources"      # originele bronbestanden (ongewijzigd)
DATA_RESTRICTED = ROOT / "data" / "restricted"  # niet publiek deelbaar, staat NIET in Git
DATA_RAW = ROOT / "data" / "raw"              # inputreeksen als CSV (overgenomen uit het werkboek)
DATA_PROCESSED = ROOT / "data" / "processed"  # berekende indicatoren
OUT_FIGURES = ROOT / "output" / "figures"
OUT_TABLES = ROOT / "output" / "tables"
OUT_CHECKS = ROOT / "output" / "checks"

# Het werkboek van Willem waaruit de inputreeksen worden overgenomen.
# De datum in de bestandsnaam is de datum van de momentopname (laatst gewijzigd).
WERKBOEK = DATA_SOURCES / "werkboeken" / "macro_analyses_willem_2026-09-16.xlsx"

# ---------------------------------------------------------------------------
# 2. Jaren en basisjaren
# ---------------------------------------------------------------------------
# Populatiegegevens (KSZ) bestaan voor 2003-2023, dus de beroepssolidariteit
# per capita loopt over die periode.
JAREN_BS = list(range(2003, 2024))

# Aandelen in de inkomsten hebben geen populatie of inflatiecorrectie nodig,
# dus de nationale solidariteit kan vroeger beginnen (2000). Ze eindigt wel in
# 2023, net als de beroepssolidariteit, zodat alle reeksen in hetzelfde jaar
# eindigen. Keuze van Wim (21 september 2026): de FOD SZ-cijfers voor 2024 zijn
# ramingen (monitor maart 2025), en een eindjaar dat verschilt tussen de
# indicatoren verwart de lezer.
JAREN_NS = list(range(2000, 2024))

# De volledige FOD SZ-reeks (tot en met 2024) gebruiken we enkel nog in
# 04_reconcile.py, om het oorspronkelijke werkboek en de oorspronkelijke tekst
# (die tot 2024 liepen) te reproduceren. Niet gebruiken voor het rapport.
JAREN_NS_RECONCILIATIE = list(range(2000, 2025))

# Basisjaar voor de index (= 100) van de beroepssolidariteit
BASISJAAR_BS = 2003
# Basisjaar voor de index van de nationale solidariteit
BASISJAAR_NS = 2000
# Prijsniveau waarin reële bedragen worden uitgedrukt (prijzen van 2024)
PRIJSJAAR = 2024


def zorg_voor_mappen() -> None:
    """Maak de outputmappen aan als ze nog niet bestaan."""
    for p in (DATA_RAW, DATA_PROCESSED, OUT_FIGURES, OUT_TABLES, OUT_CHECKS):
        p.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# 3. Hulpfuncties voor evoluties
# ---------------------------------------------------------------------------
# Hier zit de kern van correctie G1 uit de leesnota.
#
# Een index zegt hoe groot een reeks is t.o.v. het basisjaar (basisjaar = 100).
# Stel: index 2019 = 114,9 en index 2020 = 103,3.
#
#   FOUT (oude werkboekformule =S18-R18):  103,3 - 114,9 = -11,6
#        Dat is een verschil in INDEXPUNTEN. Het is alleen gelijk aan een
#        procentuele verandering als het beginjaar zelf het basisjaar is
#        (want dan is de beginwaarde precies 100).
#
#   JUIST:  103,3 / 114,9 - 1 = -10,1%
#        Dat is de RELATIEVE verandering tussen 2019 en 2020.


def relatieve_verandering(reeks: pd.Series, begin: int, eind: int) -> float:
    """Procentuele verandering van `begin` naar `eind`, in procent.

    Werkt voor elke reeks (bedragen, indexen, aandelen, ratio's), omdat een
    relatieve verandering niet afhangt van de schaal.
    """
    return (reeks.loc[eind] / reeks.loc[begin] - 1) * 100


def indexpunt_verschil(index: pd.Series, begin: int, eind: int) -> float:
    """Het verschil in indexpunten, zoals het oude werkboek rekende.

    Alleen bewaard om de oude cijfers te kunnen reproduceren en naast de
    correcte te zetten. Niet gebruiken voor rapportering.
    """
    return index.loc[eind] - index.loc[begin]


def procentpunt_verschil(aandeel: pd.Series, begin: int, eind: int) -> float:
    """Verschil tussen twee aandelen/ratio's in procentpunten.

    Voorbeeld: ratio 64,5% -> 57,2% is -7,3 procentpunt, maar -11,3% relatief.
    """
    return (aandeel.loc[eind] - aandeel.loc[begin]) * 100


def index(reeks: pd.Series, basisjaar: int) -> pd.Series:
    """Zet een reeks om naar een index met basisjaar = 100.

    Het rapport beschrijft een 'kettingmethode' (jaar X / jaar X-1 maal index
    X-1). Die geeft wiskundig exact hetzelfde resultaat als deze directe
    methode (jaar X / basisjaar maal 100), maar is eenvoudiger te controleren.
    """
    return reeks / reeks.loc[basisjaar] * 100
