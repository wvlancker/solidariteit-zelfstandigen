"""
Tegenfeitelijke oefening: wat als de groei van het aantal vennootschappen sinds 2003
zich had voorgedaan als eenmanszaken?

    python code/macro/03b_scenario_rechtsvorm.py
      -> data/processed/scenario_rechtsvorm.csv        (gevoeligheidstabel)
      -> data/processed/scenario_rechtsvorm_typen.csv  (typegevallen per vennootschap)

WAT DE OEFENING DOET
--------------------
Tussen 2003 en 2023 kwamen er N extra vennootschappen bij. We vergelijken het
zelfstandigenstelsel in 2023 zoals het is, met een stelsel waarin die groei als
eenmanszaak had plaatsgevonden. Twee dingen veranderen dan:

  1. De vennootschapsbijdrage (VB) van die N vennootschappen verdwijnt.
  2. Voor het deel s van die vennootschappen dat de beroepsactiviteit van een
     zelfstandige huisvest, wordt de winst die nu NIET als bezoldiging wordt
     uitgekeerd (X euro per jaar, gemiddeld) wél belastbaar beroepsinkomen, dus
     onderworpen aan de gewone bijdrage van 20,5%.
     Voor het deel 1-s (bv. patrimonium- of holdingvennootschappen, of vennootschappen
     zonder zelfstandige bedrijfsleider) is er geen eenmanszaak-tegenhanger: enkel de
     VB verdwijnt.

Per extra vennootschap is het verschil in bijdragen (tegenfeitelijk min feitelijk):
    g = s * 0,205 * X  -  VB
Totaal: N * g. Het effect op de beroepssolidariteit is N * g / uitgaven 2023.

Omslagpunt: g = 0 als  s * X = VB / 0,205  (ongeveer 2.000 euro in 2023).
Met andere woorden: de groei van het aantal vennootschappen levert het stelsel
enkel méér op dan dezelfde groei als eenmanszaken, als er gemiddeld per extra
vennootschap minder dan ongeveer 2.000 euro winst buiten de bijdragebasis blijft.

AANNAMES (bewust eenvoudig, allemaal in de tekst te vermelden)
- Hetzelfde economische inkomen in beide situaties (geen gedragseffect). Omdat
  (para)fiscale voordelen een reden zijn om een vennootschap op te richten, is dit
  eerder een bovengrens voor het verschil.
- Uitgaven blijven gelijk. Hogere bijdragen zouden op termijn iets hogere
  pensioenrechten openen (inkomensgebonden pensioen); op korte termijn speelt dat niet.
- X ligt onder het eerste bijdrageplafond (72.810,94 euro in 2024), zodat 20,5% geldt.
  Voor de typegevallen hieronder rekenen we het plafond wél correct door.
- De gevoeligheidstabel gaat over het stelsel in 2023 (laatste jaar van de macroreeksen)
  en gebruikt de gemiddelde VB van 2023 uit de FOD SZ-gegevens. De typegevallen volgen
  de wettelijke regels van 2024, zoals Tabel 1 en de microsimulaties (beleid op 30 juni
  2024), met het lage bedrag van de VB in 2024 (387,34 euro), zoals in de simulaties.
  (Aangepast op 22 september 2026, vraag Wim: vroeger regels van 2023.)
- Overgang van werknemer naar bedrijfsleider (managementvennootschap) valt buiten
  deze oefening: dan is de tegenhanger het werknemersstelsel, niet de eenmanszaak.
- Beheerskosten van de sociale verzekeringsfondsen worden genegeerd.
"""

import numpy as np
import pandas as pd

from common import DATA_PROCESSED, DATA_RAW, zorg_voor_mappen

# ---------------------------------------------------------------------------
# Wettelijke parameters 2024 (nominaal, euro), dezelfde als Tabel 1 in §4.1
# ---------------------------------------------------------------------------
# Bron bijdragegrenzen: Xerius, "Sociale bijdragen 2024" (barema voor boekhouders),
# https://media.xerius.be/sites/default/files/sitecore/public/boekhouders/formulieren-en-publicaties/baremas/nl/xer-10817-fiche-baremaboekhouders-nl_2024_lr.pdf
# Tot 22 september 2026 stonden hier de parameters van 2023 (Liantis, bijdragetabel 2023:
# plafonds 70.857,99 en 104.422,24, minimumbasis 16.409,20). De tarieven zijn gelijk.
TARIEF_1 = 0.205          # tot het eerste plafond
TARIEF_2 = 0.1416         # tussen eerste en tweede plafond
PLAFOND_1 = 72_810.94
PLAFOND_2 = 107_300.30
MIN_INKOMEN_HB = 16_861.46   # minimumbijdragebasis zelfstandige in hoofdberoep
# Vennootschapsbijdrage 2024, laag bedrag (balanstotaal 2022 onder 831.990,83 euro;
# SBB, 2024). Zo rekenen ook de microsimulaties (§5.2.2.1). Enkel voor de typegevallen.
VB_TYPEGEVAL = 387.34
# Minimumbezoldiging bedrijfsleider om het verlaagd tarief vennootschapsbelasting
# te genieten: 45.000 euro (of het belastbaar resultaat, als dat lager is),
# aanslagjaren 2019-2026; 50.000 euro vanaf aanslagjaar 2027.
# Bron: bv. SD Worx (2025), https://www.sdworx.be/nl-be/nieuws-inspiratie/payroll-reward/
MIN_BEZOLDIGING = 45_000

JAAR_BEGIN, JAAR_EIND = 2003, 2023


def jaarbijdrage(inkomen: float) -> float:
    """Gewone sociale bijdrage zelfstandige in hoofdberoep op een jaarinkomen (2024-regels).

    Stap voor stap:
      - onder de minimumbasis betaalt men de minimumbijdrage (20,5% van de minimumbasis)
      - tot plafond 1: 20,5%
      - tussen plafond 1 en 2: 14,16% op het deel boven plafond 1
      - boven plafond 2: niets meer bovenop
    """
    basis = max(inkomen, MIN_INKOMEN_HB)
    deel1 = min(basis, PLAFOND_1) * TARIEF_1
    deel2 = max(min(basis, PLAFOND_2) - PLAFOND_1, 0) * TARIEF_2
    return deel1 + deel2


def main() -> None:
    zorg_voor_mappen()

    rsvz = pd.read_csv(DATA_RAW / "rsvz_samenstelling.csv").set_index("jaar")
    bedragen = pd.read_csv(DATA_RAW / "fodsz_bedragen.csv").set_index("jaar")

    # --- Feitelijke toestand 2023 -------------------------------------------------
    n_extra = rsvz.loc[JAAR_EIND, "vennootschappen"] - rsvz.loc[JAAR_BEGIN, "vennootschappen"]
    # bedragen FOD SZ staan in duizend euro
    vb_totaal = bedragen.loc[JAAR_EIND, "z_vennootschapsbijdragen"] * 1000
    vb_per_venn = vb_totaal / rsvz.loc[JAAR_EIND, "vennootschappen"]      # gemiddelde VB 2023
    bijdragen = bedragen.loc[JAAR_EIND, "z_bijdragen"] * 1000
    uitgaven = bedragen.loc[JAAR_EIND, "z_uitgaven"] * 1000
    ratio = bijdragen / uitgaven
    omslag_sx = vb_per_venn / TARIEF_1   # s * X waarbij het verschil nul is

    print(f"extra vennootschappen {JAAR_BEGIN}-{JAAR_EIND}: {n_extra:,.0f}")
    print(f"gemiddelde VB per vennootschap {JAAR_EIND}: {vb_per_venn:,.2f} euro")
    print(f"beroepssolidariteit {JAAR_EIND}: {ratio:.4f}; 1 procentpunt = {uitgaven/100/1e6:,.1f} miljoen euro")
    print(f"omslagpunt s*X = {omslag_sx:,.0f} euro")

    # --- Gevoeligheidstabel ---------------------------------------------------------
    rijen = []
    for s in (0.25, 0.50, 0.75, 1.00):
        for x in (0, 2_000, 5_000, 10_000, 15_000, 20_000):
            g = s * TARIEF_1 * x - vb_per_venn          # per extra vennootschap
            totaal = n_extra * g
            rijen.append({
                "aandeel_met_zelfstandige_activiteit_s": s,
                "winst_buiten_bijdragebasis_X_eur": x,
                "verschil_per_extra_vennootschap_eur": g,
                "verschil_totaal_miljoen_eur": totaal / 1e6,
                "beroepssolidariteit_feitelijk": ratio,
                "beroepssolidariteit_tegenfeitelijk": (bijdragen + totaal) / uitgaven,
                "verschil_procentpunt": totaal / uitgaven * 100,
            })
    tabel = pd.DataFrame(rijen)
    tabel.attrs["toelichting"] = "positief = eenmanszaken hadden meer bijdragen opgeleverd"
    tabel.to_csv(DATA_PROCESSED / "scenario_rechtsvorm.csv", index=False, float_format="%.6g")

    # --- Typegevallen per vennootschap met een zelfstandige bedrijfsleider -----------
    # (bijdrage als eenmanszaak) - (bijdrage bedrijfsleider + VB), 2024-regels en VB 2024 (laag bedrag)
    typen = [
        ("volledige winst als bezoldiging, winst 45.000", 45_000, 45_000),
        ("winst 60.000, bezoldiging 45.000 (minimum voor verlaagd VenB-tarief)", 60_000, MIN_BEZOLDIGING),
        ("winst 100.000, bezoldiging 45.000", 100_000, MIN_BEZOLDIGING),
        ("winst 50.000, geen bezoldiging (dividend of liquidatiereserve)", 50_000, 0),
    ]
    typrijen = []
    for label, winst, bezoldiging in typen:
        eenmanszaak = jaarbijdrage(winst)
        vennootschap = jaarbijdrage(bezoldiging) + VB_TYPEGEVAL
        typrijen.append({
            "typegeval": label, "winst_eur": winst, "bezoldiging_eur": bezoldiging,
            "bijdrage_eenmanszaak_eur": eenmanszaak,
            "bijdrage_vennootschap_incl_vb_eur": vennootschap,
            "verschil_eur": eenmanszaak - vennootschap,
        })
    typtabel = pd.DataFrame(typrijen)
    typtabel.to_csv(DATA_PROCESSED / "scenario_rechtsvorm_typen.csv", index=False, float_format="%.6g")

    with pd.option_context("display.width", 200, "display.max_columns", 20):
        print(tabel.pivot(index="winst_buiten_bijdragebasis_X_eur",
                          columns="aandeel_met_zelfstandige_activiteit_s",
                          values="verschil_procentpunt").round(1))
        print(typtabel.round(0))

    # --- Empirisch ankerpunt voor s -----------------------------------------------------
    # Hoge Raad van Financiën (2024: 50, tabel 8): bedrijfsleiders in de personenbelasting
    # AJ2015 384.406 en AJ2022 457.585 (inkomstenjaren 2014 en 2021).
    delta_bl = 457_585 - 384_406
    delta_venn = rsvz.loc[2021, "vennootschappen"] - rsvz.loc[2014, "vennootschappen"]
    print(f"extra bedrijfsleiders per extra vennootschap 2014-2021: {delta_bl/delta_venn:.2f}")

    # --- Kernwaarden voor de tekst (gelezen door 07_tekstcijfers.py) -----------------
    kern = pd.DataFrame([
        ("n_extra", n_extra, "extra vennootschappen 2003-2023"),
        ("vb_per_venn_2023", vb_per_venn, "gemiddelde vennootschapsbijdrage per vennootschap 2023 (euro)"),
        ("omslag_sx", omslag_sx, "omslagpunt s*X (euro)"),
        ("ratio_2023", ratio, "beroepssolidariteit zelfstandigen 2023 (fractie, FOD SZ-totalen)"),
        ("uitgaven_1pp_eur", uitgaven / 100, "1 procentpunt beroepssolidariteit 2023 in euro"),
        ("delta_bedrijfsleiders_2014_2021", delta_bl, "HRF 2024 tabel 8, AJ2015-AJ2022"),
        ("delta_venn_2014_2021", delta_venn, "RSVZ, extra vennootschappen 2014-2021"),
        ("bl_per_venn", delta_bl / delta_venn, "extra bedrijfsleiders per extra vennootschap"),
        ("tarief_1", TARIEF_1, "bijdragevoet tot eerste plafond"),
        ("plafond_1", PLAFOND_1, "eerste plafond 2024"),
        ("plafond_2", PLAFOND_2, "tweede plafond 2024"),
        ("vb_typegeval", VB_TYPEGEVAL, "vennootschapsbijdrage 2024, laag bedrag (typegevallen)"),
        ("min_bezoldiging", MIN_BEZOLDIGING, "minimumbezoldiging verlaagd VenB-tarief"),
    ], columns=["sleutel", "waarde", "omschrijving"])
    kern.to_csv(DATA_PROCESSED / "scenario_rechtsvorm_kern.csv", index=False, float_format="%.10g")


if __name__ == "__main__":
    main()
