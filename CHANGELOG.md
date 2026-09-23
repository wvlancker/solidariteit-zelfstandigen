# Versies

Elke versie hier komt overeen met een release op GitHub en een gearchiveerde versie op
Zenodo. Het concept-DOI verwijst altijd naar de nieuwste versie; verwijs daarnaar, tenzij u
uitdrukkelijk naar één bepaalde versie wil verwijzen.

**Wat de nummers betekenen.** De cijfers staan voor de inhoud van het rapport, niet voor de
code.

| | Wanneer |
|---|---|
| 2.0.0, 3.0.0, ... | een nieuwe editie: andere jaren, andere gegevens, een herziene analyse |
| 1.1.0, 1.2.0, ... | de analyse wordt uitgebreid, of een cijfer in het rapport verandert |
| 1.0.1, 1.0.2, ... | code, documentatie of opmaak verandert; alle cijfers blijven gelijk |

Een cijfer dat verandert, verandert overal tegelijk: in het rapport, in de figuren, in de
tabellen en in de gegevensbestanden. Deze repository bevat altijd één geldende versie van
elk cijfer, nooit een oudere ernaast. Wie een cijfer uit een eerdere versie nodig heeft,
vindt die versie als apart archief op Zenodo.

---

## 1.0.0 (23 september 2026)

Eerste publieke versie van het rapport. Inhoudelijk gelijk aan 0.1.0; het colofon en
voetnoot 12 in §5 vermelden nu het concept-DOI van het Zenodo-archief,
[10.5281/zenodo.22914842](https://doi.org/10.5281/zenodo.22914842). Verwijs naar dat nummer:
het blijft ook bij latere versies naar de nieuwste verwijzen.

## 0.1.0 (23 september 2026)

Technische release. Zenodo kent een DOI pas toe op het moment dat een release gepubliceerd
wordt, en een DOI vooraf reserveren kan niet. Deze release dient om dat DOI te verkrijgen,
zodat het in het colofon van het rapport kan staan. De PDF in deze release vermeldt daarom
nog geen DOI.

**Dit is niet de gepubliceerde versie van het rapport.** Verwijs naar 1.0.0 of later, of
naar het concept-DOI, dat altijd naar de nieuwste versie verwijst.

De inhoud is voor de rest dezelfde als die van 1.0.0:

- Het volledige rapport, met alle figuren, tabellen en bijlagen.
- De code van de macro-analyse (bijdragen, uitgaven, beroepssolidariteit en nationale
  solidariteit, 2003-2023) en van de micro-analyse (Kakwani-index, equivalentie-,
  vervangings- en garantiegraad, scenario's voor de bijdrageschaal).
- De brongegevens van het macrodeel en de resultaten van de microsimulaties per
  inkomenspositie, met voor elk afgeschermd bronbestand een afgeleide waarmee het resultaat
  toch reproduceerbaar is (zie `DATA.md`).
- De figuren als PNG en SVG, met de geplotte gegevens per figuur en een bronvermelding per
  figuur in `output/figures/BRONNEN.md`.
