# Hoe solidair is de sociale zekerheid voor zelfstandigen?

Repository van het onderzoeksrapport voor de vzw Academie voor de KMO, Zelfstandigen en Vrije Beroepen (UNIZO).
Auteurs: Wim Van Lancker, Julie Vinck, Willem Goris, Toon Van Havere (KU Leuven, ReSPOND).

**Wat hier staat.** Alle code, gegevens en afgeleiden om elke figuur, elke tabel en elke bijlage van het rapport opnieuw te maken, plus de tekst van het rapport zelf en de opgemaakte PDF. Het macrodeel (§2, §6.1, Bijlage 2, 4, 5 en 6) vertrekt van de brongegevens. Het microdeel (§6.2, Bijlage 7) vertrekt van de uitvoer van de microsimulaties (Viren, EUROMOD): de simulatiemodellen zelf draaien hier niet, hun resultaten per inkomenspositie staan er wel.

Een deel van de brondata mag niet doorgegeven worden (het Viren/EUROMOD-werkboek, het Statbel ADI-histogram, de EU-SILC-microdata). Voor elk van die bestanden staat er een afgeleide in de repository die genoeg bevat om hetzelfde resultaat te krijgen. **`DATA.md` legt dat per bron uit.**

## Reproduceren

```
python -m pip install -r requirements.txt
python code/run_all.py
```

Dat schrijft alle CSV-bestanden, controles, figuren en de Excel opnieuw weg, vult de cijfers in de tekst in en maakt met Quarto de PDF. Er is geen speciale schakelaar nodig: elke stap kijkt zelf of de afgeschermde brondata aanwezig is en vertrekt anders van de meegeleverde CSV-afgeleide. In de uitvoer ziet u welke van de twee het werd, bijvoorbeeld:

```
invoer uit micro_werkboek_invoer.csv (1602 waarden); werkboek niet aanwezig, reproductiecontrole overgeslagen
```

Nodig: Python 3.11 of hoger met de pakketten uit `requirements.txt`, en [Quarto](https://quarto.org) 1.4 of hoger met Typst voor de PDF (ontbreekt Quarto, dan slaat de laatste stap zichzelf over). De Stata-stap met EU-SILC (`code/micro/m00_...do`) draait apart en enkel met toegang tot die microdata; zonder Stata werkt de rest gewoon, zie `code/micro/LEESMIJ.md`.

Een volledige reproductie zonder de afgeschermde brondata is getest en geeft dezelfde uitvoer, op afrondingsruis in de laatste bit na. Zie `DATA.md`, §5.

### Alleen de figuren

`output/figures/` bevat elke figuur als PNG (300 dpi) en als SVG. `output/figures/BRONNEN.md` geeft per figuur de titel, de noot en de bron zoals ze in het rapport staan, plus de citatie voor hergebruik. De gegevens achter elke figuur staan als CSV in `output/tables/figuurdata/`.

## Structuur

```
data/
  sources/      originele bronbestanden, ongewijzigd (FOD SZ, Statbel, NBB, RSVZ, eigen macrowerkboek);
                MANIFEST.csv: oorspronkelijk pad en sha256 per bestand
                micro/unizo.dta: sociale bijdrage per inkomenspositie en per type
  raw/          inputreeksen als CSV + codebook.csv (herkomst per variabele) en de publieke
                afgeleiden van de afgeschermde brondata (micro_*.csv, zie DATA.md)
  processed/    berekende indicatoren
  restricted/   NIET in Git: het Statbel ADI-histogram (Figuur 3 en weging m02)
code/
  run_all.py    draait alles in volgorde
  macro/
    common.py             mappen, basisjaren, definities van 'evolutie'
    bronspec.py           per inputreeks: waar overgenomen, waar oorspronkelijk vandaan
    01_extract_raw.py     werkboek -> data/raw/
    02_verify_sources.py  data/raw/ tegen de originele bronnen
    03_indicators.py      alle berekeningen -> data/processed/
    05_figures.py         figuren -> output/figures/
    06_excel.py           alles in één Excel -> output/tables/
    07_tekstcijfers.py    cijfers in de tekst invullen -> report/sections/, output/tables/tekstcijfers.csv
  publicatie_check.py   wat gaat mee naar GitHub en wat niet (zie DATA.md)
  micro/                  zie code/micro/LEESMIJ.md
    common_micro.py                     mappen, rooster, bijdrageschaal, Kakwani-functies
    m00_kakwani_gewichten_besilc2024.do Stata, handmatig: gewichten uit BE-SILC 2024 -> data/raw/
    m01_kakwani_besilc.py               Kakwani gewogen naar BE-SILC, controle Python = Stata
    m02_kakwani_adi2023.py              Kakwani gewogen naar Statbel ADI 2023 (restricted)
    m03_scenario_bijdrageschaal.py      waar zit de regressiviteit: degressieve schijf, plafond, onderkant
    m04_abc_opbrengst.py                statische opbrengst plafond/degressieve schijf (ABC Tabel 7)
    m05_werkboek_indicatoren.py         indicatoren §6.2 herberekend uit het werkboek, controle, correcties
    m06_figuren.py                      figuren §6.2 en Bijlage 7 in de huisstijl
output/
  figures/      PNG (300 dpi) en SVG per figuur + BRONNEN.md en bronnen.csv (titel, noot, bron, citatie)
  tables/       macro_brondata_en_indicatoren.xlsx, figuurdata/*.csv (de gegevens per figuur)
  checks/       bronverificatie en reproductiecontroles (werkboek, Tabel 7, Python vs. Stata)
  rapport/      rapport.pdf
  tekst/        NIET in Git: tekstvergelijkingen en leesversies voor de auteurs
report/
  templates/    HERWERKTE TEKST met plaatshouders voor cijfers, bv. {{z1_ratio_2023}}: hierin schrijven
  sections/     ingevulde tekst (gegenereerd door 07_tekstcijfers.py, niet bewerken)
  _typst/       sjabloon voor de opmaak; _filters/: Lua-filters voor figuren en tabellen
  _fonts/       Source Serif 4 en Source Sans 3 (SIL Open Font License)
  import/       NIET in Git: de Word-versie als markdown, enkel voor de tekstvergelijkingen
archive/        NIET in Git: kopie van de oorspronkelijke projectmap
DATA.md         databeschikbaarheid: wat wel en niet meegepubliceerd wordt, en waarom
CITATION.cff    hoe naar dit werk verwijzen (plus plaats voor het Zenodo-DOI)
.zenodo.json    metadata voor het Zenodo-archief, afgeleid uit CITATION.cff
CHANGELOG.md    wat er per versie veranderd is
LICENSE         MIT, voor de code
LICENSE-tekst-en-figuren   CC BY 4.0, voor de tekst, figuren en tabellen
CLAUDE.md       NIET in Git: werkafspraken en projectstand
```

## Van bron tot figuur

1. **Bron.** De originele bestanden (FOD SZ-tabellen, Statbel-CPI, NBB.Stat) staan ongewijzigd in `data/sources/`.
2. **Overname.** De inputs worden met code uit het werkboek van Willem gehaald (`01_extract_raw.py`), niet met de hand gekopieerd. Formules uit het werkboek worden niet overgenomen, enkel ingevoerde waarden.
3. **Controle.** `02_verify_sources.py` vergelijkt elke overgenomen reeks met het originele bronbestand.
4. **Berekening.** Alle berekeningen gebeuren opnieuw in `03_indicators.py`, met commentaar bij elke stap.
5. **Herkomst.** `data/raw/codebook.csv` geeft voor elke variabele de volledige keten: organisatie, bronbestand en locatie, plaats in het werkboek, datum geraadpleegd en opmerkingen.

### Twee bronnen zonder bronbestand

- **KSZ-populaties** (n11 tot n143). De waarden zijn indertijd manueel overgenomen uit de webtoepassing 'globale cijfers'. Er is geen export bewaard, dus deze reeksen kunnen niet automatisch geverifieerd worden. **Actie:** de reeks opnieuw exporteren (4e kwartaal, 2003-2023) en in `data/sources/ksz/` zetten.
- **RSVZ-samenstelling.** De waarden staan in `Samenstelling zelfstandigen.xlsx`, zonder export van de statistiekendatabase. Alleen het aantal vennootschappen is gecontroleerd tegen een tweede plaats in het werkboek.

## Tekst en cijfers

Cijfers staan in de tekst nooit als overgetypte getallen, maar als plaatshouder in `report/templates/*.md`. `07_tekstcijfers.py` berekent ze en vult ze in. `{{sleutel|daling}}` en `{{sleutel|stijging}}` tonen de waarde zonder teken en geven een fout als de richting niet klopt met het werkwoord in de zin. Alle beschikbare sleutels met hun waarde en omschrijving staan in `output/tables/tekstcijfers.csv`. Een nieuw cijfer nodig? Voeg het toe in `07_tekstcijfers.py`.

## Definities

| Code | Nomenclatuurposities | Betekenis |
|---|---|---|
| W1 | n11 + n141 | hoofdactiviteit in loondienst |
| W2 | n11 + n141 + n142 + n143 | alle werkenden in loondienst |
| Z1 | n12 + n13 + n142 + n143 | hoofdactiviteit als zelfstandige/helper |
| Z2 | n12 + n13 + n141 + n142 + n143 | alle werkenden als zelfstandige/helper |

- **Reëel.** Nominaal bedrag × (CPI 2024 / CPI jaar t), dus in prijzen van 2024.
- **Beroepssolidariteit.** Reële bijdragen per capita / reële uitgaven per capita. Deflator en populatie vallen hier weg: de ratio is gelijk aan nominale bijdragen / nominale uitgaven.
- **Nationale solidariteit.** Aandeel van de toelagen van publieke overheden plus de alternatieve financiering in de totale lopende ontvangsten.
- **Evolutie tussen twee jaren.** Altijd de relatieve verandering (eind / begin − 1), nooit het verschil in indexpunten. Zie `relatieve_verandering()` in `code/macro/common.py`.

## Licenties en citatie

| Onderdeel | Licentie |
|---|---|
| Code (`code/`, de Lua-filters en het Typst-sjabloon in `report/`) | MIT, zie `LICENSE` |
| Tekst, figuren en tabellen | CC BY 4.0, zie `LICENSE-tekst-en-figuren` |
| Lettertypes in `report/_fonts/` | SIL Open Font License 1.1 |
| Gegevens van derden | voorwaarden van de oorspronkelijke bron, zie `DATA.md` |

## Versies

`CHANGELOG.md` geeft per versie wat er veranderd is. Elke versie is een release op GitHub en
wordt door Zenodo gearchiveerd met een eigen DOI; het concept-DOI verwijst altijd naar de
nieuwste. Deze repository bevat altijd één geldende versie van elk cijfer, nooit een oudere
ernaast: wie een cijfer uit een eerdere versie nodig heeft, vindt die versie op Zenodo.

Verwijzen naar dit werk: zie `CITATION.cff`, of

> Van Lancker, W., Vinck, J., Goris, W., & Van Havere, T. (2026). *Hoe solidair is de sociale zekerheid voor zelfstandigen?* Leuven: KU Leuven, ReSPOND.
