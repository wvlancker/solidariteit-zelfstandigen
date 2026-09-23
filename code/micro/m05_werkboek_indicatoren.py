"""
Stap m05: indicatoren van het microdeel (§6.2 en Bijlage 7) opnieuw opbouwen uit het werkboek

Waarom?
-------
De figuren en tabellen van §6.2 stonden als Excel-grafieken en overgetypte tabellen in
het werkboek 'Unizo Results Final.xlsx' (blad 'Julie HS & VS'). Om ze in dezelfde
huisstijl en even controleerbaar te maken als het macrodeel, doen we hier drie dingen:

1. OVERNAME. We lezen enkel de INVOER van de indicatoren uit het werkboek: de gesimuleerde
   sociale bijdragen, de netto uitkeringen, de referentiebudgetten, het loon van de partner
   en het Groeipakket. Dat zijn de waarden die uit Viren en EUROMOD komen (ingeplakt in de
   rekenbladen en via formules naar 'Julie HS & VS' gehaald). Formules nemen we niet over.
       -> data/raw/micro_werkboek_invoer.csv (één rij per reeks en inkomenspositie, met de cel)

2. HERBEREKENING. Alle indicatoren worden hier opnieuw berekend, met dezelfde definities
   als in §5.2.2:
       bijdrage / draagkracht     = sociale bijdrage / netto beschikbaar maandinkomen (positie)
       vervangingsgraad           = netto uitkering / netto beschikbaar maandinkomen vóór het risico
       equivalentiegraad          = sociale bijdrage / netto uitkering
       garantiegraad (alleen)     = netto uitkering / referentiebudget alleenstaande
       garantiegraad (koppel)     = (uitkering + netto loon partner + Groeipakket) / referentiebudget koppel
   Per indicator ook het gemiddelde over de 34 posities en de variatiecoëfficiënt
   (standaardafwijking / gemiddelde, populatieversie zoals in Tabel 9 en 10).

3. CONTROLE EN CORRECTIE.
   a. Controle: elke herberekende rij moet exact (op afrondingsfouten na) gelijk zijn aan de
      rij die het werkboek zelf berekende. Zo weten we dat de overname volledig is.
          -> output/checks/micro_werkboek_reproductie.csv
   b. Correcties die met de bestaande data kunnen (beslissing 17 september 2026). Ze worden
      pas NA de controle toegepast en zijn elk apart gedocumenteerd (CORRECTIES hieronder,
      elk met reden en gevolg):
          J8  werkloosheid werknemer alleenstaande, maand 4-6, positie €2.500: de formule in
              het werkboek deelde door 26,7 in plaats van 26,07 dagen, en nam het maximale
              maandloon als basis. Bij €2.500 ligt het brutoloon (€3.842,77) boven het
              maximum, dus de uitkering is het maximum, zoals op alle hogere posities en
              zoals in het blok voor samenwonenden. Correctie: de netto uitkering van €2.750.

          J1  pensioenen: het oorspronkelijke blad 'Pensioenen' plafonneerde het PENSIOEN op de
              loongrens, terwijl de loongrens op het LOON hoort vóór de 60% wordt toegepast. Het
              maximale bruto pensioen was daardoor €6.707 (werknemer) en €6.331 (zelfstandige) in
              plaats van €4.024 en €3.799. Julie Vinck bezorgde op 18 september 2026 een nieuw blad
              'Herberekening pensioenen' (met nieuwe netto bedragen uit EUROMOD). Dat blad vervangt
              hier de zes rijen netto pensioen; de plafond- en minimumregel wordt cel per cel
              gecontroleerd (zie lees_pensioencorrectie).

          J2  zelfstandige samenwonend bij ziekte (beslissing 22 september 2026): de netto uitkering
              stond op €1.309,29 terwijl het bruto forfait €1.235,20 bedraagt (€47,38 per dag x 26,07).
              Netto boven bruto komt doordat EUROMOD hier de bijstandsbodem laat staan; bij de andere
              rijen voor samenwonenden staat die er niet. Er is geen bijdrage en geen belasting op deze
              uitkering, dus netto = bruto. Zie CORRECTIES_VAST.

   BEWUST NIET gecorrigeerd:
       - de bijstandsbodem in de netto uitkeringen van de WERKNEMER (bijvoorbeeld alleenstaand,
         maand 2, positie €1.550 en €1.800). Die hoort bij het stelsel dat gesimuleerd wordt.

Uitvoer
-------
  data/raw/micro_werkboek_invoer.csv          invoer uit het werkboek, met celverwijzing
  data/raw/micro_pensioenen_correctie.csv     bruto en netto pensioen per type en positie (nieuw blad, J1)
  data/processed/micro_indicatoren.csv        indicator per type en positie (na correctie)
  data/processed/micro_samenvatting.csv       gemiddelde en variatiecoëfficiënt per reeks (na correctie)
  data/processed/micro_tabellen.csv           de cellen van Tabel 8, 9, 10, B7.1 en B7.2
  output/checks/micro_werkboek_reproductie.csv  herberekening vóór correctie vs. werkboek
  output/checks/micro_pensioenen_correctie.csv  oud vs. nieuw netto pensioen per type en positie (J1)

Uitvoeren:  python code/micro/m05_werkboek_indicatoren.py
"""

import numpy as np
import openpyxl
import pandas as pd
from openpyxl.utils import get_column_letter

from common_micro import (DATA_PROCESSED, DATA_RAW, OUT_CHECKS, PENSIOENCORRECTIE, PENSIOENPLAFOND_JAAR,
                          PENSIOENTARIEF, ROOSTER, WERKBOEK_MICRO, zorg_voor_mappen)

BLAD = "Julie HS & VS"
KOLOMMEN = list(range(2, 36))          # kolom B (2) tot AI (35): de 34 inkomensposities
assert len(KOLOMMEN) == len(ROOSTER)

# ---------------------------------------------------------------------------
# 1. Waar staat de invoer in het blad 'Julie HS & VS'?
# ---------------------------------------------------------------------------
# Elke regel: (reeks, gezin, risico, type, maand, rij).
#   reeks  : bijdrage | uitkering | budget | partnerloon | groeipakket
#   gezin  : alleen (alleenstaande) | koppel (samenwonend, 2 kinderen) |
#            koppel_laag / koppel_gem (partner met laag of gemiddeld loon; enkel partnerloon en Groeipakket)
#   type   : WN werknemer, ZE eenmanszaak, ZV100VAA/ZV100/ZV75/ZV50/ZV00 vennootschap met x% loon,
#            ZS = zelfstandige ongeacht rechtsvorm (forfaitaire uitkering, gelijk voor iedereen)
#   maand  : uitkeringsmaand van de werknemer ('-' als niet van toepassing)
#
# De sociale bijdragen hangen niet af van het gezinstype: de rijen voor koppels (19-47) zijn
# identiek aan die voor alleenstaanden (4-17). Dat controleren we hieronder ook.
INVOER = [
    # --- sociale bijdragen per maand (Viren voor zelfstandigen, EUROMOD voor werknemers) ---
    ("bijdrage", "-", "-", "ZV100VAA", "-", 4),
    ("bijdrage", "-", "-", "ZV100", "-", 6),
    ("bijdrage", "-", "-", "ZV75", "-", 8),
    ("bijdrage", "-", "-", "ZV50", "-", 10),
    ("bijdrage", "-", "-", "ZV00", "-", 12),
    ("bijdrage", "-", "-", "ZE", "-", 14),
    ("bijdrage", "-", "-", "WN", "-", 16),
    # --- netto uitkering primaire arbeidsongeschiktheid ---
    ("uitkering", "alleen", "ziekte", "ZS", "-", 52),
    ("uitkering", "alleen", "ziekte", "WN", "1", 53),       # gewaarborgd loon (niet gebruikt in figuren)
    ("uitkering", "alleen", "ziekte", "WN", "2", 54),
    ("uitkering", "alleen", "ziekte", "WN", "3", 55),
    ("uitkering", "alleen", "ziekte", "WN", "4-6", 56),     # maand 3 = maand 4-6 (opmerking in het werkboek)
    ("uitkering", "alleen", "ziekte", "WN", "7-12", 57),
    ("uitkering", "koppel", "ziekte", "ZS", "-", 59),
    ("uitkering", "koppel", "ziekte", "WN", "1", 60),
    ("uitkering", "koppel", "ziekte", "WN", "2", 61),
    ("uitkering", "koppel", "ziekte", "WN", "3", 62),
    ("uitkering", "koppel", "ziekte", "WN", "4-6", 63),
    ("uitkering", "koppel", "ziekte", "WN", "7-12", 64),
    # --- netto uitkering werkloosheid (werknemer) / overbruggingsrecht (zelfstandige) ---
    ("uitkering", "alleen", "werkloosheid", "ZS", "-", 68),
    ("uitkering", "alleen", "werkloosheid", "WN", "1-3", 69),
    ("uitkering", "alleen", "werkloosheid", "WN", "4-6", 70),
    ("uitkering", "alleen", "werkloosheid", "WN", "7-12", 71),
    ("uitkering", "koppel", "werkloosheid", "ZS", "-", 73),
    ("uitkering", "koppel", "werkloosheid", "WN", "1-3", 74),
    ("uitkering", "koppel", "werkloosheid", "WN", "4-6", 75),
    ("uitkering", "koppel", "werkloosheid", "WN", "7-12", 76),
    # --- netto pensioen (gelijk voor alleenstaanden en koppels: geen gezinspensioen) ---
    ("uitkering", "-", "pensioen", "ZV100", "-", 78),
    ("uitkering", "-", "pensioen", "ZV75", "-", 79),
    ("uitkering", "-", "pensioen", "ZV50", "-", 80),
    ("uitkering", "-", "pensioen", "ZV00", "-", 81),
    ("uitkering", "-", "pensioen", "ZE", "-", 82),
    ("uitkering", "-", "pensioen", "WN", "-", 83),
    # --- Groeipakket (2 kinderen van 2 en 4 jaar), hangt af van het gezinsinkomen ---
    ("groeipakket", "koppel_laag", "-", "ZV100VAA", "-", 178),
    ("groeipakket", "koppel_laag", "-", "ZV100", "-", 179),
    ("groeipakket", "koppel_laag", "-", "ZV75", "-", 180),
    ("groeipakket", "koppel_laag", "-", "ZV50", "-", 181),
    ("groeipakket", "koppel_laag", "-", "ZV00", "-", 182),
    ("groeipakket", "koppel_laag", "-", "ZE", "-", 183),
    ("groeipakket", "koppel_laag", "-", "WN", "-", 184),
    ("groeipakket", "koppel_gem", "-", "ZV100VAA", "-", 186),
    ("groeipakket", "koppel_gem", "-", "ZV100", "-", 187),
    ("groeipakket", "koppel_gem", "-", "ZV75", "-", 188),
    ("groeipakket", "koppel_gem", "-", "ZV50", "-", 189),
    ("groeipakket", "koppel_gem", "-", "ZV00", "-", 190),
    ("groeipakket", "koppel_gem", "-", "ZE", "-", 191),
    ("groeipakket", "koppel_gem", "-", "WN", "-", 192),
]
# Eén getal, geen reeks over de posities: (reeks, gezin, cel)
CONSTANTEN = [
    ("budget", "alleen", "B175"),         # referentiebudget private huur, alleenstaande niet-werkende vrouw, 2024Q2
    ("budget", "koppel", "B176"),         # referentiebudget private huur, koppel met 2 kinderen (2 en 4 jaar)
    ("partnerloon", "koppel_laag", "B199"),   # netto maandloon partner, laag brutoloon (€3.065,07)
    ("partnerloon", "koppel_gem", "B208"),    # netto maandloon partner, gemiddeld brutoloon (€4.574,73)
]

ZELF_TYPES = ["ZV100VAA", "ZV100", "ZV75", "ZV50", "ZV00", "ZE"]

# ---------------------------------------------------------------------------
# 2. Welke rij van het werkboek hoort bij welke herberekende indicator? (enkel voor de controle)
# ---------------------------------------------------------------------------
# (indicator, gezin, risico, type, maand) -> rij in 'Julie HS & VS'
CONTROLE = {}
for t, r in zip(["ZV100VAA", "ZV100", "ZV75", "ZV50", "ZV00", "ZE", "WN"], [5, 7, 9, 11, 13, 15, 17]):
    CONTROLE[("bijdrage_ratio", "-", "-", t, "-")] = r
for gezin, start in (("alleen", 87), ("koppel", 92)):
    CONTROLE[("vervangingsgraad", gezin, "ziekte", "ZS", "-")] = start
    for i, m in enumerate(["2", "3-6", "7-12"], start=1):
        CONTROLE[("vervangingsgraad", gezin, "ziekte", "WN", m)] = start + i
for gezin, start in (("alleen", 98), ("koppel", 103)):
    CONTROLE[("vervangingsgraad", gezin, "werkloosheid", "ZS", "-")] = start
    for i, m in enumerate(["1-3", "4-6", "7-12"], start=1):
        CONTROLE[("vervangingsgraad", gezin, "werkloosheid", "WN", m)] = start + i
for i, t in enumerate(["ZV100", "ZV75", "ZV50", "ZV00", "ZE", "WN"]):
    CONTROLE[("vervangingsgraad", "-", "pensioen", t, "-")] = 108 + i
for gezin, start, risico, maanden in (("alleen", 125, "ziekte", ["2", "3-6", "7-12"]),
                                      ("koppel", 135, "ziekte", ["2", "3-6", "7-12"]),
                                      ("alleen", 146, "werkloosheid", ["1-3", "4-6", "7-12"]),
                                      ("koppel", 156, "werkloosheid", ["1-3", "4-6", "7-12"])):
    for i, t in enumerate(ZELF_TYPES):
        CONTROLE[("equivalentiegraad", gezin, risico, t, "-")] = start + i
    for i, m in enumerate(maanden):
        CONTROLE[("equivalentiegraad", gezin, risico, "WN", m)] = start + 6 + i
for i, t in enumerate(["ZV100", "ZV75", "ZV50", "ZV00", "ZE", "WN"]):
    CONTROLE[("equivalentiegraad", "-", "pensioen", t, "-")] = 167 + i
CONTROLE[("garantiegraad", "alleen", "ziekte", "ZS", "-")] = 195
for i, m in enumerate(["2", "3-6", "7-12"]):
    CONTROLE[("garantiegraad", "alleen", "ziekte", "WN", m)] = 196 + i
CONTROLE[("garantiegraad", "alleen", "werkloosheid", "ZS", "-")] = 218
for i, m in enumerate(["1-3", "4-6", "7-12"]):
    CONTROLE[("garantiegraad", "alleen", "werkloosheid", "WN", m)] = 219 + i
for i, t in enumerate(["ZV100", "ZV75", "ZV50", "ZV00", "ZE", "WN"]):
    CONTROLE[("garantiegraad", "-", "pensioen", t, "-")] = 239 + i
# Koppels, partner met laag loon (Bijlage 7). Het werkboek toont voor 100% loon enkel 'met VAA'.
for i, t in enumerate(["ZV100VAA", "ZV75", "ZV50", "ZV00", "ZE"]):
    CONTROLE[("garantiegraad", "koppel_laag", "ziekte", t, "-")] = 200 + i
for i, m in enumerate(["2", "3-6", "7-12"]):
    CONTROLE[("garantiegraad", "koppel_laag", "ziekte", "WN", m)] = 205 + i
for i, t in enumerate(["ZV100VAA", "ZV50", "ZV00", "ZE"]):
    CONTROLE[("garantiegraad", "koppel_laag", "werkloosheid", t, "-")] = 223 + i
for i, m in enumerate(["1-3", "4-6", "7-12"]):
    CONTROLE[("garantiegraad", "koppel_laag", "werkloosheid", "WN", m)] = 227 + i
for i, t in enumerate(["ZV100VAA", "ZV50", "ZV00", "ZE"]):
    CONTROLE[("garantiegraad", "koppel_gem", "ziekte", t, "-")] = 209 + i
    CONTROLE[("garantiegraad", "koppel_gem", "werkloosheid", t, "-")] = 231 + i
for i, m in enumerate(["2", "3-6", "7-12"]):
    CONTROLE[("garantiegraad", "koppel_gem", "ziekte", "WN", m)] = 213 + i
for i, m in enumerate(["1-3", "4-6", "7-12"]):
    CONTROLE[("garantiegraad", "koppel_gem", "werkloosheid", "WN", m)] = 235 + i

# ---------------------------------------------------------------------------
# 3. Correcties (na de controle), elk met reden.
# ---------------------------------------------------------------------------
# (reeks, gezin, risico, type, maand, positie, nieuwe waarde = waarde van deze positie, code, reden)
CORRECTIES = [
    ("uitkering", "alleen", "werkloosheid", "WN", "4-6", 2500, 2750, "J8",
     "Formule deelde door 26,7 i.p.v. 26,07 dagen; brutoloon ligt boven het maximum, dus maximale uitkering "
     "zoals op €2.750 en hoger (en zoals in het blok samenwonenden)."),
]

# wijziging: correctie | 22 september 2026, beslissing Wim: J2 wordt alsnog gecorrigeerd.
# Correcties die de hele rij (alle 34 posities) op één vaste waarde zetten.
# (reeks, gezin, risico, type, maand, nieuwe waarde, code, reden)
CORRECTIES_VAST = [
    ("uitkering", "koppel", "ziekte", "ZS", "-", 47.38 * 26.07, "J2",
     "De netto uitkering van de samenwonende zelfstandige in primaire arbeidsongeschiktheid stond in het "
     "werkboek ('Primaire arbeidsongeschiktheid'!C100) op €1.309,29, terwijl het bruto forfait €1.235,20 is "
     "(€47,38 per dag x 26,07 dagen, blad rij 101). Die €1.309,29 is de bijstandsbodem die EUROMOD toevoegt; "
     "bij de andere rijen voor samenwonenden is die bodem niet blijven staan. Op deze uitkering is geen "
     "sociale bijdrage en geen personenbelasting verschuldigd (blad rijen 102 en 103), dus netto = bruto."),
]


def lees_werkboek():
    """Lees de invoer (waarden, geen formules) uit het blad 'Julie HS & VS'."""
    wb = openpyxl.load_workbook(WERKBOEK_MICRO, data_only=True)   # data_only: de laatst berekende waarden
    ws = wb[BLAD]

    # Het rooster in rij 3 moet het rooster uit common_micro zijn
    rooster = [ws.cell(3, k).value for k in KOLOMMEN]
    assert rooster == ROOSTER, f"rooster in rij 3 wijkt af: {rooster}"

    # Bijdragen van koppels identiek aan die van alleenstaanden?
    for r_alleen, r_koppel in zip([4, 6, 8, 10, 12, 14, 16], [19, 21, 23, 25, 27, 29, 31]):
        verschil = max(abs(ws.cell(r_alleen, k).value - ws.cell(r_koppel, k).value) for k in KOLOMMEN)
        assert verschil < 1e-9, f"bijdragen koppel (rij {r_koppel}) wijken af van alleenstaande (rij {r_alleen})"

    rijen = []
    for reeks, gezin, risico, typ, maand, r in INVOER:
        for k, positie in zip(KOLOMMEN, ROOSTER):
            rijen.append(dict(reeks=reeks, gezin=gezin, risico=risico, type=typ, maand=maand, positie=positie,
                              waarde=float(ws.cell(r, k).value), cel=f"'{BLAD}'!{get_column_letter(k)}{r}"))
    for reeks, gezin, cel in CONSTANTEN:
        rijen.append(dict(reeks=reeks, gezin=gezin, risico="-", type="-", maand="-", positie=np.nan,
                          waarde=float(ws[cel].value), cel=f"'{BLAD}'!{cel}"))
    invoer = pd.DataFrame(rijen)

    # De rijen die het werkboek zelf berekende, om straks mee te vergelijken
    werkboek = {sleutel: np.array([float(ws.cell(r, k).value) for k in KOLOMMEN]) for sleutel, r in CONTROLE.items()}
    return invoer, werkboek


# ---------------------------------------------------------------------------
# 3b. Het correctieblad voor de pensioenen (leesnota J1)
# ---------------------------------------------------------------------------
# Blad 'Herberekening pensioenen' in data/sources/micro/correctie_pensioenen.xlsx.
# Per type één blok van acht rijen; de kolommen C tot AJ zijn de 34 posities.
#   (type, rij met de positie, rij 60% van het inkomen, rij minimum, rij maximum, rij gederfd bruto, rij netto)
PENS_BLOKKEN = [
    ("ZV100", 10, 12, 13, 14, 15, 16, 17, 18),
    ("ZV75", 24, 26, 27, 28, 29, 30, 31, 32),
    ("ZV50", 38, 40, 41, 42, 43, 44, 45, 46),
    ("ZV00", 52, 54, 55, 56, 57, 58, 59, 60),
    ("ZE", 68, 70, 71, 72, 73, 74, 75, 76),
    ("WN", 84, 86, 87, 88, 89, 90, 91, 92),
]
PENS_BLAD = "Herberekening pensioenen"
PENS_KOLOMMEN = list(range(3, 37))     # kolom C (3) tot AJ (36)
# Inhoudingen op het pensioen die in het netto verwerkt zitten maar niet apart in het blad staan
# (de rij 'Sociale bijdrage' in het blad staat op 0): de ZIV-bijdrage van 3,55% en de
# solidariteitsbijdrage van hoogstens 2%, samen hoogstens 5,55%, met vrijstelling en een
# ingroeizone bij de laagste pensioenen. Terug te rekenen als bruto min belasting min netto; we
# controleren enkel dat het percentage tussen 0 en 5,55 ligt en stijgt met het pensioen.
PENS_INHOUDING_MAX = 0.0555


def lees_pensioencorrectie():
    """Nieuwe bruto en netto pensioenen uit het correctieblad, met controle van de rekenregel.

    Controles (elke afwijking stopt het script):
      1. het rooster in het correctieblad is hetzelfde als in het werkboek;
      2. het gederfde bruto pensioen is precies min(max(60% van het inkomen, minimum), maximum);
      3. het maximum is het pensioenplafond per maand maal 60% (dus het plafond op het INKOMEN, niet
         op het pensioen: dat is de kern van J1), met de plafonds van 1 januari 2024 uit common_micro;
      4. de impliciete inhouding (bruto min personenbelasting min netto) ligt tussen 0 en 5,55% van
         het bruto pensioen en stijgt met het pensioen. Het percentage zelf schrijven we weg.
    """
    wb = openpyxl.load_workbook(PENSIOENCORRECTIE, data_only=True)
    ws = wb[PENS_BLAD]

    minimum_maand = float(ws["I3"].value)                      # minimumpensioen alleenstaande, per maand
    grens_zn, grens_wn = float(ws["H4"].value), float(ws["H5"].value)   # pensioenplafonds per jaar
    # De plafonds moeten die van 1 januari 2024 zijn (RSVZ, bevestigd 18 september 2026).
    for label, grens in (("ZN", grens_zn), ("WN", grens_wn)):
        verwacht = PENSIOENPLAFOND_JAAR[label]
        assert abs(grens - verwacht) < 0.01, \
            f"pensioenplafond {label} in het blad is €{grens:,.2f}, verwacht €{verwacht:,.2f} (RSVZ, 1 januari 2024)"
    max_zn, max_wn = grens_zn / 12 * PENSIOENTARIEF, grens_wn / 12 * PENSIOENTARIEF

    rijen = []
    for typ, r_pos, r_60, r_min, r_max, r_ged, r_netto, r_sb, r_pb in PENS_BLOKKEN:
        rooster = [ws.cell(r_pos, k).value for k in PENS_KOLOMMEN]
        assert rooster == ROOSTER, f"rooster van blok {typ} wijkt af: {rooster}"
        verwacht_max = max_wn if typ == "WN" else max_zn
        for k, positie in zip(PENS_KOLOMMEN, ROOSTER):
            p60 = float(ws.cell(r_60, k).value)
            mn, mx = float(ws.cell(r_min, k).value), float(ws.cell(r_max, k).value)
            bruto, netto = float(ws.cell(r_ged, k).value), float(ws.cell(r_netto, k).value)
            pb = float(ws.cell(r_pb, k).value)
            assert abs(mn - minimum_maand) < 0.01, f"{typ} €{positie}: minimum {mn} wijkt af"
            assert abs(mx - verwacht_max) < 0.01, f"{typ} €{positie}: maximum {mx} is niet 60% van de loongrens"
            assert abs(bruto - min(max(p60, mn), mx)) < 0.01, f"{typ} €{positie}: bruto pensioen volgt de regel niet"
            inhouding = bruto - pb - netto      # ZIV- en solidariteitsbijdrage, niet apart in het blad
            rijen.append(dict(type=typ, positie=positie, bruto_60pct=p60, minimum=mn, maximum=mx,
                              bruto=bruto, personenbelasting=pb, netto=netto, inhouding=inhouding,
                              inhouding_pct=100 * inhouding / bruto,
                              bindend=("minimum" if bruto <= mn + 0.01 else "maximum" if bruto >= mx - 0.01 else "-")))
    pens = pd.DataFrame(rijen)
    assert pens.inhouding_pct.between(-0.01, 100 * PENS_INHOUDING_MAX + 0.01).all(), \
        f"impliciete inhouding buiten [0; 5,55%]:\n{pens[~pens.inhouding_pct.between(-0.01, 5.56)]}"
    for typ in pens.type.unique():                # stijgt met het pensioen (vrijstelling onderaan)
        rij = pens[pens.type == typ].sort_values("positie").inhouding_pct.to_numpy()
        assert (np.diff(rij) > -0.01).all(), f"inhouding daalt bij {typ}"
    print(f"correctieblad pensioenen: regel gecontroleerd voor {len(pens)} cellen "
          f"(minimum €{minimum_maand:,.2f}, maximum €{max_zn:,.2f} ZN / €{max_wn:,.2f} WN)")
    return pens


def bereken(invoer: pd.DataFrame) -> dict:
    """Alle indicatoren uit de invoer. Resultaat: {(indicator, gezin, risico, type, maand): array(34)}."""

    def reeks(reeks, gezin="-", risico="-", typ="-", maand="-"):
        s = invoer[(invoer.reeks == reeks) & (invoer.gezin == gezin) & (invoer.risico == risico)
                   & (invoer.type == typ) & (invoer.maand == maand)].sort_values("positie")
        assert len(s) == 34, (reeks, gezin, risico, typ, maand)
        return s.waarde.to_numpy()

    def constante(reeks, gezin):
        return float(invoer[(invoer.reeks == reeks) & (invoer.gezin == gezin)].waarde.iloc[0])

    nbi = np.array(ROOSTER, dtype=float)    # netto beschikbaar maandinkomen vóór het risico = de positie
    uit = {}

    # (a) bijdrage / draagkracht
    for t in ZELF_TYPES + ["WN"]:
        uit[("bijdrage_ratio", "-", "-", t, "-")] = reeks("bijdrage", typ=t) / nbi

    # (b) vervangingsgraad = uitkering / netto beschikbaar inkomen vóór het risico
    #     Werknemer ziekte: 'maand 3-6' gebruikt de uitkering van maand 4-6 (maand 3 is daaraan gelijk).
    ziekte_maanden = {"2": "2", "3-6": "4-6", "7-12": "7-12"}
    for gezin in ("alleen", "koppel"):
        uit[("vervangingsgraad", gezin, "ziekte", "ZS", "-")] = reeks("uitkering", gezin, "ziekte", "ZS") / nbi
        for label, bron in ziekte_maanden.items():
            uit[("vervangingsgraad", gezin, "ziekte", "WN", label)] = reeks("uitkering", gezin, "ziekte", "WN", bron) / nbi
        uit[("vervangingsgraad", gezin, "werkloosheid", "ZS", "-")] = reeks("uitkering", gezin, "werkloosheid", "ZS") / nbi
        for m in ("1-3", "4-6", "7-12"):
            uit[("vervangingsgraad", gezin, "werkloosheid", "WN", m)] = reeks("uitkering", gezin, "werkloosheid", "WN", m) / nbi
    for t in ["ZV100", "ZV75", "ZV50", "ZV00", "ZE", "WN"]:
        uit[("vervangingsgraad", "-", "pensioen", t, "-")] = reeks("uitkering", "-", "pensioen", t) / nbi

    # (c) equivalentiegraad = bijdrage / uitkering
    #     Zelfstandigen bij ziekte en werkloosheid: dezelfde forfaitaire uitkering voor alle rechtsvormen.
    for gezin in ("alleen", "koppel"):
        for risico, maanden in (("ziekte", ziekte_maanden), ("werkloosheid", {m: m for m in ("1-3", "4-6", "7-12")})):
            u_zs = reeks("uitkering", gezin, risico, "ZS")
            for t in ZELF_TYPES:
                uit[("equivalentiegraad", gezin, risico, t, "-")] = reeks("bijdrage", typ=t) / u_zs
            for label, bron in maanden.items():
                uit[("equivalentiegraad", gezin, risico, "WN", label)] = \
                    reeks("bijdrage", typ="WN") / reeks("uitkering", gezin, risico, "WN", bron)
    for t in ["ZV100", "ZV75", "ZV50", "ZV00", "ZE", "WN"]:
        uit[("equivalentiegraad", "-", "pensioen", t, "-")] = reeks("bijdrage", typ=t) / reeks("uitkering", "-", "pensioen", t)

    # (d) garantiegraad
    b_alleen, b_koppel = constante("budget", "alleen"), constante("budget", "koppel")
    uit[("garantiegraad", "alleen", "ziekte", "ZS", "-")] = reeks("uitkering", "alleen", "ziekte", "ZS") / b_alleen
    for label, bron in ziekte_maanden.items():
        uit[("garantiegraad", "alleen", "ziekte", "WN", label)] = reeks("uitkering", "alleen", "ziekte", "WN", bron) / b_alleen
    uit[("garantiegraad", "alleen", "werkloosheid", "ZS", "-")] = reeks("uitkering", "alleen", "werkloosheid", "ZS") / b_alleen
    for m in ("1-3", "4-6", "7-12"):
        uit[("garantiegraad", "alleen", "werkloosheid", "WN", m)] = reeks("uitkering", "alleen", "werkloosheid", "WN", m) / b_alleen
    for t in ["ZV100", "ZV75", "ZV50", "ZV00", "ZE", "WN"]:
        uit[("garantiegraad", "-", "pensioen", t, "-")] = reeks("uitkering", "-", "pensioen", t) / b_alleen

    # Koppels: gezinsinkomen tijdens het risico = uitkering als samenwonende + netto loon partner + Groeipakket.
    # Het Groeipakket hangt af van het type (via het gezinsinkomen vóór het risico, zo staat het in het werkboek).
    for partner in ("koppel_laag", "koppel_gem"):
        loon = constante("partnerloon", partner)
        for risico, maanden in (("ziekte", ziekte_maanden), ("werkloosheid", {m: m for m in ("1-3", "4-6", "7-12")})):
            u_zs = reeks("uitkering", "koppel", risico, "ZS")
            for t in ZELF_TYPES:
                uit[("garantiegraad", partner, risico, t, "-")] = (u_zs + loon + reeks("groeipakket", partner, typ=t)) / b_koppel
            for label, bron in maanden.items():
                uit[("garantiegraad", partner, risico, "WN", label)] = \
                    (reeks("uitkering", "koppel", risico, "WN", bron) + loon + reeks("groeipakket", partner, typ="WN")) / b_koppel
    return uit


def samenvatting(uit: dict) -> pd.DataFrame:
    """Gemiddelde en variatiecoëfficiënt (populatiestandaardafwijking / gemiddelde) per reeks."""
    rijen = []
    for (ind, gezin, risico, t, m), v in uit.items():
        gem = v.mean()
        rijen.append(dict(indicator=ind, gezin=gezin, risico=risico, type=t, maand=m, gemiddelde=gem,
                          vc=v.std(ddof=0) / gem if gem != 0 else np.nan, minimum=v.min(), maximum=v.max()))
    return pd.DataFrame(rijen)


def lang(uit: dict) -> pd.DataFrame:
    rijen = []
    for (ind, gezin, risico, t, m), v in uit.items():
        for p, w in zip(ROOSTER, v):
            rijen.append(dict(indicator=ind, gezin=gezin, risico=risico, type=t, maand=m, positie=p, waarde=w))
    return pd.DataFrame(rijen)


INVOER_PUBLIEK = DATA_RAW / "micro_werkboek_invoer.csv"
PENS_PUBLIEK = DATA_RAW / "micro_pensioenen_correctie.csv"


def main():
    # wijziging: nieuw | 23 september 2026, publicatie op GitHub. De werkboeken met de uitvoer van
    # Viren en EUROMOD gaan niet mee naar de publieke repository; de gesimuleerde bedragen per
    # inkomenspositie die eruit gehaald worden wel. Staat het werkboek er, dan lezen we het uit en
    # schrijven we die bedragen weg (INVOER_PUBLIEK, PENS_PUBLIEK) en doen we de reproductiecontrole.
    # Staat het er niet, dan vertrekken we van die twee bestanden. De correcties, de indicatoren en
    # alle tabellen komen er identiek uit; enkel de reproductiecontrole tegen het werkboek vervalt,
    # want die vergelijkt met formules die in het werkboek zelf staan. Zie DATA.md.
    zorg_voor_mappen()
    uit_werkboek = WERKBOEK_MICRO.exists()
    if not uit_werkboek and not INVOER_PUBLIEK.exists():
        print(f"{WERKBOEK_MICRO.name} en {INVOER_PUBLIEK.name} ontbreken allebei: stap overgeslagen.")
        raise SystemExit(0)

    if uit_werkboek:
        invoer, werkboek = lees_werkboek()
        invoer.to_csv(INVOER_PUBLIEK, index=False, float_format="%.17g")
        print(f"geschreven: data/raw/micro_werkboek_invoer.csv ({len(invoer)} waarden)")

        # --- controle: herberekening zonder correcties = werkboek ---
        uit = bereken(invoer)
        controle = []
        for sleutel, rij in CONTROLE.items():
            verschil = np.abs(uit[sleutel] - werkboek[sleutel]).max()
            controle.append(dict(indicator=sleutel[0], gezin=sleutel[1], risico=sleutel[2], type=sleutel[3],
                                 maand=sleutel[4], rij_werkboek=rij, max_abs_verschil=verschil))
        controle = pd.DataFrame(controle)
        controle.to_csv(OUT_CHECKS / "micro_werkboek_reproductie.csv", index=False, float_format="%.3g")
        slecht = controle[controle.max_abs_verschil > 1e-9]
        print(f"controle: {len(controle)} rijen van het werkboek herberekend, grootste verschil "
              f"{controle.max_abs_verschil.max():.2g}")
        if len(slecht):
            raise AssertionError(f"herberekening wijkt af van het werkboek:\n{slecht}")
    else:
        invoer = pd.read_csv(INVOER_PUBLIEK, dtype={"maand": str, "gezin": str, "risico": str, "type": str},
                             float_precision="round_trip")
        print(f"invoer uit {INVOER_PUBLIEK.name} ({len(invoer)} waarden); werkboek niet aanwezig, "
              "reproductiecontrole overgeslagen")

    # --- correcties toepassen op de invoer, dan opnieuw berekenen ---
    gecorrigeerd = invoer.copy()
    for reeks, gezin, risico, typ, maand, positie, bron_positie, code, reden in CORRECTIES:
        sel = ((gecorrigeerd.reeks == reeks) & (gecorrigeerd.gezin == gezin) & (gecorrigeerd.risico == risico)
               & (gecorrigeerd.type == typ) & (gecorrigeerd.maand == maand))
        oud = gecorrigeerd.loc[sel & (gecorrigeerd.positie == positie), "waarde"].iloc[0]
        nieuw = gecorrigeerd.loc[sel & (gecorrigeerd.positie == bron_positie), "waarde"].iloc[0]
        gecorrigeerd.loc[sel & (gecorrigeerd.positie == positie), "waarde"] = nieuw
        print(f"correctie {code}: {reeks} {gezin} {risico} {typ} maand {maand} op €{positie}: "
              f"{oud:.2f} -> {nieuw:.2f}")

    # wijziging: correctie | 22 september 2026: rijcorrecties met een vaste waarde (J2).
    for reeks, gezin, risico, typ, maand, waarde, code, reden in CORRECTIES_VAST:
        sel = ((gecorrigeerd.reeks == reeks) & (gecorrigeerd.gezin == gezin) & (gecorrigeerd.risico == risico)
               & (gecorrigeerd.type == typ) & (gecorrigeerd.maand == maand))
        oud = gecorrigeerd.loc[sel, "waarde"].unique()
        gecorrigeerd.loc[sel, "waarde"] = waarde
        print(f"correctie {code}: {reeks} {gezin} {risico} {typ} maand {maand}, alle {int(sel.sum())} posities: "
              f"{', '.join(f'{v:.2f}' for v in oud)} -> {waarde:.2f}")

    # --- correctie J1: de netto pensioenen komen uit het correctieblad ---
    if PENSIOENCORRECTIE.exists():
        pens = lees_pensioencorrectie()
        pens.to_csv(PENS_PUBLIEK, index=False, float_format="%.17g")
    else:
        pens = pd.read_csv(PENS_PUBLIEK, float_precision="round_trip")
        print(f"pensioencorrectie uit {PENS_PUBLIEK.name} (correctieblad niet aanwezig)")
    vergelijking = []
    for typ in ["ZV100", "ZV75", "ZV50", "ZV00", "ZE", "WN"]:
        sel = ((gecorrigeerd.reeks == "uitkering") & (gecorrigeerd.risico == "pensioen") & (gecorrigeerd.type == typ))
        oud = gecorrigeerd.loc[sel].sort_values("positie")
        nieuw = pens[pens.type == typ].sort_values("positie")
        assert len(oud) == len(nieuw) == 34
        for p, o, n, b in zip(ROOSTER, oud.waarde.to_numpy(), nieuw.netto.to_numpy(), nieuw.bindend):
            vergelijking.append(dict(type=typ, positie=p, netto_werkboek=o, netto_gecorrigeerd=n,
                                     verschil=n - o, bindend=b))
        gecorrigeerd.loc[sel, "waarde"] = gecorrigeerd.loc[sel, "positie"].map(
            dict(zip(nieuw.positie, nieuw.netto)))
        gecorrigeerd.loc[sel, "cel"] = f"'{PENS_BLAD}'!correctie J1"
    vergelijking = pd.DataFrame(vergelijking)
    vergelijking.to_csv(OUT_CHECKS / "micro_pensioenen_correctie.csv", index=False, float_format="%.10g")
    print(f"correctie J1: netto pensioenen vervangen, {int((vergelijking.verschil.abs() > 0.01).sum())} van "
          f"{len(vergelijking)} cellen wijzigen (grootste daling €{-vergelijking.verschil.min():,.0f})")

    uit = bereken(gecorrigeerd)

    lang(uit).to_csv(DATA_PROCESSED / "micro_indicatoren.csv", index=False, float_format="%.10g")
    sv = samenvatting(uit)
    sv.to_csv(DATA_PROCESSED / "micro_samenvatting.csv", index=False, float_format="%.10g")
    print("geschreven: data/processed/micro_indicatoren.csv, micro_samenvatting.csv")

    # --- de cellen van de tabellen in §6.2 en Bijlage 7 ---
    # wijziging: cijfer | 22 september 2026, leesnota J3 beslist door Wim: de uitkeringsmaand van de werknemer
    # is geharmoniseerd over alle tabellen. Overal ziekte maand 2 en werkloosheid maand 1-3, zoals bij de
    # equivalentiegraad in Tabel 9 en B7.1. Dat verandert drie cellen ten opzichte van het oorspronkelijke
    # rapport: Tabel 10 ziekte (was maand 7-12), Tabel B7.2 ziekte (was maand 7-12) en Tabel B7.2 werkloosheid
    # (was maand 4-6). De rijen van de zelfstandigen wijzigen niet: hun uitkering is forfaitair en dus
    # maandonafhankelijk. Eerder al hersteld: de cel werkloosheid in Tabel 10, die was overgenomen uit de
    # tabel voor koppels.
    def cel(tabel, rij, kolom, ind, gezin, risico, t, m):
        r = sv[(sv.indicator == ind) & (sv.gezin == gezin) & (sv.risico == risico) & (sv.type == t) & (sv.maand == m)]
        assert len(r) == 1, (tabel, ind, gezin, risico, t, m)
        return dict(tabel=tabel, rij=rij, kolom=kolom, indicator=ind, gezin=gezin, risico=risico, type=t, maand=m,
                    gemiddelde=r.gemiddelde.iloc[0], vc=r.vc.iloc[0])

    cellen = []
    for t in ["WN", "ZE", "ZV100VAA", "ZV100", "ZV75", "ZV50", "ZV00"]:
        cellen.append(cel("8", t, "gelijk", "bijdrage_ratio", "-", "-", t, "-"))
    for t in ["WN", "ZE", "ZV100VAA", "ZV100", "ZV75", "ZV50", "ZV00"]:
        m_z, m_w = ("2", "1-3") if t == "WN" else ("-", "-")
        cellen.append(cel("9", t, "ziekte", "equivalentiegraad", "alleen", "ziekte", t, m_z))
        cellen.append(cel("9", t, "werkloosheid", "equivalentiegraad", "alleen", "werkloosheid", t, m_w))
        if t != "ZV100VAA":
            cellen.append(cel("9", t, "pensioen", "equivalentiegraad", "-", "pensioen", t, "-"))
    cellen.append(cel("10", "WN", "ziekte", "vervangingsgraad", "alleen", "ziekte", "WN", "2"))
    cellen.append(cel("10", "WN", "werkloosheid", "vervangingsgraad", "alleen", "werkloosheid", "WN", "1-3"))
    cellen.append(cel("10", "ZS", "ziekte", "vervangingsgraad", "alleen", "ziekte", "ZS", "-"))
    cellen.append(cel("10", "ZS", "werkloosheid", "vervangingsgraad", "alleen", "werkloosheid", "ZS", "-"))
    for t in ["WN", "ZE", "ZV100", "ZV75", "ZV50", "ZV00"]:
        cellen.append(cel("10", t, "pensioen", "vervangingsgraad", "-", "pensioen", t, "-"))
    for t in ["WN", "ZE", "ZV100VAA", "ZV75", "ZV50", "ZV00"]:
        m_z, m_w = ("2", "1-3") if t == "WN" else ("-", "-")
        cellen.append(cel("B7.1", t, "ziekte", "equivalentiegraad", "koppel", "ziekte", t, m_z))
        cellen.append(cel("B7.1", t, "werkloosheid", "equivalentiegraad", "koppel", "werkloosheid", t, m_w))
    cellen.append(cel("B7.2", "WN", "ziekte", "vervangingsgraad", "koppel", "ziekte", "WN", "2"))
    cellen.append(cel("B7.2", "WN", "werkloosheid", "vervangingsgraad", "koppel", "werkloosheid", "WN", "1-3"))
    cellen.append(cel("B7.2", "ZS", "ziekte", "vervangingsgraad", "koppel", "ziekte", "ZS", "-"))
    cellen.append(cel("B7.2", "ZS", "werkloosheid", "vervangingsgraad", "koppel", "werkloosheid", "ZS", "-"))
    pd.DataFrame(cellen).to_csv(DATA_PROCESSED / "micro_tabellen.csv", index=False, float_format="%.10g")
    print("geschreven: data/processed/micro_tabellen.csv")


if __name__ == "__main__":
    main()
