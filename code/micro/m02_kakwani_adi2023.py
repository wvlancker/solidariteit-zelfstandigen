"""
Stap m02: Kakwani-index gewogen naar het administratief inkomen (Statbel ADI 2023)

Waarom?
-------
Tweede, onafhankelijke weging naast BE-SILC (m01). Statbel leverde histogrammen van
het gestandaardiseerd beschikbaar inkomen op basis van administratieve gegevens
(ADI 2023), apart voor werknemers (blad EMPL) en zelfstandigen (blad SELF).
Voordeel: volledige populatie, geen steekproefruis. Nadeel: enkel klassen van
€1.000 per jaar en een open topklasse vanaf €83.500 per jaar.

Het bestand is NIET publiek deelbaar en staat in data/restricted/ (niet in Git).
Ontbreekt het, dan slaat dit script zichzelf over.

Werkwijze
---------
1. Histogram inlezen: klassemidden (_MINPT_, jaarbedrag) en aantal personen (_COUNT_).
   Klassen zijn €1.000 breed; de laatste klasse (midden 84.000) is open naar boven.
2. Rond elke roosterpositie (maandbedrag x 12) leggen we een interval: de grens met de
   buurpositie ligt in het midden tussen beide. De eerste positie (€1.550) krijgt alles
   eronder, de laatste (€15.000) alles erboven.
3. Binnen een histogramklasse veronderstellen we een uniforme spreiding. Het gewicht van
   een positie = som over de klassen van (aantal x overlap met het interval / klassebreedte).
4. De open topklasse verdelen we over de posities met een Pareto-staart (hoofdscenario).
   De Pareto-parameter alpha schatten we uit de klassen €50.000-€83.000 (log-lineaire fit
   van aantal op inkomen: log n = a + b log x, alpha = -b - 1).
5. Kakwani-index en gemiddelde bijdrage/draagkracht met die gewichten (functies in common_micro).

Gevoeligheidsscenario's
-----------------------
  hoofd                 eigen verdeling per groep, Pareto-staart
  zelfst_voor_iedereen  zelfstandigenverdeling ook voor werknemers
  top_op_laagste        open topklasse volledig op de eerste positie erin
  top_gelijk            open topklasse gelijk verdeeld over de posities erin
  onder_rooster_weg     personen onder het rooster weglaten i.p.v. aan €1.550 toe te wijzen
  inkomens_plus3        histogram 3% opgetrokken (inkomensjaar 2023 -> niveau 2024)

Uitvoer
-------
  data/processed/micro_kakwani_adi2023.csv            Kakwani en ratio per scenario en type
  data/processed/micro_gewichten_adi2023.csv          gewicht per positie (hoofdscenario)  [restricted-afgeleid, zie .gitignore]

Uitvoeren:  python code/micro/m02_kakwani_adi2023.py
"""

import numpy as np
import openpyxl
import pandas as pd

from common_micro import (ADI_HISTOGRAM, DATA_PROCESSED, DATA_RAW, ROOSTER, TYPES, gem_ratio, kakwani,
                          lees_unizo, zorg_voor_mappen)

# wijziging: nieuw | 23 september 2026, publicatie op GitHub. Het histogram van Statbel is niet
# publiek deelbaar, de gewichten per roosterpositie die eruit volgen wel: dat zijn aandelen, geen
# microgegevens. Staat het histogram in data/restricted/, dan berekenen we de gewichten eruit en
# schrijven we ze weg naar GEWICHTEN_PUBLIEK. Staat het er niet (publieke repository), dan lezen we
# dat bestand en draaien alle scenario's daarmee verder. Zie DATA.md.
GEWICHTEN_PUBLIEK = DATA_RAW / "micro_adi_gewichten.csv"

zorg_voor_mappen()
UIT_HISTOGRAM = ADI_HISTOGRAM.exists()
if not UIT_HISTOGRAM and not GEWICHTEN_PUBLIEK.exists():
    print(f"{ADI_HISTOGRAM.name} en {GEWICHTEN_PUBLIEK.name} ontbreken allebei: stap overgeslagen.")
    raise SystemExit(0)

d = lees_unizo()
y = d.INKOMEN.values.astype(float)                # maandinkomen per positie
# Grenzen van de intervallen rond elke positie, op jaarbasis
grenzen = np.r_[-np.inf, (y[1:] + y[:-1]) / 2, np.inf] * 12

wb = openpyxl.load_workbook(ADI_HISTOGRAM, data_only=True) if UIT_HISTOGRAM else None


def histogram(blad):
    """Klassemiddens en aantallen uit een histogramblad (enkel de datarijen)."""
    ws = wb[blad]
    rijen = [(ws.cell(r, 2).value, ws.cell(r, 4).value) for r in range(2, ws.max_row + 1)
             if ws.cell(r, 1).value == "MS_EQ_ADI_STATBEL"]
    midden = np.array([m for m, _ in rijen], dtype=float)
    aantal = np.array([n for _, n in rijen], dtype=float)
    assert np.all(np.diff(midden) == 1000), f"{blad}: klassen niet €1.000 breed"
    return midden, aantal


def gewichten(blad, factor=1.0, top="pareto", onder_rooster_weg=False):
    """Gewicht per roosterpositie (som = 1)."""
    midden, aantal = histogram(blad)
    midden = midden * factor
    breedte = 1000 * factor
    onder, boven = midden - breedte / 2, midden + breedte / 2
    w = np.zeros(len(y))

    # Gesloten klassen: uniforme spreiding binnen de klasse
    for a, b, n in zip(onder[:-1], boven[:-1], aantal[:-1]):
        for i in range(len(y)):
            lo, hi = grenzen[i], grenzen[i + 1]
            if onder_rooster_weg and i == 0:
                lo = y[0] * 12 - (y[1] - y[0]) * 12 / 2   # symmetrisch interval rond €1.550
            overlap = max(0.0, min(b, hi) - max(a, lo))
            w[i] += n * overlap / breedte

    # Open topklasse
    n_top = aantal[-1]
    ondergrens_top = onder[-1]
    in_top = np.where(grenzen[1:] > ondergrens_top)[0]       # posities waarvan het interval de topklasse raakt
    if top == "op_laagste":
        w[in_top[0]] += n_top
    elif top == "gelijk":
        w[in_top] += n_top / len(in_top)
    elif top == "pareto":
        sel = (midden >= 50000 * factor) & (midden < midden[-1])
        b, _ = np.polyfit(np.log(midden[sel]), np.log(aantal[sel]), 1)
        alpha = -b - 1
        # overlevingsfunctie Pareto: S(x) = (x / ondergrens)^-alpha
        S = lambda x: 0.0 if np.isinf(x) else (max(x, ondergrens_top) / ondergrens_top) ** (-alpha)
        for i in in_top:
            w[i] += n_top * (S(grenzen[i]) - S(grenzen[i + 1]))
    else:
        raise ValueError(top)
    return w / w.sum()


if UIT_HISTOGRAM:
    w_zs = gewichten("SELF")
    w_wn = gewichten("EMPL")
    scenarios = {
        "rapport_gelijk": (np.ones(len(y)), np.ones(len(y))),
        "hoofd": (w_wn, w_zs),
        "zelfst_voor_iedereen": (w_zs, w_zs),
        "top_op_laagste": (gewichten("EMPL", top="op_laagste"), gewichten("SELF", top="op_laagste")),
        "top_gelijk": (gewichten("EMPL", top="gelijk"), gewichten("SELF", top="gelijk")),
        "onder_rooster_weg": (gewichten("EMPL", onder_rooster_weg=True), gewichten("SELF", onder_rooster_weg=True)),
        "inkomens_plus3": (gewichten("EMPL", 1.03), gewichten("SELF", 1.03)),
    }
    # Publieke afgeleide: gewicht per scenario, groep en positie (aandelen, som 1 per reeks).
    lang = [dict(scenario=s, groep=g, positie=int(p), gewicht=v)
            for s, (wwn, wzs) in scenarios.items()
            for g, vec in (("werknemers", wwn), ("zelfstandigen", wzs))
            for p, v in zip(y, vec / vec.sum())]
    pd.DataFrame(lang).to_csv(GEWICHTEN_PUBLIEK, index=False, float_format="%.17g")
    print(f"geschreven: {GEWICHTEN_PUBLIEK.relative_to(DATA_RAW.parents[1])}")
else:
    print(f"gewichten uit {GEWICHTEN_PUBLIEK.name} (bronhistogram niet aanwezig)")
    lang = pd.read_csv(GEWICHTEN_PUBLIEK, float_precision="round_trip")
    assert sorted(lang.positie.unique().tolist()) == sorted(ROOSTER), "gewichten volgen het rooster niet"
    scenarios = {}
    for s, sub in lang.groupby("scenario", sort=False):
        per_groep = {}
        for g in ("werknemers", "zelfstandigen"):
            r = sub[sub.groep == g].set_index("positie")["gewicht"]
            per_groep[g] = np.array([r[p] for p in y.astype(int)], dtype=float)
        scenarios[s] = (per_groep["werknemers"], per_groep["zelfstandigen"])
    w_wn, w_zs = scenarios["hoofd"]

rijen = []
for s, (wwn, wzs) in scenarios.items():
    for t in TYPES:
        w = wwn if t == "WN" else wzs
        rijen.append(dict(scenario=s, type=t, kakwani=kakwani(d[t], y, w), ratio=gem_ratio(d[t], y, w)))
res = pd.DataFrame(rijen)
res.to_csv(DATA_PROCESSED / "micro_kakwani_adi2023.csv", index=False)
pd.DataFrame({"pos": y.astype(int), "w_werknemers": w_wn, "w_zelfstandigen": w_zs}).to_csv(
    DATA_PROCESSED / "micro_gewichten_adi2023.csv", index=False)

tab = res.pivot(index="type", columns="scenario", values="kakwani").loc[list(TYPES)]
print("Kakwani, gewogen naar ADI 2023:")
print(tab[list(scenarios)].round(3).to_string())
