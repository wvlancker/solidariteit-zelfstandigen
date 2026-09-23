"""
Tekstvergelijking §6.2 (microniveau), referenties en bijlagen: origineel naast herwerkte tekst, alinea per alinea.

    python code/tekst/vergelijk_micro_bijlagen.py   ->  output/tekst/vergelijking_6-2_bijlagen.html

Zelfde werkwijze als vergelijk_hoofdstukken.py (die functie bouw() wordt hergebruikt):
  - Origineel: de opgeschoonde import uit importeer_micro_bijlagen.py (functie schoon_delen).
  - Nieuw: report/sections/*.md (ingevulde templates, dus met de cijfers zoals ze in de PDF staan).
  - Koppeling van alinea's automatisch; soort en toelichting uit de commentaren in de template.
Gewijzigde cijfers zijn in de woord-per-woordmarkering zichtbaar. Tabellen verschijnen als tabel.
"""

import sys
from pathlib import Path

HIER = Path(__file__).resolve().parent
ROOT = HIER.parents[1]
sys.path.insert(0, str(HIER))
import importeer_micro_bijlagen as imb  # noqa: E402
import vergelijk_hoofdstukken as vh  # noqa: E402

TITELS = {
    "06-2_micro.md": "6.2 Microniveau: horizontale en verticale solidariteit",
    "bijlage7_micro_koppels.md": "Bijlage 7 (was Bijlage 6): microresultaten koppels",
    "bijlage1_hervormingen.md": "Bijlage 1: hervormingsmomenten",
    "bijlage2_populaties.md": "Bijlage 2: populatieaantallen",
    "bijlage3_viren.md": "Bijlage 3: manipulaties Viren",
    "bijlage4-5_macro.md": "Bijlage 4 en 5: macro, Z2/W2 en werkgeversbijdragen",
    "referenties.md": "Referenties",
}

if __name__ == "__main__":
    origineel = imb.schoon_delen()
    # de kop 'Referenties' staat in de herwerkte versie in rapport.qmd (Typst), niet in de template
    origineel["referenties.md"] = origineel["referenties.md"].replace("# Referenties", "", 1).strip()
    vh.bouw(
        titels=TITELS,
        origineel=origineel,
        uit=ROOT / "output" / "tekst" / "vergelijking_6-2_bijlagen.html",
        label="§6.2 en bijlagen",
        paginatitel="Tekstvergelijking §6.2 en bijlagen",
        inleiding=("§6.2 is herwerkt op basis van de leesnota (deel B, C, E, J en K) en de nieuwe figuren; de bijlagen "
                   "zijn overgenomen en enkel aangepast waar nodig. Cijfers komen uit de code en staan hier ingevuld. "
                   "De pensioenen zijn herberekend met de loongrens op het loon in plaats van op het pensioen "
                   "(leesnota J1, 18 september 2026). Ongewijzigde alinea's zijn samengevouwen."),
        bronlabel="§6.2, referenties en bijlagen",
        templatelabel="report/templates/06-2_micro.md, referenties.md, bijlage1-7",
        script="vergelijk_micro_bijlagen.py",
    )
