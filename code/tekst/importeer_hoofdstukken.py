"""
Eenmalige overname van hoofdstuk 1 tot 5 uit de geïmporteerde tekst van het oorspronkelijke rapport.

    python code/tekst/importeer_hoofdstukken.py

Leest report/import/rapport_finaal_TC_volledig.md (Word-bestand omgezet met pandoc, bijgehouden
wijzigingen aanvaard) en schrijft per hoofdstuk een template in report/templates/:

    01_inleiding.md, 02_context.md, 03_solidariteit.md, 04_sociaal_statuut.md, 05_methodologie.md

Wat het script doet, en niets meer:
  - Word-restanten weghalen (ankers, lege vetgedrukte regels, gemarkeerde lege stukken)
  - verloren tabelnummers herstellen ("Tabel ." -> "**Tabel 1.**", in volgorde)
  - figuren in de afgesproken vorm zetten: "**Figuur N.** bijschrift", afbeelding, Noot, Bron
  - de voetnoten die in het hoofdstuk voorkomen onderaan het hoofdstuk zetten

Inhoudelijke wijzigingen gebeuren daarna met de hand in de templates, telkens met een
commentaar <!-- wijziging: soort | toelichting --> vlak boven de gewijzigde alinea.
Daarom weigert het script een bestaande template te overschrijven.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BRON = ROOT / "report" / "import" / "rapport_finaal_TC_volledig.md"
DOEL = ROOT / "report" / "templates"

HOOFDSTUKKEN = [  # (bestandsnaam, kop in het bronbestand)
    ("01_inleiding.md", "# Inleiding"),
    ("02_context.md", "# De maatschappelijke context"),
    ("03_solidariteit.md", "# Solidariteit in de sociale zekerheid"),
    ("04_sociaal_statuut.md", "# Het sociaal statuut van de zelfstandigen"),
    ("05_methodologie.md", "# Methodologie: operationaliseren van de verschillende dimensies van solidariteit"),
]
EINDE = "# Resultaten"

# Nieuwe figuren (code/macro/05_figures.py), pad relatief tegenover report/sections/
FIGUREN = {
    "1": "../../output/figures/fig01_werkende_bevolking.png",
    "2": "../../output/figures/fig02_samenstelling_zelfstandigen.png",
    "3": "../../output/figures/fig03_inkomensverdeling.png",
}


def schoon_hoofdstukken():
    """Geeft {bestandsnaam: opgeschoonde tekst} terug, zonder iets te schrijven.
    Ook gebruikt door vergelijk_hoofdstukken.py als 'origineel'."""
    uit = {}
    tekst = BRON.read_text(encoding="utf-8")
    regels = tekst.splitlines()
    voetnoten = dict(re.findall(r"^\[\^(\d+)\]: (.+)$", tekst, flags=re.M))

    # begin- en eindregel van elk hoofdstuk (eerste voorkomen NA de inhoudsopgave)
    def zoek(kop, vanaf=0):
        for i in range(vanaf, len(regels)):
            if regels[i].rstrip() == kop:
                return i
        raise ValueError(kop)

    start_inleiding = zoek("# Inleiding")
    posities = [zoek(k, start_inleiding) for _, k in HOOFDSTUKKEN] + [zoek(EINDE, start_inleiding)]

    tabelnummer = 0
    for (naam, _), b, e in zip(HOOFDSTUKKEN, posities[:-1], posities[1:]):
        stuk = "\n".join(regels[b:e])

        # Word-restanten
        stuk = re.sub(r'<span id="[^"]*" class="anchor"></span>', "", stuk)
        stuk = re.sub(r"\*\*<span class=\"mark\">\s*</span>\*\*", "", stuk)
        stuk = re.sub(r"^\*\*\s*\n\*\*\s*$", "", stuk, flags=re.M)
        stuk = re.sub(r"^(#+ .*?)[ \t]+$", r"\1", stuk, flags=re.M)

        # tabelnummers
        def tabel(m):
            nonlocal tabelnummer
            tabelnummer += 1
            return f"**Tabel {tabelnummer}.** {m.group(1)}"
        stuk = re.sub(r"^Tabel \. (.+)$", tabel, stuk, flags=re.M)

        # figuren: bijschrift vet, afbeelding erna
        def figuur(m):
            nr, bijschrift = m.group(1), m.group(2)
            return f"**Figuur {nr}.** {bijschrift}\n\n![]({FIGUREN[nr]})"
        stuk = re.sub(r"^Figuur (\d+)\. (.+)$", figuur, stuk, flags=re.M)

        # voetnoten van dit hoofdstuk
        nummers = sorted(set(re.findall(r"\[\^(\d+)\](?!:)", stuk)), key=int)
        stuk = re.sub(r"\n{3,}", "\n\n", stuk).strip()
        if nummers:
            stuk += "\n\n" + "\n\n".join(f"[^{n}]: {voetnoten[n]}" for n in nummers)

        uit[naam] = stuk
    return uit


def main():
    bestaand = [n for n, _ in HOOFDSTUKKEN if (DOEL / n).exists()]
    if bestaand and "--forceer" not in sys.argv:
        raise SystemExit(f"Bestaat al, niet overschreven: {bestaand}. Gebruik --forceer om toch te overschrijven.")
    kop = ("<!--\nTEMPLATE, overgenomen uit Rapport UNIZO_finaal_TC.docx met code/tekst/importeer_hoofdstukken.py.\n"
           "Wijzigingen ten opzichte van het origineel staan aangeduid met een commentaar wijziging: vlak boven de alinea.\n-->\n\n")
    for naam, stuk in schoon_hoofdstukken().items():
        (DOEL / naam).write_text(kop + stuk + "\n", encoding="utf-8")
        print(f"geschreven: report/templates/{naam}")


if __name__ == "__main__":
    main()
