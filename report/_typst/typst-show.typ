// Geeft de metadata uit report/rapport.qmd door aan de functie `rapport`
// (gedefinieerd in typst-template.typ). Pandoc-sjabloonsyntaxis: $veld$.
#show: doc => rapport(
$if(title)$
  title: [$title$],
$endif$
$if(subtitle)$
  subtitle: [$subtitle$],
$endif$
$if(kortetitel)$
  kortetitel: [$kortetitel$],
$endif$
  auteurs: ($for(auteurs)$[$auteurs$],$endfor$),
$if(instelling)$
  instelling: ($for(instelling)$[$instelling$],$endfor$),
$endif$
$if(webadres)$
  webadres: [$webadres$],
$endif$
$if(datum)$
  datum: [$datum$],
$endif$
$if(status)$
  status: [$status$],
$endif$
$if(colofon)$
  colofon: [$colofon$],
$endif$
  toc: $if(toc)$true$else$false$endif$,
$if(toc-title)$
  toc_title: [$toc-title$],
$endif$
  toc_depth: $if(toc-depth)$$toc-depth$$else$2$endif$,
  doc,
)
