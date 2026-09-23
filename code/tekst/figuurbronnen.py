"""
Bronvermelding bij de downloadbare figuren

Waarom?
-------
De figuren in output/figures/ mogen hergebruikt worden (CC BY 4.0), maar dan moet wie ze
downloadt ook weten wat ze tonen en waarop ze gebaseerd zijn. Die informatie staat al in
het rapport, in het onderschrift bij elke figuur. Dit script haalt ze daar weg en zet ze
naast de figuren zelf, zodat een gedownloade PNG of SVG niet zonder bron rondzwerft.

Werkwijze
---------
De ingevulde tekst in report/sections/*.md heeft per figuur dezelfde opbouw:

    **Figuur 1.** <titel>
    ![](../../output/figures/fig01_werkende_bevolking.png)
    Noot: <noot>            (optioneel)
    Bron: <bron>

We lezen die blokken uit, in de volgorde van het rapport, en schrijven ze weg.

Uitvoer
-------
  output/figures/BRONNEN.md    leesbare lijst: nummer, titel, noot, bron, bestandsnamen
  output/figures/bronnen.csv   dezelfde gegevens als tabel, voor wie ze wil inlezen

Uitvoeren:  python code/tekst/figuurbronnen.py
            (draait ook mee in code/run_all.py, na 07_tekstcijfers.py)
"""

import csv
import re
import sys
from pathlib import Path

WORTEL = Path(__file__).resolve().parents[2]
SECTIES = WORTEL / "report" / "sections"
FIGUREN = WORTEL / "output" / "figures"

# De volgorde van de hoofdstukken in het rapport; zo staat de lijst in dezelfde volgorde.
VOLGORDE = ["01_inleiding", "02_context", "03_solidariteit", "04_sociaal_statuut", "05_methodologie",
            "06-1_macro", "06-2_micro", "07_conclusie", "bijlage1_hervormingen", "bijlage2_populaties",
            "bijlage3_viren", "bijlage4-5_macro", "bijlage6_scenario_rechtsvorm", "bijlage7_micro_koppels"]

CITATIE = ("Van Lancker, W., Vinck, J., Goris, W., & Van Havere, T. (2026). Hoe solidair is de "
           "sociale zekerheid voor zelfstandigen? Leuven: KU Leuven, ReSPOND.")
LICENTIE = "CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/deed.nl)"

# **Figuur 12.** titel ... ![](.../figXX_naam.png) ... eventueel Noot: ... Bron: ...
# re.DOTALL laat . ook over regeleindes lopen; niet-gulzig (.*?) zodat we bij de eerste
# volgende figuur stoppen.
BLOK = re.compile(
    r"\*\*(?P<label>Figuur [^*]+?)\.?\*\*\s*(?P<titel>[^\n]*)\n"      # kop met titel
    r"(?P<tussen>.*?)"                                                # noot, commentaar, ...
    r"!\[\]\((?P<pad>[^)]*?/(?P<bestand>fig[^/)]+?)\.png)\)"          # de figuur zelf
    r"(?P<na>.*?)(?=\n\*\*(?:Figuur|Tabel)|\Z)",                      # tot de volgende figuur/tabel
    re.DOTALL)

REGEL = re.compile(r"^(Noot|Bron):\s*(.+?)\s*$", re.MULTILINE)


def opschonen(tekst):
    """Markdownlinks [tekst](url) worden 'tekst (url)'; HTML-commentaar valt weg."""
    tekst = re.sub(r"<!--.*?-->", "", tekst, flags=re.DOTALL)
    tekst = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1 (\2)", tekst)
    tekst = re.sub(r"\s+", " ", tekst).strip()
    return tekst


def lees_figuren():
    rijen = []
    for stam in VOLGORDE:
        pad = SECTIES / f"{stam}.md"
        if not pad.exists():
            continue
        tekst = pad.read_text(encoding="utf-8")
        for m in BLOK.finditer(tekst):
            velden = {"Noot": "", "Bron": ""}
            for sleutel, waarde in REGEL.findall(m.group("tussen") + m.group("na")):
                if not velden[sleutel]:                # eerste voorkomen telt
                    velden[sleutel] = opschonen(waarde)
            rijen.append(dict(
                figuur=m.group("label").strip(),
                titel=opschonen(m.group("titel")),
                noot=velden["Noot"],
                bron=velden["Bron"],
                bestand=m.group("bestand"),
                sectie=stam,
            ))
    return rijen


def main():
    if not SECTIES.exists():
        print("report/sections/ ontbreekt: draai eerst 07_tekstcijfers.py.")
        return 0
    rijen = lees_figuren()
    if not rijen:
        print("geen figuren gevonden in report/sections/: script herzien.")
        return 1

    FIGUREN.mkdir(parents=True, exist_ok=True)
    ontbreekt = [r["bestand"] for r in rijen if not (FIGUREN / f"{r['bestand']}.png").exists()]

    with open(FIGUREN / "bronnen.csv", "w", newline="", encoding="utf-8") as f:
        s = csv.DictWriter(f, fieldnames=["figuur", "titel", "noot", "bron", "bestand", "sectie",
                                          "citatie", "licentie"])
        s.writeheader()
        for r in rijen:
            s.writerow({**r, "citatie": CITATIE, "licentie": LICENTIE})

    regels = [
        "# Figuren: wat ze tonen en waar ze vandaan komen",
        "",
        "Elke figuur staat hier als PNG (300 dpi, voor tekstverwerking) en als SVG (vectorieel, ",
        "voor wie de figuur wil aanpassen). De gegevens achter elke figuur staan in ",
        "`output/tables/figuurdata/<bestand>.csv`.",
        "",
        "**Hergebruik.** De figuren staan onder CC BY 4.0. Vermeld bij overname:",
        "",
        f"> {CITATIE}",
        "",
        f"Licentie: {LICENTIE}",
        "",
        "De onderliggende gegevens zijn van derden (zie de bronregel per figuur). Die licentie dekt ",
        "onze weergave, niet de gegevens zelf: neem de bronregel mee bij hergebruik.",
        "",
        "Deze lijst wordt gemaakt door `code/tekst/figuurbronnen.py` uit de onderschriften in het ",
        "rapport. Pas ze niet met de hand aan.",
        "",
    ]
    for r in rijen:
        regels += [f"## {r['figuur']}. {r['titel']}", ""]
        regels += [f"- Bestanden: `{r['bestand']}.png`, `{r['bestand']}.svg`, "
                   f"gegevens `output/tables/figuurdata/{r['bestand']}.csv`"]
        if r["noot"]:
            regels.append(f"- Noot: {r['noot']}")
        regels.append(f"- Bron: {r['bron'] or '(geen bronregel in het onderschrift)'}")
        regels.append("")
    (FIGUREN / "BRONNEN.md").write_text("\n".join(regels), encoding="utf-8")

    zonder_bron = [r["figuur"] for r in rijen if not r["bron"]]
    print(f"figuurbronnen: {len(rijen)} figuren -> output/figures/BRONNEN.md en bronnen.csv")
    if zonder_bron:
        print(f"LET OP: geen bronregel gevonden bij {', '.join(zonder_bron)}")
    if ontbreekt:
        print(f"LET OP: geen PNG gevonden voor {', '.join(ontbreekt)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
