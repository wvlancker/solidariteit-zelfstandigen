"""
Stap m04: statische orde van grootte van de opbrengst van ingrepen aan de top van de bijdrageschaal

Waarom?
-------
De conclusie (§7) zei oorspronkelijk dat we over het NIVEAU van de opbrengst niets kunnen
zeggen, omdat de inkomensmassa boven de grenzen onbekend is. Tabel 7 van het ABC-verslag
2022/04 geeft die massa wel, per inkomensschijf, voor zelfstandigen in hoofdberoep.
Daarmee kan een statische orde van grootte berekend worden. Het is GEEN puntschatting:
gedragseffecten (bv. meer vervennootschappelijking) blijven buiten beschouwing, en die
zijn net aan de top het grootst.

Dit gaat over het bruto beroepsinkomen (bijdragebasis), niet over draagkracht. Voor
uitspraken over verdeling gebruikt het rapport de microsimulaties (m01-m03); dit script
dient enkel voor de opbrengst.

Werkwijze
---------
Invoer: data/raw/abc_2022_tabel7.csv (herkomst: abc_2022_tabel7_bron.md).
Per schijf kennen we het aandeel personen p en het gemiddeld inkomen y. Per gemiddelde
hoofdberoeper is de extra bijdrage van een ingreep:
    som over schijven [ p x extra bijdrage bij inkomen y ]
Omdat de schaal binnen elke schijf lineair is, volstaat het gemiddeld inkomen van de schijf
(geen informatie over de spreiding binnen de schijf nodig), op voorwaarde dat iedereen in de
schijf in hetzelfde lineaire stuk van de schaal zit. Dat is zo: de schijven vallen samen met
de grenzen van de schaal.

Scenario's (grenzen 2021, zonder beheerskosten, zoals in de ABC-tabel):
  geen_plafond              14,16% loopt door boven de maximumgrens
  geen_degressieve_schijf   20,5% tot de maximumgrens (plafond blijft)
  beide                     20,5% op het hele inkomen boven de tussengrens

De relatieve opbrengst = extra bijdrage / gemiddelde bijdrage (€5.878).
Omrekening naar euro, twee varianten:
  bovengrens   relatieve opbrengst x ALLE gewone bijdragen 2023 (FOD SZ, data/raw/fodsz_bedragen.csv).
               Overschat: de gewone bijdragen omvatten ook zelfstandigen in bijberoep en actieven
               na pensioen, die zelden boven de tussengrens zitten.
  hoofdberoep  relatieve opbrengst x gewone bijdragen 2023 x aandeel van hoofdberoepers in de gewone
               bijdragen. Dat aandeel benaderen we als (472.049 hoofdberoepers, ABC Tabel 2, 2019)
               x €5.878 (ABC Tabel 4, geïndexeerd naar 2021) / gewone bijdragen 2021 (FOD SZ).
               Benadering: jaren en bronnen lopen door elkaar (aantallen 2019, bedragen 2021).

Extra: de opbrengst van het afschaffen van de degressieve schijf uitgedrukt als % van de
bijdragen die hoofdberoepers onder de minimumdrempel betalen (aandeel bijdragemassa 16,9%).

Uitvoer
-------
  data/processed/abc_opbrengst_statisch.csv

Uitvoeren:  python code/micro/m04_abc_opbrengst.py
"""

import numpy as np
import pandas as pd

from common_micro import DATA_PROCESSED, DATA_RAW, zorg_voor_mappen

zorg_voor_mappen()

t = pd.read_csv(DATA_RAW / "abc_2022_tabel7.csv").set_index("schijf")
schijven = t.drop(index="totaal")
tot = t.loc["totaal"]

# Grenzen en tarieven 2021 (zoals in de ABC-tabel)
T1, T3 = 60638.0, 89361.0
R1, R2 = 0.205, 0.1416

# ---------------------------------------------------------------------------
# Controles op de overgetypte tabel
# ---------------------------------------------------------------------------
for k in ["aandeel_personen", "aandeel_inkomensmassa", "aandeel_bijdragemassa", "aandeel_uitgavenmassa"]:
    assert abs(schijven[k].sum() - 1) < 0.0015, f"{k} telt niet op tot 1"
# aandeel personen x gemiddeld inkomen / totaal gemiddelde = aandeel inkomensmassa (afronding op 0,1 procentpunt)
herberekend = schijven.aandeel_personen * schijven.gem_inkomen / tot.gem_inkomen
assert np.allclose(herberekend, schijven.aandeel_inkomensmassa, atol=0.004), herberekend
# gemiddelde bijdrage boven het plafond = maximumbijdrage zonder beheerskosten
assert abs(T1 * R1 + (T3 - T1) * R2 - schijven.loc["boven_plafond", "gem_bijdrage"]) < 1

# ---------------------------------------------------------------------------
# Extra bijdrage per persoon in elke schijf, per scenario
# ---------------------------------------------------------------------------
y = schijven.gem_inkomen
p = schijven.aandeel_personen
huidig = np.minimum(y, T1) * R1 + np.clip(y - T1, 0, T3 - T1) * R2
scen = {
    "geen_plafond": np.minimum(y, T1) * R1 + np.maximum(y - T1, 0) * R2,
    "geen_degressieve_schijf": np.minimum(y, T1) * R1 + np.clip(y - T1, 0, T3 - T1) * R1,
    "beide": np.minimum(y, T1) * R1 + np.maximum(y - T1, 0) * R1,
}

fod = pd.read_csv(DATA_RAW / "fodsz_bedragen.csv").set_index("jaar")
gewone_2023 = fod.loc[2023, "z_gewone_bijdragen"] * 1000   # duizend euro -> euro

# Aandeel hoofdberoepers in de gewone bijdragen (benadering, zie docstring)
n_hoofdberoep = pd.read_csv(DATA_RAW / "abc_2022_tabel2.csv").set_index("categorie").loc["totaal", "hoofdberoep_aantal"]
aandeel_hoofdberoep = n_hoofdberoep * tot.gem_bijdrage / (fod.loc[2021, "z_gewone_bijdragen"] * 1000)
assert 0 < aandeel_hoofdberoep < 1

rijen = []
for s, nieuw in scen.items():
    extra_pp = (p * (nieuw - huidig)).sum()        # per gemiddelde hoofdberoeper, euro per jaar
    rel = extra_pp / tot.gem_bijdrage
    rijen.append(dict(scenario=s, extra_per_hoofdberoeper=extra_pp, opbrengst_rel=rel,
                      bovengrens_mln_euro_2023=rel * gewone_2023 / 1e6,
                      hoofdberoep_mln_euro_2023=rel * gewone_2023 * aandeel_hoofdberoep / 1e6))
res = pd.DataFrame(rijen)

rel_schijf = res.set_index("scenario").loc["geen_degressieve_schijf", "opbrengst_rel"]
res["opbrengst_schijf_als_aandeel_bijdragen_onder_minimumdrempel"] = np.where(
    res.scenario == "geen_degressieve_schijf", rel_schijf / schijven.loc["onder_minimumdrempel", "aandeel_bijdragemassa"],
    np.nan)
res.to_csv(DATA_PROCESSED / "abc_opbrengst_statisch.csv", index=False)

print(f"Gewone bijdragen 2023 (FOD SZ): €{gewone_2023/1e9:.3f} miljard; benaderd aandeel hoofdberoepers {aandeel_hoofdberoep:.1%}")
print(res.round(4).to_string(index=False))
