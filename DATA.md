# Databeschikbaarheid

Alle figuren, tabellen en bijlagen van dit rapport zijn reproduceerbaar met wat in deze
repository staat. Een deel van de brondata mogen we niet doorgeven. Voor elk van die
bestanden staat hier een afgeleide in de repository die genoeg bevat om hetzelfde resultaat
te krijgen, zonder de onderliggende gegevens bloot te geven.

Controle in één commando:

```
python code/run_all.py          # draait alles opnieuw, met of zonder de afgeschermde bronnen
python code/publicatie_check.py # toont wat er gepubliceerd wordt en wat niet
```

---

## 1. Wat wel gepubliceerd wordt

| Wat | Waar | Opmerking |
|---|---|---|
| Alle code | `code/` | Python en Stata, MIT-licentie |
| Tekst van het rapport | `report/templates/`, `report/sections/`, `output/rapport/rapport.pdf` | CC BY 4.0 |
| Figuren (PNG 300 dpi en SVG) | `output/figures/` | CC BY 4.0, bronvermelding per figuur in `output/figures/BRONNEN.md` |
| Gegevens achter elke figuur | `output/tables/figuurdata/` | één CSV per figuur |
| Tabellen en indicatoren | `output/tables/`, `data/processed/` | inclusief de Excel met alles samen |
| Macrobrondata, ongewijzigd | `data/sources/` (fodsz, nbb, rsvz, statbel, werkboeken) | publieke of publiek gemaakte statistieken, zie §3 |
| Inputreeksen als CSV | `data/raw/` | met `codebook.csv`: herkomst per variabele |
| Resultaten van de microsimulaties | `data/sources/micro/unizo.dta`, `data/raw/micro_*.csv` | de simulatie-uitvoer per inkomenspositie, zie §2 |
| Controles | `output/checks/` | bronverificatie en reproductiecontroles, zie §2.5 |

## 2. Wat niet gepubliceerd wordt, en wat ervoor in de plaats komt

### 2.1 Viren en EUROMOD: het werkboek met de simulaties

`data/sources/micro/unizo_results_final.xlsx` en `data/sources/micro/correctie_pensioenen.xlsx`
bevatten de volledige uitvoer van de microsimulatiemodellen Viren (Teal Partners) en EUROMOD,
met alle tussenstappen per inkomenspositie. Die bestanden mogen we niet doorgeven.

Wel gepubliceerd: de **resultaten** per inkomenspositie, dat is precies wat het rapport
gebruikt.

| Bestand | Inhoud | Gebruikt door |
|---|---|---|
| `data/sources/micro/unizo.dta` | sociale bijdrage per roosterpositie en per type (werknemer, eenmanszaak, vijf vennootschapsvarianten) | m01, m02, m03, m04 |
| `data/raw/micro_werkboek_invoer.csv` | 1.602 bedragen: uitkeringen, referentie-inkomens en pensioenen per gezinstype, risico, type en maand | m05 |
| `data/raw/micro_pensioenen_correctie.csv` | 204 herberekende nettopensioenen (correctieblad, leesnota J1) | m05 |
| `data/raw/micro_schaal_invoer.csv` | per roosterpositie: te benaderen DPI, netto belastbaar inkomen, gesimuleerde bijdrage (eenmanszaak) | m03 |

Wie het werkboek wél heeft, laat de scripts er automatisch van vertrekken: ze schrijven die
CSV's dan opnieuw weg en voeren bovendien een reproductiecontrole uit (elke waarde cel per
cel tegen het werkboek, en Tabel 7 met `code/tekst/controle_tabel7.py`). Zonder het werkboek
wordt die controle overgeslagen en verandert er verder niets aan de uitvoer.

### 2.2 Statbel, administratief beschikbaar inkomen (ADI) 2023

`data/restricted/statbel_adi_histogram_2023.xlsx` is een histogram van de inkomensverdeling
van werknemers en zelfstandigen, via persoonlijke communicatie bezorgd (25 november 2025).
Het bestand zelf wordt niet gedeeld.

Wel gepubliceerd:

| Bestand | Inhoud | Gebruikt door |
|---|---|---|
| `output/tables/figuurdata/fig03_inkomensverdeling.csv` | de aandelen die Figuur 3 toont, per inkomensklasse van €1.000 | `05_figures.py` |
| `data/raw/micro_adi_gewichten.csv` | het gewicht per roosterpositie in de zeven wegingsscenario's | m02 |

Dat zijn geaggregeerde aandelen, geen microgegevens en geen celaantallen. Ze volstaan om
Figuur 3 en de volledige ADI-weging van de Kakwani-index opnieuw te maken. **Let op:** de
figuurdata staan op zes beduidende cijfers, zodat de opnieuw getekende Figuur 3 op een
honderdduizendste van een beeldpunt na samenvalt met de originele.

### 2.3 EU-SILC 2024 (BE-SILC)

De Belgische EU-SILC-microdata zijn alleen toegankelijk met een overeenkomst met Statbel.
De Stata-stap `code/micro/m00_kakwani_gewichten_besilc2024.do` draait op die microdata en
schrijft gewichten per inkomenspositie weg. De uitvoerbestanden met het **aantal
waarnemingen per cel** (`data/raw/kakwani_gewichten_besilc2024.csv`,
`kakwani_gewichten_eq_besilc2024.csv`) en de Stata-logs worden niet gedeeld.

Wel gepubliceerd:

| Bestand | Inhoud | Gebruikt door |
|---|---|---|
| `data/raw/micro_silc_gewichten.csv` | de som van de steekproefgewichten per positie, per variant en groep, zonder celaantallen | m01, m03, 07 |
| `data/raw/micro_silc_groepen.csv` | per variant en groep: totaal aantal waarnemingen, aantal bezette posities, aantal posities met minder dan 10 waarnemingen | m01 (precisiekolommen) |
| `data/raw/kakwani_resultaten_eq_besilc2024.csv` | de Kakwani- en Gini-indices zoals Stata ze berekent, gebruikt om de Python-code te controleren | m01 |
| Het Stata-script zelf | `code/micro/m00_*.do` | documenteert de volledige bewerking op de microdata |

De precisie-informatie is bewust op groepsniveau gehouden: het aantal posities met minder
dan 10 waarnemingen staat er wel, de celaantallen zelf niet.

### 2.4 ABC-verslag 2022/04

`data/sources/abc/abc_verslag_2022-04_solidariteit.pdf` is een publicatie van het Algemeen
Beheerscomité voor het sociaal statuut der zelfstandigen, geen eigen werk. We nemen het niet
op in deze repository. De twee tabellen die het rapport gebruikt staan wel in
`data/raw/abc_2022_tabel2.csv` en `abc_2022_tabel7.csv`, met de precieze vindplaats in
`data/raw/abc_2022_tabel7_bron.md`.

### 2.5 De interne kwaliteitscontrole

De cijfers in dit rapport zijn tot stand gekomen na een controle van een ouder werkboek en
van een conceptversie van de tekst. Daarbij zijn rekenfouten gevonden en rechtgezet. Het
spoor van die controle (een errata, het vergelijkingsscript en zijn uitvoer) staat **niet**
in deze repository, om één reden: die documenten zetten naast elke huidige waarde ook de
oude, verworpen waarde. Er is nooit een versie met die oude cijfers verschenen, dus er valt
publiek niets te corrigeren, en losse verouderde getallen in een publieke repository kunnen
alleen maar verkeerd worden overgenomen. Wat hier staat, is telkens de enige geldende versie.

Niet gepubliceerd: `ERRATA.md`, `code/macro/04_reconcile.py` en zijn uitvoer
`output/checks/rapportcijfers.csv` en `output/checks/reconciliatie_werkboek.csv`. De
pijplijn slaat stap 04 over als het script er niet is, en de Excel in `output/tables/` krijgt
de twee bijbehorende bladen dan niet. Alle andere controles in `output/checks/` gaan wel
mee: die vergelijken niets met een oude versie, ze verifiëren de huidige (overgenomen
brondata tegen de originele bestanden, de reproductie van het werkboek in m05, de bedragen
van Tabel 7, de pensioencorrectie, en de Python-berekening tegen Stata).

Eén kanttekening bij `data/sources/werkboeken/macro_analyses_willem_2026-09-16.xlsx`: dat
werkboek gaat wél mee, want het is de bron waaruit `01_extract_raw.py` de macroreeksen
haalt. In de afgeleide bladen van dat werkboek zitten de rekenfouten nog. Dat is geen
probleem voor de reproductie, omdat de code alleen de **ingevoerde** waarden overneemt en
nooit een formule of een afgeleide cel: `02_verify_sources.py` controleert elke overgenomen
reeks tegen het originele bronbestand van de instelling zelf, en alle berekeningen gebeuren
opnieuw in `03_indicators.py`. Neem dus geen cijfers over uit dat werkboek; neem ze uit
`data/processed/`, `output/tables/` of het rapport.

### 2.6 Werkdocumenten

Niet gepubliceerd, omdat het geen onderzoeksmateriaal is: `archive/` (kopie van de
oorspronkelijke projectmap), `report/import/` (de Word-versie omgezet naar markdown, alleen
gebruikt om de herschreven tekst ermee te vergelijken), `output/tekst/` (die
tekstvergelijkingen en de leesversies), `Claude outputs/` (losse bestanden die tijdens het
werk in de projectmap belandden) en `CLAUDE.md` (werkafspraken).

## 3. Herkomst van de macrogegevens

De bestanden in `data/sources/` zijn ongewijzigde kopieën. `data/sources/MANIFEST.csv` geeft
per bestand het oorspronkelijke pad, de datum van laatste wijziging en een sha256-controlegetal,
zodat te verifiëren valt dat er niets aan veranderd is.

| Bron | Bestand | Status |
|---|---|---|
| FOD Sociale Zekerheid, ontvangsten en uitgaven werknemers en zelfstandigen 2000-2025 | `data/sources/fodsz/` | per e-mail bezorgd (persoonlijke communicatie, 18 april 2025); geaggregeerde overheidsstatistiek |
| Statbel, consumptieprijsindex 1920-2025 | `data/sources/statbel/` | publiek beschikbaar |
| NBB.Stat, werknemers- en werkgeversbijdragen 2003-2023 | `data/sources/nbb/` | publiek beschikbaar |
| RSVZ, samenstelling zelfstandigen 2000-2024 | `data/sources/rsvz/` | overgenomen uit de publieke statistiekendatabase |
| KSZ, populaties (webtoepassing 'globale cijfers') | `data/raw/ksz_populatie.csv` | manueel overgenomen, geen export bewaard; `data/sources/ksz/LEESMIJ.txt` |
| Eigen werkboek macro-analyses | `data/sources/werkboeken/` | eigen werk |

De FOD SZ-tabellen zijn geaggregeerde overheidsstatistieken zonder gegevens over personen.
Ze worden meegepubliceerd omdat het in wezen publieke informatie is. Wie ze in een publicatie
gebruikt, vermeldt 'FOD Sociale Zekerheid (persoonlijke communicatie, 18 april 2025)'.

## 4. Licenties

| Onderdeel | Licentie |
|---|---|
| Code (`code/`, de Lua-filters en het Typst-sjabloon in `report/`) | MIT, zie `LICENSE` |
| Tekst, figuren en tabellen | CC BY 4.0, zie `LICENSE-tekst-en-figuren` |
| Lettertypes Source Serif 4 en Source Sans 3 (`report/_fonts/`) | SIL Open Font License 1.1, zie `report/_fonts/LICENSE_SourceSerif4.md` |
| Gegevens van derden (`data/sources/`, `data/raw/`) | voorwaarden van de oorspronkelijke bron, zie §3 |

## 5. Wat een replicatie oplevert zonder de afgeschermde brondata

Getest op 23 september 2026 door `data/restricted/`, het Viren/EUROMOD-werkboek, het
correctieblad pensioenen en de Stata-uitvoer weg te halen en `python code/run_all.py`
volledig te laten lopen:

- alle CSV's in `data/processed/` komen er identiek uit, op afrondingsruis in de laatste bit
  na (grootste verschil 1,1e-16);
- alle gegevens in `output/tables/figuurdata/` zijn byte voor byte identiek;
- alle figuren zijn identiek, ook Figuur 3 als PNG; alleen in de SVG van Figuur 3 verschuiven
  de coördinaten met 2e-5 beeldpunt (zie §2.2);
- de ingevulde tekst in `report/sections/` is byte voor byte identiek, en de PDF heeft
  dezelfde bestandsgrootte en dezelfde tekst;
- overgeslagen worden alleen de twee controles die de brondata zelf nodig hebben: de
  cel-per-celvergelijking van het werkboek in m05, en de bedragen van Tabel 7
  (`code/tekst/controle_tabel7.py`). De vergelijking van de Python- met de
  Stata-berekening in m01 blijft wel draaien, want `kakwani_resultaten_eq_besilc2024.csv`
  wordt meegepubliceerd.
