// ============================================================================
// Opmaak van het rapport (Typst). Wordt door Quarto gebruikt via _quarto.yml.
//
// Alles wat de vormgeving bepaalt staat in dit ene bestand:
//   1. kleuren en lettertypes
//   2. hulpfuncties (figuurnoot)
//   3. de functie `rapport`: pagina, tekst, koppen, figuren, voetnoten,
//      tabellen, kop- en voettekst, titelpagina, colofon, inhoudsopgave
// ============================================================================

// ---- 1. Kleuren en lettertypes ---------------------------------------------
#let inkt      = rgb("#1b1b19")   // lopende tekst
#let inkt2     = rgb("#55544f")   // noten, kop- en voettekst
#let lijn      = rgb("#c9c7bf")   // dunne lijnen
#let nummer    = rgb("#8f8d85")   // grote hoofdstuknummers
#let serif     = ("Source Serif 4", "Libertinus Serif")
#let sans      = ("Source Sans 3", "DejaVu Sans")

// ---- 2. Hulpfuncties --------------------------------------------------------

// Platte tekst uit een stuk inhoud halen. Nodig om te zien of een kop met "Bijlage" begint.
#let platte_tekst(el) = {
  let t = if type(el) == str { el }
    else if type(el) == content {
      if el.has("text") { el.text }
      else if el.has("children") { el.children.map(platte_tekst).join("") }
      else if el.has("body") { platte_tekst(el.body) }
      else { "" }
    } else { "" }
  if t == none { "" } else { t }
}

// Noot en Bron onder een figuur (de filter _filters/figuren.lua zet ze hierin)
#let figuurnoot(body) = block(width: 100%, above: 0.7em)[
  #set align(left)
  #set par(justify: false, leading: 0.48em, spacing: 0.5em)
  #set text(font: sans, size: 8.5pt, fill: inkt2)
  #body
]

// Figuur in een bijlage ("Figuur B4.1."): eigen nummer uit de markdown, buiten de doorlopende
// nummering van het rapport. Zelfde opmaak als de gewone figuren: bijschrift boven, noot eronder,
// nooit over twee pagina's gesplitst. (De filter _filters/figuren.lua roept dit aan.)
#let bijlagefiguur(nummer: "", bijschrift, inhoud) = block(width: 100%, breakable: false, above: 1.4em, below: 1.6em)[
  // merkteken voor de lijst van figuren (zie lijst_van hieronder)
  #metadata((soort: "Figuur", nummer: nummer, titel: bijschrift)) <lijstitem>
  #block(width: 100%, below: 0.7em)[
    #set align(left)
    #set par(justify: false, leading: 0.5em)
    #set text(font: sans, size: 10.5pt)
    #text(weight: "semibold")[Figuur #nummer.]#h(0.35em)#bijschrift
  ]
  #set par(justify: false, leading: 0.48em, spacing: 0.5em)
  #show par: set text(font: sans, size: 8.5pt, fill: inkt2)
  #inhoud
]

// Tabel met bijschrift boven en Noot/Bron eronder (de filter _filters/tabellen.lua zet ze
// hierin). Het bijschrift is 'sticky', zodat het nooit alleen onderaan een pagina blijft staan;
// het blok zelf mag wel over twee pagina's lopen, want sommige tabellen zijn lang.
// wijziging: opmaak | 22 september 2026: breakable: false, zodat een tabel met bijschrift en noten
// niet over twee pagina's loopt (Tabel 4 en 8). Alle tabellen zijn korter dan een pagina.
#let tabelblok(nummer: "", bijschrift, inhoud) = block(width: 100%, above: 2.2em, below: 2.2em, breakable: false)[
  // merkteken voor de lijst van tabellen (zie lijst_van hieronder)
  #metadata((soort: "Tabel", nummer: nummer, titel: bijschrift)) <lijstitem>
  #block(width: 100%, below: 0.7em, sticky: true)[
    #set align(left)
    #set par(justify: false, leading: 0.5em)
    #set text(font: sans, size: 10.5pt)
    #text(weight: "semibold")[Tabel #nummer.]#h(0.35em)#bijschrift
  ]
  #inhoud
]

// Lijst van figuren of tabellen (22 september 2026, op vraag van Wim). Wordt aangeroepen
// in rapport.qmd: #lijst_van("Figuur") en #lijst_van("Tabel").
// - Figuren in de lopende tekst zijn gewone Quarto-figuren (kind "quarto-float-fig"),
//   met hun nummer uit de teller van Typst.
// - Bijlagefiguren en alle tabellen komen uit #bijlagefiguur en #tabelblok, die een
//   merkteken <lijstitem> achterlaten met hun nummer en bijschrift.
// Elke regel: "Tabel 8." | bijschrift | paginanummer, en is klikbaar in de PDF.
#let lijst_van(soort) = context {
  let items = ()
  if soort == "Figuur" {
    for f in query(figure.where(kind: "quarto-float-fig")) {
      items.push((nummer: str(f.counter.at(f.location()).first()), titel: f.caption.body,
                  plek: f.location()))
    }
  }
  for m in query(<lijstitem>) {
    if m.value.soort == soort {
      items.push((nummer: m.value.nummer, titel: m.value.titel, plek: m.location()))
    }
  }
  set text(font: sans, size: 9.5pt)
  set par(justify: false, leading: 0.45em)
  for it in items {
    block(above: 0em, below: 0.6em, link(it.plek, grid(
      columns: (5.9em, 1fr, 2.2em), column-gutter: 0.5em,
      text(weight: "semibold")[#soort #it.nummer.],
      it.titel,
      align(right)[#counter(page).at(it.plek).first()],
    )))
  }
}

// ---- 3. Het rapport ---------------------------------------------------------
#let rapport(
  title: none,
  subtitle: none,
  kortetitel: none,
  auteurs: (),
  instelling: (),          // lijst van regels (rapport.qmd)
  webadres: none,         // niet "website": die sleutel is gereserveerd door Quarto
  datum: none,
  status: none,
  colofon: none,
  toc: true,
  toc_title: [Inhoudsopgave],
  toc_depth: 2,
  doc,
) = {
  set document(title: title)

  // -- Pagina: A4, tekstbreedte 16 cm (= breedte van de figuren) -------------
  set page(
    paper: "a4",
    margin: (x: 2.5cm, top: 3cm, bottom: 2.6cm),
    header: context {
      let p = here().page()
      if p <= 3 { return }                                   // titelpagina, colofon, inhoud
      // geen koptekst op de eerste pagina van een hoofdstuk
      if query(heading.where(level: 1)).any(h => h.location().page() == p) { return }
      let vorige = query(heading.where(level: 1).before(here()))
      let hoofdstuk = if vorige.len() > 0 {
        let h = vorige.last()
        let titel = platte_tekst(h.body)
        let kort = titel.split(":").at(0)
        if h.numbering != none [#counter(heading).at(h.location()).first() #kort] else [#kort]
      }
      set text(font: sans, size: 8pt, fill: inkt2, hyphenate: false)
      grid(columns: (1fr, auto), column-gutter: 1em, kortetitel, hoofdstuk)
      v(-0.5em)
      line(length: 100%, stroke: 0.4pt + lijn)
    },
    footer: context {
      let p = here().page()
      if p <= 1 { return }
      set text(font: sans, size: 8pt, fill: inkt2)
      align(right)[#counter(page).display("1")]
    },
  )

  // -- Lopende tekst ------------------------------------------------------------
  // 11.5pt in plaats van 10.5pt: op A4 met 16 cm tekstbreedte geeft dat ongeveer 80 tekens
  // per regel, comfortabel op scherm en in druk. De regelafstand groeit mee.
  set text(font: serif, size: 11.5pt, fill: inkt, lang: "nl", hyphenate: true,
           number-type: "lining")
  set par(justify: true, leading: 0.68em, spacing: 1.1em)
  show strong: set text(weight: "semibold")

  // -- Koppen -----------------------------------------------------------------
  set heading(numbering: "1.1")

  // hoofdstuk: altijd op een nieuwe pagina, groot nummer
  // wijziging: opmaak | 22 september 2026, opmerking Wim: een ongenummerde kop van niveau 1
  // (Lijst van afkortingen, Lijst van figuren, Lijst van tabellen, Referenties, Bijlagen) begint
  // bovenaan de pagina. Genummerde hoofdstukken houden de val van 2,2 cm, zodat het grote
  // hoofdstuknummer lager op de pagina blijft staan.
  show heading.where(level: 1): it => {
    pagebreak(weak: true)
    if it.numbering != none { v(2.2cm) }
    set par(justify: false)
    block(below: 1.2em, sticky: true)[
      #if it.numbering != none {
        text(font: sans, size: 44pt, weight: "regular", fill: nummer)[#counter(heading).display("1")]
        linebreak()
      }
      #text(font: sans, size: 26pt, weight: "semibold", hyphenate: false)[#it.body]
    ]
    v(0.6em)
  }
  // Bij elke paragraaf en subparagraaf: figuren die nog op een plaats wachten, worden
  // eerst geplaatst (place.flush), zodat een figuur nooit voorbij zijn paragraaf schuift.

  // paragraaf (6.1). Elke bijlage begint op een nieuwe pagina.
  show heading.where(level: 2): it => {
    if platte_tekst(it.body).starts-with("Bijlage") { pagebreak(weak: true) }
    place.flush()
  } + block(above: 2.2em, below: 1em, sticky: true)[
    #set par(justify: false)
    #set text(font: sans, size: 15.5pt, weight: "semibold", hyphenate: false)
    #if it.numbering != none [#counter(heading).display()#h(0.7em)]#it.body
  ]
  // subparagraaf (6.1.1)
  show heading.where(level: 3): it => place.flush() + block(above: 1.8em, below: 0.8em, sticky: true)[
    #set par(justify: false)
    #set text(font: sans, size: 12.5pt, weight: "semibold", hyphenate: false)
    #if it.numbering != none [#text(fill: inkt2)[#counter(heading).display()]#h(0.6em)]#it.body
  ]
  // sub-subparagraaf (5.2.2.1): het rapport verwijst naar deze nummers
  show heading.where(level: 4): it => block(above: 1.4em, below: 0.6em, sticky: true)[
    #set text(font: sans, size: 11.5pt, weight: "semibold", style: "italic")
    #if it.numbering != none [#text(fill: inkt2, style: "normal")[#counter(heading).display()]#h(0.5em)]#it.body
  ]

  // -- Figuren ----------------------------------------------------------------
  // bijschrift boven, links uitgelijnd, "Figuur 4." vet
  show figure.caption: it => context block(width: 100%, below: 0.7em)[
    #set align(left)
    #set par(justify: false, leading: 0.5em)
    #set text(font: sans, size: 10.5pt)
    #text(weight: "semibold")[#it.supplement #it.counter.display(it.numbering).]#h(0.35em)#it.body
  ]
  // figuren schuiven naar de boven- of onderkant van een pagina als ze niet passen,
  // zodat er geen halve lege pagina's ontstaan; een figuur wordt nooit gesplitst
  show figure.where(kind: "quarto-float-fig"): set figure(placement: auto)
  show figure.where(kind: "quarto-float-fig"): set block(breakable: false)
  set figure(gap: 0.6em)
  // Ruimte boven en onder figuren en tabellen in de lopende tekst. Typst laat zwakke ruimte
  // wegvallen aan het begin van een pagina, dus bovenaan een pagina komt er niets bij.
  show figure: set block(above: 2.2em, below: 2.2em)
  set place(clearance: 2.4em)

  // -- Voetnoten ----------------------------------------------------------------
  // Nummer links tegen de marge, tekst ernaast als blok (hangende inspringing) in plaats van
  // de standaard waarbij het nummer inspringt en de tekst doorloopt tot aan de marge.
  set footnote.entry(separator: line(length: 25%, stroke: 0.5pt + lijn), gap: 0.5em,
                     clearance: 1em, indent: 0pt)
  show footnote.entry: it => {
    let nr = numbering(it.note.numbering, ..counter(footnote).at(it.note.location()))
    set text(font: sans, size: 8.5pt, fill: inkt)
    set par(justify: false, leading: 0.45em, spacing: 0.4em, hanging-indent: 0pt)
    grid(columns: (1.6em, 1fr), column-gutter: 0.4em,
         align(left)[#text(fill: inkt2)[#nr]],
         it.note.body)
  }

  // -- Tabellen: horizontale lijnen boven en onder de kop, en onder de tabel -------
  set table(
    stroke: (x, y) => if y == 0 { (top: 0.8pt + inkt, bottom: 0.5pt + inkt) },
    inset: (x: 5pt, y: 4pt),
  )
  show table: set text(font: sans, size: 9pt, hyphenate: false)
  show table: set par(justify: false, leading: 0.45em)
  show table.cell.where(y: 0): set text(weight: "semibold")
  // pandoc zet de tabel in #align(center); links uitlijnen past beter bij de tekst
  show table: set align(left)
  // Onderlijn: even dik als de bovenlijn, meteen onder de laatste rij. Als losse
  // lijn na de tabel (niet via 'stroke'), omdat de stroke-functie niet weet welke
  // rij de laatste is. Loopt een tabel over twee pagina's, dan staat de lijn enkel
  // onder het laatste stuk.
  // De lijn is even breed als de tabel zelf (gemeten met measure), zodat ze bij een smalle
  // tabel zoals Tabel 2 niet voorbij de tabel doorloopt (opmerking Wim, 22 september 2026).
  show table: t => layout(ruimte => {
    let breedte = measure(t, width: ruimte.width).width
    block(below: 0pt, t)
    block(above: 0pt, below: 0.9em, line(length: breedte, stroke: 0.8pt + inkt))
  })

  // -- Titelpagina ------------------------------------------------------------
  page(margin: (x: 2.5cm, top: 2.5cm, bottom: 2.5cm), header: none, footer: none)[
    #set par(justify: false)
    // Logo's van de KU Leuven en van de onderzoeksgroep ReSPOND (report/_logos/)
    #grid(columns: (auto, 1fr, auto), align: (left + horizon, center, right + horizon),
      image("report/_logos/kuleuven.png", height: 1.5cm),
      [],
      image("report/_logos/respond.png", height: 1.5cm))
    #v(1fr)
    #text(font: sans, size: 9pt, weight: "semibold", tracking: 0.08em, fill: inkt2)[#upper[Onderzoeksrapport]]
    #v(0.6em)
    #text(font: serif, size: 30pt, weight: "semibold", hyphenate: false)[#title]
    #v(0.9em)
    #if subtitle != none { text(font: serif, size: 13pt, style: "italic", fill: inkt2)[#subtitle] }
    #v(2.4em)
    #set text(font: sans, size: 11.5pt)
    #for a in auteurs [#a \ ]
    // <!-- wijziging: opmaak | 23 september 2026 (vraag Wim): meer witruimte tussen de auteurs
    // en de instelling, zodat de onderzoeksgroep wat lager op de titelpagina staat. -->
    #v(1.8em)
    // Instelling: elke regel uit rapport.qmd op een eigen regel, daaronder het webadres
    #text(size: 10pt, fill: inkt2)[
      #for regel in instelling [#regel \ ]
      #if webadres != none [#webadres]
    ]
    #v(1fr)
    #set text(size: 9.5pt, fill: inkt2)
    #grid(columns: (1fr, auto), datum, if status != none { text(weight: "semibold")[#status] })
  ]

  // -- Colofon -----------------------------------------------------------------
  page(header: none)[
    #set par(justify: false)
    #set text(font: sans, size: 8.5pt, fill: inkt2)
    #v(1fr)
    #text(weight: "semibold", fill: inkt)[#title] \
    #if subtitle != none [#subtitle \ ]
    #v(0.6em)
    Auteurs: #auteurs.join(", ", last: " en ") \
    #if datum != none [Versie: #datum]
    #v(0.8em)
    // <!-- wijziging: publicatie | geen afbreking in het colofon, zodat namen als GitHub
    // en een DOI niet over twee regels gesplitst worden -->
    #if colofon != none { text(hyphenate: false, colofon) }
    #v(0.8em)
    #text(weight: "semibold", fill: inkt)[Aanbevolen citatie] \
    #auteurs.join(", ", last: " & ") (2026). _#title;_ #subtitle. #instelling.join(", ").
  ]

  // -- Inhoudsopgave ---------------------------------------------------------------
  if toc {
    page(header: none)[
      #set par(justify: false)
      #text(font: sans, size: 26pt, weight: "semibold")[#toc_title]
      #v(1.2em)
      #set text(font: sans, size: 10pt)
      #show outline.entry.where(level: 1): it => { v(0.7em); strong(it) }
      #outline(title: none, depth: toc_depth, indent: 1.6em)
    ]
  }

  doc
}
