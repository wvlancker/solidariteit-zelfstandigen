"""
Eenmalige overname van §6.2 (microniveau), de referenties en de bijlagen uit de geïmporteerde
tekst van het oorspronkelijke rapport.

    python code/tekst/importeer_micro_bijlagen.py            (weigert bestaande templates te overschrijven)

Zelfde werkwijze als importeer_hoofdstukken.py (hoofdstuk 1 tot 5): enkel Word-restanten
opruimen, verloren nummers van tabellen en figuren herstellen, figuren in de afgesproken vorm
zetten en de voetnoten onderaan het deel plaatsen. Inhoudelijke wijzigingen gebeuren daarna met
de hand in de templates, telkens met <!-- wijziging: soort | toelichting --> erboven.

Delen (template <- stuk van het origineel):
    06-2_micro.md                    ## Microniveau ... tot # Conclusie
    referenties.md                   # Referenties  tot # Bijlagen
    bijlage1_hervormingen.md         ## Bijlage 1   tot ## Bijlage 2
    bijlage2_populaties.md           ## Bijlage 2   tot ## Bijlage 3
    bijlage3_viren.md                ## Bijlage 3   tot ## Bijlage 4
    bijlage4-5_macro.md              ## Bijlage 4   tot ## Bijlage 6
    bijlage7_micro_koppels.md        ## Bijlage 6 (koppels) tot de voetnoten; wordt Bijlage 7

De functie schoon_delen() geeft de opgeschoonde originelen terug zonder te schrijven; die
gebruikt vergelijk_micro_bijlagen.py als 'origineel' voor de tekstvergelijking.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BRON = ROOT / "report" / "import" / "rapport_finaal_TC_volledig.md"
DOEL = ROOT / "report" / "templates"

# (template, beginkop, eindkop). Koppen zoals ze in het bronbestand staan (na de inhoudsopgave).
DELEN = [
    ("06-2_micro.md", "## Microniveau: horizontale solidariteit en verticale solidariteit", "# Conclusie"),
    ("referenties.md", "# Referenties", "# Bijlagen"),
    ("bijlage1_hervormingen.md", "## Bijlage 1: Belangrijkste hervormingsmomenten in het sociaal statuut van zelfstandigen in de afgelopen 25 jaar",
     "## Bijlage 2: Populatieaantallen werknemers en zelfstandigen"),
    ("bijlage2_populaties.md", "## Bijlage 2: Populatieaantallen werknemers en zelfstandigen", "## Bijlage 3: Manipulaties Viren"),
    ("bijlage3_viren.md", "## Bijlage 3: Manipulaties Viren",
     "## Bijlage 4: Resultaten solidariteit op macroniveau, beroepssolidariteit, populatiedefinities Z2 en W2"),
    ("bijlage4-5_macro.md", "## Bijlage 4: Resultaten solidariteit op macroniveau, beroepssolidariteit, populatiedefinities Z2 en W2",
     "## Bijlage 6: Resultaten solidariteit op microniveau, horizontale en verticale solidariteit voor koppels met 2 kinderen (2 en 4 jaar)"),
    ("bijlage7_micro_koppels.md",
     "## Bijlage 6: Resultaten solidariteit op microniveau, horizontale en verticale solidariteit voor koppels met 2 kinderen (2 en 4 jaar)",
     None),  # tot aan de voetnoten
]

# Figuren in het origineel -> nieuwe figuur (pad relatief tegenover report/sections/)
FIGUREN = {
    "8": "../../output/figures/fig08_bijdragen_draagkracht.png",
    "9": "../../output/figures/fig09_equivalentiegraad_alleenstaanden.png",
    "10": "../../output/figures/fig10_vervangingsgraad_alleenstaanden.png",
    "11": "../../output/figures/fig11_garantiegraad_alleenstaanden.png",
    "B4.1": "../../output/figures/figB4-1_beroepssolidariteit_Z2_W2.png",
    "B4.2": "../../output/figures/figB4-2_vennootschappen_Z2.png",
    "B5.1": "../../output/figures/figB5-1_werknemers_werkgeversbijdragen.png",
    "B6.1": "../../output/figures/figB7-1_equivalentiegraad_koppels.png",
    "B6.2": "../../output/figures/figB7-2_vervangingsgraad_koppels.png",
    "B6.3": "../../output/figures/figB7-3_garantiegraad_koppels.png",
}


def schoon_delen():
    """{template: opgeschoonde tekst van het origineel}, zonder iets te schrijven."""
    tekst = BRON.read_text(encoding="utf-8")
    regels = [r.rstrip() for r in tekst.splitlines()]
    voetnoten = dict(re.findall(r"^\[\^(\d+)\]: (.+)$", tekst, flags=re.M))
    eerste_voetnoot = next(i for i, r in enumerate(regels) if re.match(r"^\[\^\d+\]: ", r))
    start = regels.index("# Inleiding", 30)          # na de inhoudsopgave

    def zoek(kop, vanaf):
        for i in range(vanaf, len(regels)):
            if regels[i] == kop:
                return i
        raise ValueError(kop)

    uit = {}
    for naam, begin, einde in DELEN:
        b = zoek(begin, start)
        e = zoek(einde, b + 1) if einde else eerste_voetnoot
        stuk = "\n".join(regels[b:e])

        # Word-restanten
        stuk = re.sub(r'<span id="[^"]*" class="anchor"></span>', "", stuk)
        stuk = re.sub(r'<span class="mark">\s*</span>', "", stuk)
        stuk = re.sub(r"^\*\*\s*$", "", stuk, flags=re.M)
        stuk = re.sub(r"^\*{4}\s*$", "", stuk, flags=re.M)
        stuk = re.sub(r"^## \s*$", "", stuk, flags=re.M)

        # verloren tabelnummers in §6.2 (Tabel 8, 9, 10: na Tabel 7 in §5)
        teller = iter(range(8, 20))
        stuk = re.sub(r"^Tabel \. (.+)$", lambda m: f"**Tabel {next(teller)}.** {m.group(1)}", stuk, flags=re.M)
        # bijlagetabellen: 'Tabel B2.1: ...' of 'Tabel B6.1. ...'
        stuk = re.sub(r"^Tabel (B\d+\.\d+)[:.] (.+)$", r"**Tabel \1.** \2", stuk, flags=re.M)

        # figuren: 'Figuur . bijschrift' (nummer verloren) in §6.2, 'Figuur B4.1. bijschrift' in de bijlagen.
        # 'Figuur 9. Vervolg' (tweede helft van een figuur over twee pagina's) verdwijnt: de nieuwe
        # figuren staan telkens op één pagina.
        stuk = re.sub(r"^Figuur (\d+|B\d+\.\d+)\. Vervolg$", "", stuk, flags=re.M)
        fig_nr = iter(["8", "9", "10", "11"])

        def figuur(m):
            nr = m.group(1) or next(fig_nr)
            return f"**Figuur {nr}.** {m.group(2)}\n\n![]({FIGUREN[nr]})"
        stuk = re.sub(r"^Figuur (B\d+\.\d+)?\.? ?(?<=\. )(.+)$", figuur, stuk, flags=re.M)

        nummers = sorted(set(re.findall(r"\[\^(\d+)\](?!:)", stuk)), key=int)
        stuk = re.sub(r"\n{3,}", "\n\n", stuk).strip()
        if nummers:
            stuk += "\n\n" + "\n\n".join(f"[^{n}]: {voetnoten[n]}" for n in nummers)
        uit[naam] = stuk
    return uit


def main():
    delen = schoon_delen()
    bestaand = [n for n in delen if (DOEL / n).exists()]
    if bestaand and "--forceer" not in sys.argv:
        raise SystemExit(f"Bestaat al, niet overschreven: {bestaand}. Gebruik --forceer om toch te overschrijven.")
    kop = ("<!--\nTEMPLATE, overgenomen uit Rapport UNIZO_finaal_TC.docx met code/tekst/importeer_micro_bijlagen.py.\n"
           "Wijzigingen ten opzichte van het origineel staan aangeduid met een commentaar wijziging: vlak boven de alinea.\n-->\n\n")
    for naam, stuk in delen.items():
        (DOEL / naam).write_text(kop + stuk + "\n", encoding="utf-8")
        print(f"geschreven: report/templates/{naam}")


if __name__ == "__main__":
    main()
