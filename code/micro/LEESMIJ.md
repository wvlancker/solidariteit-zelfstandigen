# Microdeel: scripts en herkomst

Deze map bevat de analyses op microniveau die na de narekening van §6.2 (leesnota deel J) zijn gemaakt: de weging van de Kakwani-index, de scenario's voor de bijdrageschaal en de statische opbrengstberekening op basis van het ABC-verslag. De simulaties zelf (Viren voor zelfstandigen, EUROMOD voor werknemers) zijn niet reproduceerbaar: we vertrekken van hun uitvoer zoals die in het werkboek staat.

Alles draait mee met `python code/run_all.py`, behalve de Stata-stap m00. Sinds 17 september 2026 ook de overname van de indicatoren en figuren van §6.2 (m05, m06); sinds 18 september 2026 met de rechtgezette pensioenen.

## Overzicht

| Stap | Script | Taal | Invoer | Uitvoer |
|---|---|---|---|---|
| m00 | `m00_kakwani_gewichten_besilc2024.do` | Stata 19, handmatig | BE-SILC 2024 (niet in repo), `unizo.dta` | `data/raw/kakwani_gewichten_eq_besilc2024.csv`, `kakwani_resultaten_eq_besilc2024.csv`, `.log` |
| m01 | `m01_kakwani_besilc.py` | Python | uitvoer m00, `unizo.dta` | `data/processed/micro_kakwani_besilc2024.csv`, `output/checks/micro_kakwani_stata_vs_python.csv` |
| m02 | `m02_kakwani_adi2023.py` | Python | `data/restricted/statbel_adi_histogram_2023.xlsx`, `unizo.dta` | `data/processed/micro_kakwani_adi2023.csv`, `micro_gewichten_adi2023.csv` |
| m03 | `m03_scenario_bijdrageschaal.py` | Python | werkboek (blad Eénmanszaak_alleenstaande), `unizo.dta`, gewichten m00/m02 | `data/processed/micro_schaal_posities.csv`, `micro_schaal_scenarios.csv`, `micro_schaal_onderkant.csv` |
| m04 | `m04_abc_opbrengst.py` | Python | `data/raw/abc_2022_tabel7.csv`, `abc_2022_tabel2.csv`, `fodsz_bedragen.csv` | `data/processed/abc_opbrengst_statisch.csv` |
| m05 | `m05_werkboek_indicatoren.py` | Python | werkboek, blad `Julie HS & VS`, plus `correctie_pensioenen.xlsx` (J1) | `data/raw/micro_werkboek_invoer.csv`, `data/processed/micro_indicatoren.csv`, `micro_samenvatting.csv`, `micro_tabellen.csv`, `output/checks/micro_werkboek_reproductie.csv`, `micro_pensioenen_correctie.csv`, `data/raw/micro_pensioenen_correctie.csv` |
| m06 | `m06_figuren.py` | Python | uitvoer m05, huisstijl uit `code/macro/05_figures.py` | `output/figures/fig08-fig11`, `figB7-1` tot `figB7-3` (PNG, SVG), `output/tables/figuurdata/` |
| | `common_micro.py` | Python | | mappen, rooster, bijdrageschaal, Kakwani-functies |
| | `verouderd/m00_v1_gewichten_huishoudinkomen.do` | Stata | | eerste versie (huishoudinkomen), vervangen door m00 |

Een stap waarvan de invoer ontbreekt (geen BE-SILC-uitvoer, geen ADI-histogram) slaat zichzelf over met een melding. De rest loopt door.

## Invoer en herkomst

| Bestand in de repository | Oorsprong | Opmerking |
|---|---|---|
| `data/sources/micro/unizo_results_final.xlsx` | SharePoint `Julie Vinck - UNIZO/Micro niveau/Unizo Results Final.xlsx` | Ingeplakte Viren- en EUROMOD-uitvoer. Kopie van 17 september 2026 (enige verschil met de versie van de narekening: hulpcel `Pensioenen!AC79`). |
| `data/sources/micro/unizo.dta` | idem, `unizo.dta` | Bijdragen per roosterpositie, basis Kakwani in het rapport (Tabel 8). |
| `data/sources/abc/abc_verslag_2022-04_solidariteit.pdf` | SharePoint `Bronnen/ABC Verslag 2022-04.pdf` | Publiek advies ABC, 23 december 2022. |
| `data/raw/abc_2022_tabel7.csv`, `abc_2022_tabel2.csv` | overgetypt uit de pdf | Herkomst en controles: `data/raw/abc_2022_tabel7_bron.md`. |
| `data/raw/kakwani_*_besilc2024.*` | uitvoer m00 | Gemaakt door Wim in Stata op 17 september 2026. |
| `data/restricted/statbel_adi_histogram_2023.xlsx` | SharePoint `Histogram cijfers ADI 2023.xlsx` | Niet publiek, niet in Git. |

Hashes en datums van de bronbestanden: `data/sources/MANIFEST.csv`.

## Wat elk script doet

### m00 (Stata): gewichten uit BE-SILC 2024
- Selecteert zelfstandigen (`pl040a` 1 of 2) en werknemers (`pl040a` 3), alleenstaanden (`ht` 5) en koppels met kinderen (`ht` 10-12), zoals de typegevallen.
- Inkomen: gestandaardiseerd netto beschikbaar inkomen `eq_inc20`/12. Twee controles stoppen het script als `eq_inc20` niet gelijk is aan `hy020/eq_ss` of als `eq_ss` niet 1 is voor alleenstaanden. Beide slaagden (log).
- Wijst elke persoon toe aan de dichtstbijzijnde roosterpositie. Iedereen onder €1.550 komt op €1.550, iedereen boven €15.000 op €15.000.
- Drie varianten: **A** gestandaardiseerd inkomen rechtstreeks (hoofdvariant, zelfde inkomensbegrip als de levensstandaard in de typegevallen); **B** en **C** herleiden het gezinsinkomen van koppels naar het individuele inkomen van de zelfstandige in het typegeval (min partnerloon laag of gemiddeld, min Groeipakket). B en C zetten 32-47% van de zelfstandigen onder het rooster en zijn daarom enkel gevoeligheidsanalyses.
- Schrijft gewichten per positie en berekent de Kakwani-indices al in Stata.

### m01: Kakwani gewogen naar BE-SILC
Rekent alle indices opnieuw in Python en stopt als die meer dan 1e-9 van Stata afwijken. Controleert ook dat gelijke gewichten Tabel 8 van het rapport geven (eenmanszaak -0,159, werknemer 0,072). Voegt per groep het aantal waarnemingen en het aantal posities met minder dan 10 waarnemingen toe (zelfstandigen typegevallen: n = 368; 14 van de 25 bezette posities hebben n < 10).

### m02: Kakwani gewogen naar ADI 2023
Onafhankelijke tweede weging op administratieve gegevens. Verdeelt histogramklassen van €1.000 uniform over de intervallen rond de roosterposities en de open topklasse (vanaf €83.500 per jaar) volgens een Pareto-staart. Zes gevoeligheidsscenario's (zie docstring).

### m03: scenario's bijdrageschaal eenmanszaak
Toetst waar de regressiviteit zit, in termen van netto beschikbaar inkomen:
- Controleert dat de schaal (Viren-grenzen, 20,5% / 14,16%, +3,05% beheerskosten) de gesimuleerde bijdragen reproduceert (max. afwijking €0,43).
- Controleert dat de minimumbijdrage nergens op het rooster bindt: het laagste netto belastbaar inkomen van de eenmanszaak is €19.956 per jaar, boven de minimumdrempel €16.861.
- Deelt de posities in zones in en rekent vier schalen door (huidig, geen degressieve schijf, geen plafond, vlak 20,5%), statisch, met drie wegingen (gelijk, BE-SILC A, ADI 2023).

### m04: statische opbrengst op basis van ABC Tabel 7
Extra bijdragen per gemiddelde hoofdberoeper bij afschaffen van het plafond en/of de degressieve schijf, als % van de bijdragen en omgerekend naar euro met twee varianten (bovengrens: alle gewone bijdragen 2023; benadering: aandeel hoofdberoepers). Bruto beroepsinkomen, dus enkel voor uitspraken over opbrengst, niet over verdeling naar draagkracht.

### m05: indicatoren van §6.2 uit het werkboek
- Neemt enkel de invoer over uit `Julie HS & VS`: sociale bijdragen, netto uitkeringen (ziekte, werkloosheid/overbruggingsrecht, pensioen), referentiebudgetten, netto loon partner en Groeipakket, met de celverwijzing per waarde.
- Herberekent bijdrage/draagkracht, vervangingsgraad, equivalentiegraad en garantiegraad, met gemiddelde en variatiecoëfficiënt (populatiestandaardafwijking), en controleert dat dit de 114 indicatorrijen van het werkboek exact reproduceert.
- Past daarna de correcties toe die met de bestaande data kunnen (nu: J8, werkloosheid maand 4-6 bij €2.500). Pensioenen (J1) en bijstandsbodem (J2) bewust ongewijzigd. De correcties en hun gevolgen staan per stuk in de kop van `m05_werkboek_indicatoren.py`.
- Schrijft de cellen van Tabel 8, 9, 10, B7.1 en B7.2 weg. De tekst haalt de cijfers via plaatshouders `{{mi_...}}` in `code/macro/07_tekstcijfers.py` (functie `micro_cijfers`, met de uitleg van de codes).

### m06: figuren van §6.2 en Bijlage 7
Laadt de huisstijl uit `code/macro/05_figures.py` (kleuren, lettertypes, wegschrijven), zodat macro- en microfiguren één stijl hebben. x-as op schaal in euro, eindlabels, referentielijn op 100%.

## Kernresultaten (17 september 2026)

Deze cijfers staan in de leesnota (deel K). Na elke nieuwe run gelden de CSV-bestanden in `data/processed/`, niet deze tabel.

| | Gelijk gewicht | BE-SILC A | ADI 2023 |
|---|---|---|---|
| Kakwani eenmanszaak | -0,159 | 0,057 | 0,038 |
| Kakwani werknemer | 0,072 | 0,183 | 0,228 |
| Kakwani eenmanszaak zonder degressieve schijf | -0,143 | 0,066 | 0,052 |
| Kakwani eenmanszaak zonder plafond | 0,008 | 0,074 | 0,071 |
| Gewicht posities boven het plafond (≥ €5.250) | 56% | 3,3% | 5,8% |

ABC Tabel 7, statisch: plafond weg +6,2% van de bijdragen van hoofdberoepers (≈ €196-313 miljoen), degressieve schijf weg +1,6% (≈ €52-83 miljoen), beide +10,6% (≈ €336-537 miljoen).

## Beperkingen die in de code zitten

- **Statisch.** Scenario's houden het netto belastbaar inkomen en de DPI vast en negeren gedrag.
- **Surveydata aan de top.** BE-SILC telt weinig zelfstandigen boven het plafond (15 waarnemingen vanaf €5.250 in variant A). ADI 2023 is administratief, maar de top is een open klasse.
- **Onder het rooster.** Zelfstandigen onder €1.550 (14% in BE-SILC A) worden op €1.550 gezet. Wie onder de minimumdrempel zit en de minimumbijdrage betaalt, zit niet in de simulaties.
- **Pensioenplafond (leesnota J1).** Rechtgezet op 18 september 2026. m05 leest het blad `Herberekening pensioenen` uit `data/sources/micro/correctie_pensioenen.xlsx` en vervangt daarmee de zes rijen netto pensioen, na de controle tegen het werkboek. De functie `lees_pensioencorrectie()` controleert per cel dat het bruto pensioen gelijk is aan 60% van het begrensde inkomen (minimum, dan maximum = 60% van de loongrens per maand) en dat de impliciete inhouding tussen 0 en 5,55% ligt en stijgt met het pensioen.

## Delen buiten het projectteam

- `data/raw/kakwani_gewichten*_besilc2024.csv` bevat ongewogen aantallen per cel, soms n = 1. Die bestanden staan in `.gitignore`. Controleer de voorwaarden van Statbel voor BE-SILC voordat ze gedeeld worden. De Kakwani-resultaten en logs bevatten enkel geaggregeerde cijfers.
- `data/processed/micro_gewichten_adi2023.csv` is afgeleid van het niet-publieke ADI-histogram en staat ook in `.gitignore`.
