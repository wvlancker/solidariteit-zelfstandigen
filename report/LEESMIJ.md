# Het rapport opmaken als PDF

## In één zin

De tekst staat in markdown (`report/sections/`), `rapport.qmd` legt de volgorde vast, en **Quarto** maakt er met **Typst** een PDF van in rapportvorm: `quarto render` → `output/rapport/rapport.pdf`.

## Keten

```
report/templates/*.md   tekst met plaatshouders {{sleutel}}          (hier schrijf je)
        │  code/macro/07_tekstcijfers.py
        ▼
report/sections/*.md    tekst met ingevulde cijfers                   (gegenereerd)
        │  rapport.qmd: metadata + volgorde van de hoofdstukken
        │  report/_filters/figuren.lua: figuren herkennen en nummeren
        │  report/_typst/typst-template.typ: volledige opmaak
        ▼
output/rapport/rapport.pdf
```

## Installatie (eenmalig)

- **Quarto.** Het is een apart programma, geen Python-pakket. Gebruik op een beheerde Windows-computer zonder administratorrechten de zip-versie van https://quarto.org/docs/download/: uitpakken en de map `bin` aan het PATH van de gebruiker toevoegen. Typst zit in Quarto zelf, er is niets anders nodig (geen LaTeX).
- **Lettertypes.** Die zitten in `report/_fonts/` en worden van daaruit gebruikt. Niets te installeren.
- Getest met Quarto 1.7.32 (Typst 0.13).

## Gebruik

```
quarto render                # vanuit de root van het project
python code/run_all.py       # volledige keten, de PDF is stap 08
```

## Afspraken voor de markdown in `report/sections/`

| Wat | Hoe |
|---|---|
| Hoofdstuk, paragraaf, subparagraaf | `#`, `##`, `###`. Nummering gebeurt automatisch, typ geen nummers. |
| Figuur | Vier alinea's na elkaar: `**Figuur N.** bijschrift`, dan `![](../../output/figures/...png)`, dan `Noot: ...`, dan `Bron: ...`. De filter maakt er één figuur van: bijschrift boven, noot en bron eronder, nooit gesplitst over twee pagina's. |
| Figuurnummer | De PDF nummert zelf. Het nummer in de markdown wordt enkel gecontroleerd: wijkt het af, dan verschijnt bij het renderen een `WAARSCHUWING figuren.lua`. |
| Bijlagefiguur | `**Figuur B7.1.** bijschrift`: een nummer met een letter telt niet mee in de doorlopende nummering; de filter neemt het nummer letterlijk over en zet de figuur in `#bijlagefiguur` (typst-template). |
| Tabel | `**Tabel N.** bijschrift`, dan een pipe-tabel, dan `Noot: ...` en `Bron: ...`. De filter `tabellen.lua` maakt er één blok van: bijschrift boven (het blijft bij de tabel), noot en bron eronder in kleinere letter. De streepjes in de scheidingsregel bepalen de kolombreedte; kolommen smaller dan 9% worden opgetrokken en alle breedtes worden herschaald naar de volle tekstbreedte, zodat geen kolom nog woord per woord afbreekt. Cijferkolommen rechts uitlijnen met `---:`. |
| Tabelnummer | Zoals bij de figuren: de markdown wordt gecontroleerd tegen de telling (`WAARSCHUWING tabellen.lua`). Bijlagetabellen (`**Tabel B3.1.**`) tellen niet mee. |
| Ongenummerde hoofdstukkop (Referenties) | In `rapport.qmd` als Typst-blok `#heading(level: 1, numbering: none)[...]`; een markdownkop met `{.unnumbered}` kan in Typst geen nieuwe pagina openen. |
| Voetnoot | `[^label]` in de tekst en `[^label]: tekst` eronder. Labels moeten uniek zijn over het **hele** rapport. Gebruik daarom een voorvoegsel per sectie, bijvoorbeeld `[^61-breuk]`. |
| Pagina-einde | `{{< pagebreak >}}` |

## Opmaak aanpassen

Alles staat in `report/_typst/typst-template.typ`, met commentaar per onderdeel: kleuren en lettertypes bovenaan, dan pagina, koppen, figuren, voetnoten, tabellen, titelpagina, colofon en inhoudsopgave. Titel, auteurs, datum en status staan in de kop van `rapport.qmd`.

Keuzes die op 18 september 2026 zijn vastgelegd:

- **Lopende tekst 11,5 pt** (was 10,5), met de koppen, bijschriften, tabellen en voetnoten in verhouding mee. Op A4 met 16 cm tekstbreedte geeft dat ongeveer 80 tekens per regel: comfortabel op scherm en in druk.
- **Geen lijn onder de titels.** Hoofdstuktitels en de titel van de inhoudsopgave staan zonder streep; de dunne lijn onder de koptekst blijft, die scheidt de koptekst van de tekst.
- **Voetnoten**: het nummer staat tegen de linkermarge, de tekst ernaast als blok (hangende inspringing).
- **Bijlagen** beginnen elk op een nieuwe pagina: elke kop van niveau twee die met "Bijlage" begint, krijgt een pagina-einde.
- **Figuren en tabellen** krijgen 2,2 em ruimte boven en onder. Die ruimte is zwak: begint het blok bovenaan een pagina, dan valt ze weg.
- **Koptekst**: lange hoofdstuktitels worden afgekapt op de dubbele punt ("5 Methodologie"), zodat de koptekst één regel blijft.
- **Voettekst**: enkel het paginanummer, rechts. De vermelding "Ontwerpversie, niet verspreiden" staat nog op de titelpagina, niet meer op elke pagina.
- **Titelpagina**: logo's van de KU Leuven en ReSPOND bovenaan (`report/_logos/`, uit het oorspronkelijke Word-rapport), zonder streepje onder de titel.
- **Hoogte van de figuren**: drie panelen boven elkaar worden hoogstens 7,9 inch (ongeveer 20 cm), zodat bijschrift, figuur en noot samen op één pagina passen. Staat als `PANEELHOOGTE` in `code/micro/m06_figuren.py`.

## Nog te doen

- **Verwijzingen naar figuren en tabellen.** Nu nog met de hand ("Figuur 4"). Quarto kan dat automatisch (`@fig-...`), zodat nummers nooit meer verkeerd staan. Voorstel: omzetten zodra alle hoofdstukken erin zitten.
- **Literatuurlijst.** Nu als gewone tekst. Kan automatisch met een `.bib`-bestand en een citatiestijl (bv. APA).
- **Tabellen.** De kolombreedtes en de noten zijn opgelost (zie hierboven). Blijft over: Tabel 4 en 7 lopen over twee pagina's; de kop wordt wel herhaald. Splitsen of liggend zetten kan als dat stoort.
- **Word-versie.** Kan uit dezelfde bronnen, met één extra formaat in `_quarto.yml` (`docx` met een referentiedocument), als de opdrachtgever dat vraagt.
