"""
Stap m03: waar zit de regressiviteit in de bijdrageschaal van de eenmanszaak?

Waarom?
-------
De conclusie (§7) wijst twee plaatsen in de bijdrageschaal aan: de degressieve schijf
(14,16% tussen tussengrens en maximumgrens) en de minimumbijdrage. Dit script toetst
dat op onze eigen simulaties, met netto beschikbaar inkomen als draagkracht (zoals
in het hele microdeel), en niet op bruto beroepsinkomen.

Werkwijze
---------
1. Per roosterpositie van de eenmanszaak (alleenstaande) lezen we uit het werkboek:
   te benaderen DPI (rij 7), netto belastbaar inkomen per maand (rij 11) en de
   gesimuleerde sociale bijdrage (rij 14), blad 'Eénmanszaak_alleenstaande'.
2. Controle 1: de bijdrageschaal in common_micro.bijdrage_zelfstandige() reproduceert
   de gesimuleerde bijdragen (tot op €1). Zo weten we dat de schaal klopt.
3. Controle 2: de minimumbijdrage speelt nergens op het rooster (laagste netto
   belastbaar inkomen ligt boven de minimumdrempel).
4. We delen elke positie in: onder de tussengrens, in de degressieve schijf, boven de
   maximumgrens (plafond).
5. Scenario's: dezelfde netto belastbare inkomens, andere schaal:
     huidig
     geen_degressieve_schijf    20,5% tot het plafond
     geen_plafond               14,16% loopt door boven de tussengrens
     vlak_20_5                  20,5% op het hele inkomen
   STATISCH: een hogere bijdrage zou het belastbaar inkomen en de DPI wat verlagen,
   en gedrag (bv. overstap naar een vennootschap) blijft buiten beschouwing.
6. Voor elk scenario: Kakwani-index, gemiddelde bijdrage/draagkracht en de relatieve
   verandering van de totale bijdragen, met drie wegingen:
     gelijk     1/34 per positie (zoals het rapport)
     silc_A     BE-SILC 2024, zelfstandigen typegevallen, variant A (uitvoer m00)
     adi2023    Statbel ADI 2023, zelfstandigen (uitvoer m02; enkel als die bestaat)
   Let op: surveydata (BE-SILC) onderschatten de top. De opbrengst van ingrepen boven de
   tussengrens is met silc_A eerder een ondergrens.
7. Onderkant: de opbrengst van het afschaffen van de degressieve schijf, uitgedrukt als
   % van de bijdragen die de posities tot €1.550, €2.000 en €2.500 betalen. Dat geeft aan
   hoe groot een vermindering onderaan met die opbrengst kan zijn.

Uitvoer
-------
  data/processed/micro_schaal_posities.csv    per positie: inkomens, zone, bijdragen per scenario, ratio's, gewichten
  data/processed/micro_schaal_scenarios.csv   per scenario en weging: Kakwani, ratio, opbrengst
  data/processed/micro_schaal_onderkant.csv   opbrengst degressieve schijf t.o.v. bijdragen onderaan

Uitvoeren:  python code/micro/m03_scenario_bijdrageschaal.py
"""

import numpy as np
import pandas as pd

from common_micro import (DATA_PROCESSED, DATA_RAW, MAXIMUMGRENS_JAAR, MINIMUMDREMPEL_JAAR, ROOSTER,
                          TUSSENGRENS_JAAR, WERKBOEK_MICRO, bijdrage_zelfstandige, gem_ratio, kakwani,
                          lees_silc_gewichten, lees_unizo, zorg_voor_mappen)

zorg_voor_mappen()

# <!-- wijziging: publicatie | publieke invoer zodat m03 ook zonder het werkboek draait -->
# Publieke afgeleide van de drie rijen die dit script uit het werkboek haalt. Het werkboek
# zelf is afgeschermde brondata (Viren/EUROMOD, zie DATA.md); deze drie rijen zijn de
# gesimuleerde bedragen per roosterpositie en worden wel meegepubliceerd.
INVOER_PUBLIEK = DATA_RAW / "micro_schaal_invoer.csv"

# ---------------------------------------------------------------------------
# 1. Inkomens en bijdragen per positie uit het werkboek
# ---------------------------------------------------------------------------
if WERKBOEK_MICRO.exists():
    # header=None: Excel-rij r staat op pandas-index r-1. Kolommen C:AJ = 34 posities.
    blad = pd.read_excel(WERKBOEK_MICRO, sheet_name="Eénmanszaak_alleenstaande", header=None)
    assert str(blad.iat[6, 1]).strip() == "Te benaderen DPI"
    assert str(blad.iat[10, 1]).strip() == "Netto belastbaar inkomen"
    assert str(blad.iat[13, 1]).strip() == "Sociale bijdrage"
    pos = pd.DataFrame({
        "dpi": blad.iloc[6, 2:36].astype(float).values,
        "nbi_maand": blad.iloc[10, 2:36].astype(float).values,
        "bijdrage_werkboek": blad.iloc[13, 2:36].astype(float).values,
    })
    # %.17g: genoeg decimalen om elke float exact terug te lezen, zodat de publieke modus
    # bit voor bit dezelfde uitvoer geeft als de modus met het werkboek.
    pos.to_csv(INVOER_PUBLIEK, index=False, float_format="%.17g")
elif INVOER_PUBLIEK.exists():
    pos = pd.read_csv(INVOER_PUBLIEK, float_precision="round_trip")
    print(f"invoer uit {INVOER_PUBLIEK.name} (werkboek niet aanwezig)")
else:
    print(f"{WERKBOEK_MICRO.name} en {INVOER_PUBLIEK.name} ontbreken allebei: stap overgeslagen.")
    raise SystemExit(0)
assert pos.dpi.tolist() == ROOSTER

# unizo.dta bevat dezelfde bijdragen (basis Kakwani in het rapport) en die van werknemers
u = lees_unizo()
assert np.allclose(u.ZE.values, pos.bijdrage_werkboek.values, atol=0.01), "unizo.dta wijkt af van het werkboek"
pos["bijdrage_werknemer"] = u.WN.values

# ---------------------------------------------------------------------------
# 2-3. Controles op de schaal
# ---------------------------------------------------------------------------
herberekend = bijdrage_zelfstandige(pos.nbi_maand)
maxafw = np.abs(herberekend - pos.bijdrage_werkboek).max()
assert maxafw < 1.0, f"schaal reproduceert het werkboek niet (max. afwijking €{maxafw:.2f})"
laagste_nbi_jaar = pos.nbi_maand.min() * 12
assert laagste_nbi_jaar > MINIMUMDREMPEL_JAAR, "minimumbijdrage speelt wel op het rooster: script herzien"
print(f"Schaal reproduceert het werkboek (max. afwijking €{maxafw:.2f}). Laagste netto belastbaar inkomen "
      f"€{laagste_nbi_jaar:,.0f}/jaar > minimumdrempel €{MINIMUMDREMPEL_JAAR:,.0f}: minimumbijdrage niet bindend.")

# ---------------------------------------------------------------------------
# 4. Zones
# ---------------------------------------------------------------------------
pos["zone"] = np.select(
    [pos.nbi_maand * 12 <= TUSSENGRENS_JAAR, pos.nbi_maand * 12 <= MAXIMUMGRENS_JAAR],
    ["onder tussengrens", "degressieve schijf"], "boven plafond")

# ---------------------------------------------------------------------------
# 5. Scenario's
# ---------------------------------------------------------------------------
SCEN = {
    "huidig": dict(),
    "geen_degressieve_schijf": dict(tarief_2=0.205),
    "geen_plafond": dict(plafond=False),
    "vlak_20_5": dict(tarief_2=0.205, plafond=False),
}
for s, kw in SCEN.items():
    pos[f"bijdrage_{s}"] = bijdrage_zelfstandige(pos.nbi_maand, **kw)
    pos[f"ratio_{s}"] = pos[f"bijdrage_{s}"] / pos.dpi
pos["ratio_werknemer"] = pos.bijdrage_werknemer / pos.dpi

# ---------------------------------------------------------------------------
# 6. Wegingen
# ---------------------------------------------------------------------------
wegingen = {"gelijk": np.ones(len(pos))}
# <!-- wijziging: publicatie | gewichten via lees_silc_gewichten (Stata-uitvoer of publieke afgeleide) -->
g = lees_silc_gewichten()
if g is not None:
    gA = g[(g.variant == "A") & (g.groep == "zs_typ")].set_index("pos")["w"]
    wegingen["silc_A"] = pos.dpi.map(gA).fillna(0).values
adi = DATA_PROCESSED / "micro_gewichten_adi2023.csv"
if adi.exists():
    wegingen["adi2023"] = pd.read_csv(adi).set_index("pos").loc[ROOSTER, "w_zelfstandigen"].values
for k, w in wegingen.items():
    pos[f"gewicht_{k}"] = w / w.sum()

rijen = []
for k, w in wegingen.items():
    basis = (w * pos.bijdrage_huidig).sum()
    for s in SCEN:
        b = pos[f"bijdrage_{s}"].values
        rijen.append(dict(weging=k, scenario=s,
                          kakwani=kakwani(b, pos.dpi, w),
                          gem_ratio=gem_ratio(b, pos.dpi, w),
                          opbrengst_rel=(w * b).sum() / basis - 1))
    # werknemers ter vergelijking (enkel betekenisvol bij gelijke weging; gewogen werknemers: zie m01/m02)
    if k == "gelijk":
        rijen.append(dict(weging=k, scenario="werknemer", kakwani=kakwani(pos.bijdrage_werknemer, pos.dpi, w),
                          gem_ratio=gem_ratio(pos.bijdrage_werknemer, pos.dpi, w), opbrengst_rel=np.nan))
scen = pd.DataFrame(rijen)

# ---------------------------------------------------------------------------
# 7. Onderkant
# ---------------------------------------------------------------------------
onder = []
for k, w in wegingen.items():
    b0 = w * pos.bijdrage_huidig
    extra = (w * (pos.bijdrage_geen_degressieve_schijf - pos.bijdrage_huidig)).sum()
    for grens in (1550, 2000, 2500):
        m = pos.dpi <= grens
        onder.append(dict(weging=k, tot_dpi=grens,
                          aandeel_gewicht=w[m].sum() / w.sum(),
                          aandeel_bijdragen=b0[m].sum() / b0.sum(),
                          opbrengst_schijf_als_aandeel_bijdragen_onderaan=extra / b0[m].sum()))
onder = pd.DataFrame(onder)

pos.to_csv(DATA_PROCESSED / "micro_schaal_posities.csv", index=False)
scen.to_csv(DATA_PROCESSED / "micro_schaal_scenarios.csv", index=False)
onder.to_csv(DATA_PROCESSED / "micro_schaal_onderkant.csv", index=False)

print("\nBijdrage/DPI per zone (min-max) en gewicht:")
z = pos.groupby("zone", sort=False).agg(dpi_van=("dpi", "min"), dpi_tot=("dpi", "max"),
                                         ratio_begin=("ratio_huidig", "first"), ratio_eind=("ratio_huidig", "last"),
                                         **{f"gewicht_{k}": (f"gewicht_{k}", "sum") for k in wegingen})
print(z.round(3).to_string())
print("\nScenario's:")
print(scen.round(3).to_string(index=False))
print("\nOnderkant:")
print(onder.round(3).to_string(index=False))
