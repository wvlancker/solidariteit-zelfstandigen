# Herkomst `abc_2022_tabel7.csv`

- **Document:** Algemeen Beheerscomité voor het sociaal statuut der zelfstandigen (ABC), *Verslag 2022/04* over de solidariteit in het sociaal statuut, goedgekeurd 23 december 2022. Kopie: `data/sources/abc/abc_verslag_2022-04_solidariteit.pdf` (origineel: SharePoint `Julie Vinck - UNIZO/Bronnen/ABC Verslag 2022-04.pdf`).
- **Tabel:** Tabel 7, "Aandeel van de verschillende inkomensgroepen in de inkomens-, bijdragen- en uitkeringsmassa van de zelfstandigen in hoofdberoep, 2019", p. 16. Gemiddeld inkomen en gemiddelde bijdrage staan ook in Tabel 4, p. 12 ("raming op grond van de inkomsten van het jaar 2019, geïndexeerd op het jaar 2021"). Bron volgens het ABC: DG BeSoc, FOD Sociale Zekerheid.
- **Overname:** met de hand overgetypt uit de pdf (de tabel is in de pdf niet als tekst uitleesbaar), gecontroleerd tegen een weergave van p. 16 op 17 september 2026. Percentages als fractie.
- **Populatie:** enkel zelfstandigen in hoofdberoep. Inkomens van 2019, geïndexeerd naar 2021; de grenzen (€14.042, €60.638, €89.361) zijn die van 2021.
- **Bedragen:** jaarbedragen in euro. De gemiddelde bijdrage bevat geen beheerskosten: de gemiddelde bijdrage boven het plafond (€16.498) is precies de maximumbijdrage 20,5% x €60.638 + 14,16% x (€89.361 - €60.638). `m04` controleert dat.
- **Controles in `code/micro/m04_abc_opbrengst.py`:** aandelen tellen op tot 1; aandeel personen x gemiddeld inkomen / totaal gemiddelde reproduceert het aandeel in de inkomensmassa (binnen afronding).

# Herkomst `abc_2022_tabel2.csv`

- **Tabel:** Tabel 2, "Inkomenshoogte van zelfstandigen volgens bijdragedrempels, volledige populatie en hoofdberoepers, 2019", p. 7 van hetzelfde ABC-verslag. Bron volgens het ABC: dienst Statistieken RSVZ.
- **Overname:** met de hand overgetypt uit de tekstlaag van de pdf, 17 september 2026.
- **Opmerking:** de indeling volgt de bijdragedrempels die in 2019 golden (inkomens van 2016), niet de grenzen van 2021 uit Tabel 7. Daarom verschilt het aandeel boven de maximumgrens (4,7% hier, 3,5% in Tabel 7). `m04` gebruikt uit deze tabel enkel het aantal hoofdberoepers (472.049) om de bijdragemassa van hoofdberoepers te benaderen.
