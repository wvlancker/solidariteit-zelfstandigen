"""
Stap m01: Kakwani-index gewogen naar de inkomensverdeling in BE-SILC 2024

Waarom?
-------
In het rapport weegt elke roosterpositie even zwaar (1/34). Het rooster is dicht
bij lage inkomens en ijl aan de top, maar 21 van de 34 posities liggen boven de
mediaan. Een zelfstandige met €15.000 per maand telt dan even zwaar als een
zelfstandige met €2.000. De gewogen versie laat elke positie meetellen naar het
aandeel zelfstandigen (of werknemers) dat in BE-SILC 2024 rond dat inkomen zit.

Werkwijze
---------
1. De gewichten per roosterpositie komen uit de Stata-stap
   `m00_kakwani_gewichten_besilc2024.do` (BE-SILC-microdata, niet in de repository).
   Die schrijft naar data/raw/:
     kakwani_gewichten_eq_besilc2024.csv   gewicht per variant, groep en positie
     kakwani_resultaten_eq_besilc2024.csv  Kakwani-indices berekend in Stata
     kakwani_eq_besilc2024.log
2. Dit script rekent alle Kakwani-indices opnieuw uit in Python, met dezelfde
   gewichten en de bijdragen uit unizo.dta.
3. Controle: Python en Stata moeten tot op 1e-9 hetzelfde geven. Anders stopt het script.

Varianten van het inkomen (zie m00 en code/micro/LEESMIJ.md):
  A  gestandaardiseerd netto beschikbaar inkomen (eq_inc20/12) rechtstreeks  <- hoofdvariant
  B  omgerekend naar het individuele inkomen in het typegeval, laag partnerloon
  C  idem, gemiddeld partnerloon

Uitvoer
-------
  data/processed/micro_kakwani_besilc2024.csv          alle indices (Python)
  output/checks/micro_kakwani_stata_vs_python.csv      verschil per index

Uitvoeren:  python code/micro/m01_kakwani_besilc.py
"""

import numpy as np
import pandas as pd

from common_micro import (DATA_PROCESSED, DATA_RAW, OUT_CHECKS, ROOSTER, SILC_GEWICHTEN,
                          SILC_RESULTATEN, gem_ratio, kakwani, lees_unizo, zorg_voor_mappen,
                          concentratie)

# wijziging: nieuw | 23 september 2026, publicatie op GitHub. De uitvoer van m00 (Stata) steunt op de
# BE-SILC-microdata en bevat het aantal waarnemingen per roosterpositie; die aantallen delen we niet.
# Het gewicht per positie is een aandeel en geen microgegeven, dus dat kan wel mee. Deze stap schrijft
# daarom twee publieke afgeleiden:
#   data/raw/micro_silc_gewichten.csv  gewicht per variant, groep en positie (zonder celaantallen)
#   data/raw/micro_silc_groepen.csv    per variant en groep: totaal aantal waarnemingen, aantal
#                                      posities met waarnemingen en aantal posities met minder dan 10
# Ontbreekt de Stata-uitvoer (publieke repository), dan draait deze stap met die twee bestanden verder
# en komen alle cijfers van Tabel 8 er identiek uit. Zie DATA.md.
GEWICHTEN_PUBLIEK = DATA_RAW / "micro_silc_gewichten.csv"
GROEPEN_PUBLIEK = DATA_RAW / "micro_silc_groepen.csv"

zorg_voor_mappen()

UIT_STATA = SILC_GEWICHTEN.exists()
if not UIT_STATA and not GEWICHTEN_PUBLIEK.exists():
    # Zonder BE-SILC-uitvoer en zonder publieke afgeleide kan deze stap niet.
    print(f"{SILC_GEWICHTEN.name} en {GEWICHTEN_PUBLIEK.name} ontbreken allebei: stap overgeslagen.")
    raise SystemExit(0)

d = lees_unizo()
y = d.INKOMEN.values.astype(float)

# Gewichten inlezen. Posities zonder waarnemingen staan niet in het bestand: gewicht 0.
if UIT_STATA:
    g = pd.read_csv(SILC_GEWICHTEN, sep=";")
    g[["variant", "groep", "pos", "w"]].to_csv(GEWICHTEN_PUBLIEK, index=False, float_format="%.17g")
    g.groupby(["variant", "groep"]).agg(
        n_obs=("n", "sum"), posities_met_obs=("pos", "size"),
        posities_n_onder_10=("n", lambda r: int((r < 10).sum())),
    ).reset_index().to_csv(GROEPEN_PUBLIEK, index=False)
    print(f"geschreven: {GEWICHTEN_PUBLIEK.name} en {GROEPEN_PUBLIEK.name} (publieke afgeleiden)")
else:
    print(f"gewichten uit {GEWICHTEN_PUBLIEK.name} (Stata-uitvoer niet aanwezig)")
    g = pd.read_csv(GEWICHTEN_PUBLIEK, float_precision="round_trip")

rijen = []

# (a) Gelijke gewichten: reproduceert het rapport
for t in ["ZE", "ZV100VAA", "ZV100", "ZV75", "ZV50", "ZV00", "WN"]:
    w = np.ones(len(y))
    rijen.append(dict(variant="-", groep="rapport", type=t, gini=concentratie(y, y, w),
                      kakwani=kakwani(d[t], y, w), ratio=gem_ratio(d[t], y, w)))

# (b) BE-SILC-gewichten per variant en groep
for (variant, groep), sub in g.groupby(["variant", "groep"], sort=True):
    w = d.INKOMEN.map(sub.set_index("pos")["w"]).fillna(0).values
    types = ["ZE", "ZV100VAA", "ZV100", "ZV75", "ZV50", "ZV00"] if groep.startswith("zs") else ["WN"]
    for t in types:
        rijen.append(dict(variant=variant, groep=groep, type=t, gini=concentratie(y, y, w),
                          kakwani=kakwani(d[t], y, w), ratio=gem_ratio(d[t], y, w)))

res = pd.DataFrame(rijen)

# Aantal ongewogen waarnemingen per groep en het aandeel posities met minder dan 10 waarnemingen,
# als indicatie van de precisie (geen betrouwbaarheidsinterval). Die aantallen staan per groep in
# GROEPEN_PUBLIEK, zodat ze ook zonder de Stata-uitvoer beschikbaar zijn.
n = pd.read_csv(GROEPEN_PUBLIEK)
res = res.merge(n, on=["variant", "groep"], how="left")
res.to_csv(DATA_PROCESSED / "micro_kakwani_besilc2024.csv", index=False)

# ---------------------------------------------------------------------------
# Controle tegen Stata
# ---------------------------------------------------------------------------
# <!-- wijziging: publicatie | controle enkel als de Stata-resultaten aanwezig zijn -->
# De Stata-resultaten bevatten alleen indices (geen celaantallen) en worden meegepubliceerd,
# maar wie het bestand niet heeft, kan de rest van de stap wel draaien.
if SILC_RESULTATEN.exists():
    stata = pd.read_csv(SILC_RESULTATEN, sep=";").fillna({"variant": "-"})
    stata["variant"] = stata["variant"].replace("", "-")
    cmp = res.merge(stata, on=["variant", "groep", "type"], suffixes=("_python", "_stata"), how="outer",
                    indicator=True)
    for k in ["gini", "kakwani", "ratio"]:
        cmp[f"verschil_{k}"] = cmp[f"{k}_python"] - cmp[f"{k}_stata"]
    cmp.to_csv(OUT_CHECKS / "micro_kakwani_stata_vs_python.csv", index=False)

    assert (cmp["_merge"] == "both").all(), "Python en Stata hebben niet dezelfde combinaties"
    maxverschil = cmp[[c for c in cmp if c.startswith("verschil_")]].abs().max().max()
    assert maxverschil < 1e-9, f"Python wijkt af van Stata (max {maxverschil})"
    vergelijking = f"Python = Stata (max. verschil {maxverschil:.1e})"
else:
    vergelijking = f"{SILC_RESULTATEN.name} niet aanwezig, vergelijking met Stata overgeslagen"

# Rapportcontrole: gelijke gewichten geven de cijfers uit Tabel 8 van het rapport
r = res.set_index(["variant", "groep", "type"])["kakwani"]
assert round(r[("-", "rapport", "ZE")], 3) == -0.159 and round(r[("-", "rapport", "WN")], 3) == 0.072

print(f"Kakwani BE-SILC: {len(res)} indices, {vergelijking}.")
kern = res[(res.groep.isin(["rapport", "zs_typ", "wn_typ"])) & (res.type.isin(["ZE", "ZV00", "WN"]))]
print(kern[["variant", "groep", "type", "kakwani", "ratio"]].round(3).to_string(index=False))
