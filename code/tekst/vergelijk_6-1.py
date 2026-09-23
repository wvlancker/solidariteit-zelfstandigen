"""
Tekstvergelijking §6.1: oorspronkelijke tekst naast de herwerkte tekst.

    python code/tekst/vergelijk_6-1.py   ->  output/tekst/vergelijking_6-1.html

De koppeling tussen alinea's (welke oude alinea overeenkomt met welke nieuwe)
en de toelichting per wijziging staan hieronder in KOPPELING en zijn met de
hand gemaakt. De teksten zelf worden telkens opnieuw ingelezen:
  - origineel: report/import/06-1_resultaten_macro.md (+ voetnoten uit het volledige import-bestand)
  - nieuw:     report/sections/06-1_macro.md (ingevulde versie van de template)
Verandert de nieuwe tekst, draai dan dit script opnieuw. Verandert het aantal
alinea's, pas dan de indexen in KOPPELING aan (het script meldt ontbrekende of
dubbel gebruikte alinea's).

Waar oude en nieuwe alinea sterk op elkaar lijken, markeert het script de
woorden die verdwenen (doorgestreept) en die erbij kwamen (gemarkeerd).
Sterk herschreven alinea's worden zonder woordmarkering naast elkaar gezet,
omdat een woord-voor-woordvergelijking daar enkel ruis oplevert.
"""

import difflib
import html
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ORIG = ROOT / "report" / "import" / "06-1_resultaten_macro.md"
ORIG_VOLLEDIG = ROOT / "report" / "import" / "rapport_finaal_TC_volledig.md"
NIEUW = ROOT / "report" / "sections" / "06-1_macro.md"
UIT = ROOT / "output" / "tekst" / "vergelijking_6-1.html"


def alineas(pad):
    t = re.sub(r"<!--.*?-->", "", pad.read_text(encoding="utf-8"), flags=re.S)
    return [a.strip() for a in t.split("\n\n") if a.strip()]


# ---------------------------------------------------------------------------
# Koppeling: (oude alinea's, nieuwe alinea's, soorten wijziging, locatie, toelichting)
# Soorten: cijfer, interpretatie, nieuw, geschrapt, redactie, figuur
# Oude voetnoten: 'fn21', 'fn22', 'fn23'
# ---------------------------------------------------------------------------
KOPPELING = [
    ([0, 1], [0, 1, 2, 3, 4], ["redactie", "nieuw"], "Inleiding",
     "Leeswijzer toegevoegd: veranderingen van aandelen en ratio's in procentpunt, van bedragen per capita in "
     "procent (leesnota D6); Z1 en W1 expliciet als hoofddefinitie; uitleg bij de banden en genummerde lijnen. "
     "Figuur 4 toont nu bijdragen, uitgaven en ratio in drie panelen met beide stelsels samen."),
    ([2], [5], ["redactie"], "Vaststelling 1: niveau",
     "Zelfde niveaus (71/64% en 67/57%). De daling staat nu in procentpunt (-3,6 en -7,3) in plaats van relatief "
     "(-5% en -11%). Vaststelling geformuleerd vanuit de zelfstandigen."),
    ([3], [6, 7, 8], ["interpretatie", "nieuw"], "Vaststelling 2: drijvende kracht",
     "Oud: evoluties lopen 'relatief gelijk' tot 2020. Nieuw: over de volledige periode drijven de uitgaven de "
     "daling (Z1 uitgaven +21%, bijdragen +7%), met uitgavengroei 2,3 keer zo snel als bij werknemers (leesnota "
     "B1/G2). De rol van de populatiedefinitie wordt uitgelegd: de ratio is onder Z1 en Z2 identiek, alleen de "
     "verdeling over bijdragen en uitgaven verschilt. Pensioenaandeel toegevoegd."),
    ([4, "fn21"], [9, "fn:rekenhof"], ["redactie", "cijfer"], "Periode 2003-2014",
     "Daling in procentpunt (-8,4 en -6,3) in plaats van relatief (-12% en -10%). Groei van uitgaven en bijdragen "
     "per capita toegevoegd. Nieuw: in deze periode daalde de beroepssolidariteit bij werknemers sterker. "
     "Voetnoot Rekenhof ongewijzigd."),
    ([5], [10, 11, "fn:breuk", "fn:taxshift"], ["interpretatie", "cijfer", "nieuw"], "Periode 2015-2019",
     "Opgesplitst in twee delen. (1) 2015 als boekhoudkundige breuk: gezinsbijslag en een deel van de "
     "RIZIV-overdrachten verdwijnen, gekwantificeerd; de sprong in de ratio is geen versterking van de "
     "beroepssolidariteit (RIZIV bij het eerste gebruik voluit, 22 september 2026). (2) Tax shift 2016-2018 met correcte tarieven: zelfstandigen 22% naar 20,5% "
     "gefaseerd (niet in één keer in 2016), werkgevers 32,4% naar 25% (niet 33%). Geschrapt: 'tussen 2016 en "
     "2019 bleven de uitgaven relatief constant' en de vergelijking 2003-2019 (-1% en -2%)."),
    ([6, 7, "fn22"], [12], ["cijfer", "redactie"], "Periode 2020-2022: corona",
     "Cijfercorrecties (fout G1): uitgaven 2020 +11% wordt +10%, +50% wordt +45%; bijdragen zelfstandigen -11% "
     "wordt -10%. Voetnoot 22 (+53% en +48%) geschrapt: na correctie is het verschil tussen Z1 en Z2 nog 1 "
     "procentpunt. De daling van de ratio 2019-2022 (-4% en -20%) vervangen door het niveau in 2020 en de "
     "evolutie 2019-2022 van uitgaven en bijdragen. Uitleg over de steunmaatregelen behouden."),
    ([8], [13], ["interpretatie", "nieuw"], "2023",
     "De vergelijking Z1/Z2 over 2003-2023 is verhuisd naar vaststelling 2. Nieuw: bijdragen per zelfstandige "
     "liggen in 2023 nog 7% onder 2019, die per werknemer 3% boven; voorbehoud over de vertraagde regularisatie "
     "van bijdragen van zelfstandigen."),
    ([9], [14], ["interpretatie"], "Tussentijdse synthese beroepssolidariteit",
     "Oud: de snellere daling bij zelfstandigen is 'vooral te wijten aan lagere ontvangsten per hoofd'. Nieuw: de "
     "drijvende kracht verschuift. Vóór 2015 verklaren de uitgaven de daling (en daalt ze bij werknemers "
     "sterker); na 2015 dalen de bijdragen per zelfstandige met 13%, waarvan de verlaagde bijdragevoet "
     "mechanisch ongeveer de helft verklaart. Externe onderbouwing: Hoge Raad van Financiën (2024: 50)."),
    ([10, 11, 12], [15, 16, 17, 18], ["figuur"], "Figuur 4",
     "Nieuwe opbouw (drie panelen, geen tweede y-as). Noot aangevuld met banden en genummerde lijnen; bron "
     "concreter."),
    ([13, 14], [19, 20], ["cijfer", "redactie"], "Vennootschappen: inleiding",
     "Oud: aandeel vennootschapsbijdragen 'ongeveer 5%' en 'relatief stabiel doorheen de tijd'. Nieuw: 3,9% "
     "(2003), 6,3% (2005), 5,2% (2023), dus niet stabiel vanaf 2003 (leesnota G4). Eigen tussentitel."),
    ([15], [21, 22, 23, "fn:vb2004"], ["interpretatie", "cijfer", "nieuw"], "Vennootschapsbijdrage",
     "Oud: dalende bijdrage per vennootschap door de gedifferentieerde bijdrage van 2004, die lagere bijdragen "
     "invoerde. Nieuw: de nominale bijdrage per vennootschap lag 14 jaar vlak (€403 tot €422); de reële daling "
     "is exact de inflatie-erosie van een bevroren forfait. De hervorming van 2004 verhoogde de gemiddelde "
     "bijdrage (voetnoot, voorzichtig geformuleerd). Nieuw: effect op de beroepssolidariteit (ongeveer 9% van de "
     "daling sinds 2006) en contrafeitelijke indexering (-1,5 procentpunt, €0,14 miljard). Toegevoegd na bespreking: "
     "de kwalificatie dat dit een mechanische redenering is, met een verwijzing naar de sensitiviteitsanalyse in "
     "Bijlage 6 (groei als eenmanszaken in plaats van vennootschappen; omslagpunt €2.000 winst buiten de bijdragebasis). "
     "Op vraag van Wim (22 september) vereenvoudigd: het omslagpunt uitgelegd als vergelijking tussen de "
     "vennootschapsbijdrage en de gewone bijdrage, met één voorbeeld (typegeval 2 uit Tabel B6.2, regels van 2024)."),
    ([16, 17], [24], ["interpretatie", "geschrapt"], "Gewone bijdragen en vervennootschappelijking",
     "Geschrapt: 'Dat is allicht een belangrijke determinant van de dalende beroepssolidariteit' en de "
     "redenering dat bijberoepers de daling niet verklaren omdat ze geen rechten openen (leesnota H2/H4). "
     "Nieuw: het substitutiemechanisme (loon vervangen door forfaits), de erkenning dat dit kanaal op macroniveau "
     "niet meetbaar is, en de vaststelling van de Hoge Raad van Financiën (2024: 7 en 50)."),
    ([18, 19, 20], [25, 26, 27, 28], ["figuur"], "Figuur 5",
     "Noot aangevuld (wat door wat gedeeld wordt); bron concreter."),
    ([21], [29, 30, 31, "fn:nbb"], ["interpretatie", "cijfer", "nieuw"], "Werkgevers- en werknemersbijdragen",
     "Nieuw: voorbehoud dat de NBB-cijfers een ruimer geheel betreffen (10 à 17% hoger dan FOD SZ; leesnota G3). "
     "Cijfers voor 2003-2015 en 2003-2023 behouden, daling tijdens de tax shift toegevoegd (-9%). 'In belangrijke "
     "mate samenhangt met' afgezwakt tot 'valt samen met'."),
    ([22], [46, 47], ["interpretatie"], "Synthese macro (nu: Samenvatting)",
     "Oud: daling 'voornamelijk gedreven door lagere ontvangsten per hoofd', en dalende vennootschapsbijdragen "
     "en dalende sociale bijdragen 'die elkaar dreigen te versterken'. Nieuw: uitgaven over de hele periode, "
     "bijdragen sinds 2015; vennootschapsbijdrage goed voor ongeveer 9% van de daling; het zwaardere kanaal is "
     "niet rechtstreeks meetbaar."),
    ([23], [32, 33], ["redactie", "cijfer"], "Nationale solidariteit: inleiding",
     "Tikfout rechtgezet: de periode is niet 2020-2024 (sinds 21 september 2026 loopt Figuur 6 over 2000-2023). Terminologie geharmoniseerd: 'toelagen van "
     "publieke overheden' in plaats van afwisselend staatstoelagen en overheidstoelagen (leesnota D1)."),
    ([24, 25, 26], [36, 37, 38, 39], ["figuur"], "Figuur 6",
     "Twee panelen in plaats van staven en lijnen op twee assen. De periode eindigt sinds 21 september 2026 in 2023 (de cijfers voor 2024 waren ramingen)."),
    ([27, 28], [34, 35], ["cijfer", "interpretatie"], "Evolutie nationale solidariteit",
     "Oud: stijging 'sterker bij werknemers (+48%) dan bij zelfstandigen (+30%)'. Nieuw: in procentpunt "
     "van dezelfde orde (+10,6 en +9,3 over 2000-2023, iets groter bij zelfstandigen); het relatieve verschil is een basiseffect (leesnota D6). Alle fases in procentpunt. "
     "Cijfercorrecties door fout G1 verdwijnen hiermee, en de periodelabels volgen nu wat berekend is "
     "(2007-2009 in plaats van 2008-2009, 2009-2014 in plaats van 2010-2014, 2015-2019 in plaats van 2016-2019)."),
    ([29, 30], [40], ["cijfer", "redactie"], "Inkomstenstructuur",
     "Aandelen als niveaus (toelagen zelfstandigen 29% naar 12% over 2000-2023) in plaats van relatieve veranderingen van "
     "aandelen (-68%, +561%). Geschrapt: 'stijgende ontvangsten' (bedoeld was: uitgaven)."),
    ([31, 32, "fn23"], [41, "fn:btw"], ["interpretatie", "cijfer", "geschrapt"], "Samenstelling nationale solidariteit",
     "Keerpunt verlegd van 2015 naar 2017 (financieringshervorming), met bedragen (toelagen zelfstandigen "
     "€1,4 miljard naar €0,4 miljard, alternatieve financiering €0,7 naar €2,1 miljard). Geschrapt: 'bij "
     "werknemers speelt de alternatieve financiering gedurende de gehele periode een grotere rol ... behalve in "
     "enkele jaren', want in 2000-2003 en 2015-2016 lag het aandeel toelagen boven 50%. Voetnoot 23 opgenomen in "
     "de tekst; voetnoot over btw verhuisd vanuit de conclusie. Nieuw (22 september 2026): de btw is in 2023 in "
     "beide stelsels ongeveer even groot binnen de nationale solidariteit (54% en 55%), maar financiert 24% van "
     "alle inkomsten bij zelfstandigen tegenover 17% bij werknemers; nodig voor de conclusie."),
    ([33, 34], [42, 43, 44, 45], ["figuur"], "Figuur 7",
     "Nieuwe noot: definitie overige financiering en genummerde hervormingen (de zin over de raming 2024 is "
     "geschrapt sinds de periode eindigt in 2023)."),
    ([], [48, "fn:def"], ["nieuw"], "Samenvatting nationale solidariteit en voetnoot definities",
     "Nieuwe slotalinea die de nationale solidariteit samenvat en naar de conclusie verwijst. Nieuwe voetnoot "
     "over rechten van bijberoepers en de overlap tussen de definities (te verifiëren door de auteurs)."),
]

SOORTEN = {
    "interpretatie": "Interpretatie herzien",
    "cijfer": "Cijfer gecorrigeerd",
    "nieuw": "Nieuw",
    "geschrapt": "Geschrapt",
    "redactie": "Redactioneel",
    "figuur": "Figuur",
}


def inline_md(t: str) -> str:
    """Minimale markdown naar HTML: vet, cursief, voetnootverwijzing, links, figuren."""
    t = re.sub(r"<span[^>]*></span>", "", t)
    if t.startswith("!["):
        return '<span class="fig">[figuur]</span>'
    t = html.escape(t, quote=False)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", t)
    t = re.sub(r"\[\^([\w-]+)\]", r'<sup class="fn">\1</sup>', t)
    t = re.sub(r"&lt;(https?://[^&]+)&gt;", r"\1", t)
    t = re.sub(r"^#{2,3} (.+)$", r'<span class="kop">\1</span>', t)
    return t


def cijfers_markeren(fragment: str) -> str:
    """Cijfers in een HTML-fragment (buiten tags) subtiel markeren."""
    delen = re.split(r"(<[^>]+>)", fragment)
    # enkel echte resultaatcijfers: bedragen (€), percentages, procentpunten, getekende of decimale getallen.
    # Jaartallen, figuur- en tabelnummers en Z1/W1 blijven ongemarkeerd.
    patroon = re.compile(
        r"(?<![\w])("
        r"[+\-−]?€\s?\d[\d.,]*(?:\s?miljard)?"          # bedragen
        r"|[+\-−]?\d[\d.,]*\s?(?:%|procentpunten|procentpunt)"  # percentages en procentpunten
        r"|[+\-−]\d[\d.,]*\d?"                           # getekende getallen
        r"|\d+,\d+"                                      # decimale getallen
        r")")
    return "".join(d if d.startswith("<") else patroon.sub(r'<span class="num">\1</span>', d) for d in delen)


def woorddiff(oud: str, nieuw: str):
    """Geeft (oud_html, nieuw_html, gelijkenis). Markeert woorden alleen bij voldoende overeenkomst."""
    a, b = oud.split(), nieuw.split()
    sm = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
    ratio = sm.ratio()
    if ratio < 0.45:
        return None, None, ratio
    oh, nh = [], []
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        oa, nb = " ".join(a[i1:i2]), " ".join(b[j1:j2])
        if op == "equal":
            oh.append(inline_md(oa)); nh.append(inline_md(nb))
        else:
            if oa:
                oh.append(f"<del>{inline_md(oa)}</del>")
            if nb:
                nh.append(f"<ins>{inline_md(nb)}</ins>")
    return " ".join(oh), " ".join(nh), ratio


def main():
    oud = alineas(ORIG)
    nieuw = alineas(NIEUW)

    # voetnoten
    volledig = ORIG_VOLLEDIG.read_text(encoding="utf-8")
    oud_fn = {f"fn{n}": re.search(rf"^\[\^{n}\]: (.+)$", volledig, flags=re.M).group(1) for n in (21, 22, 23)}
    nieuw_fn = {}
    nieuw_tekst = []
    for a in nieuw:
        m = re.match(r"^\[\^([\w-]+)\]: (.+)$", a, flags=re.S)
        if m:
            nieuw_fn[f"fn:{m.group(1)}"] = m.group(2)
        else:
            nieuw_tekst.append(a)
    # indexen in KOPPELING verwijzen naar alle alinea's inclusief voetnoten; bouw lookup
    def haal_oud(k):
        return ("voetnoot " + k[2:], oud_fn[k]) if isinstance(k, str) else (None, oud[k])

    def haal_nieuw(k):
        return ("voetnoot " + k[3:], nieuw_fn[k]) if isinstance(k, str) else (None, nieuw[k])

    # controle: elke alinea precies één keer gebruikt
    gebruikt_o = [k for r in KOPPELING for k in r[0] if isinstance(k, int)]
    gebruikt_n = [k for r in KOPPELING for k in r[1] if isinstance(k, int)]
    n_tekst_nieuw = len(nieuw) - len(nieuw_fn)
    ontbrekend_o = sorted(set(range(len(oud))) - set(gebruikt_o))
    ontbrekend_n = sorted(set(range(n_tekst_nieuw)) - set(gebruikt_n))
    dubbel = [k for k in set(gebruikt_o) if gebruikt_o.count(k) > 1] + [k for k in set(gebruikt_n) if gebruikt_n.count(k) > 1]
    if ontbrekend_o or ontbrekend_n or dubbel:
        raise SystemExit(f"Koppeling onvolledig: oud {ontbrekend_o}, nieuw {ontbrekend_n}, dubbel {dubbel}")

    teller = {s: 0 for s in SOORTEN}
    rijen_html = []
    for i, (ko, kn, soorten, locatie, toelichting) in enumerate(KOPPELING, start=1):
        for s in soorten:
            teller[s] += 1
        oude = [haal_oud(k) for k in ko]
        nieuwe = [haal_nieuw(k) for k in kn]
        oud_plat = "\n\n".join(t for _, t in oude)
        nieuw_plat = "\n\n".join(t for _, t in nieuwe)

        # woorddiff enkel als beide kanten één gewone alinea hebben
        diff_o = diff_n = None
        if len(oude) == 1 and len(nieuwe) == 1 and oude[0][0] is None and nieuwe[0][0] is None:
            diff_o, diff_n, _ = woorddiff(oud_plat, nieuw_plat)

        def blokken(items, diff):
            if diff is not None:
                return f"<p>{cijfers_markeren(diff)}</p>"
            if not items:
                return '<p class="leeg">Geen overeenkomstige tekst.</p>'
            uit = []
            for label, t in items:
                inhoud = cijfers_markeren(inline_md(t))
                if label:
                    uit.append(f'<p class="vn"><span class="vnlabel">{html.escape(label)}</span> {inhoud}</p>')
                else:
                    uit.append(f"<p>{inhoud}</p>")
            return "\n".join(uit)

        chips = "".join(f'<span class="chip chip-{s}">{SOORTEN[s]}</span>' for s in soorten)
        modus = "woorden gemarkeerd" if diff_o is not None else ("nieuwe tekst" if not ko else "herschreven")
        rijen_html.append(f"""
<article class="rij" data-soorten="{' '.join(soorten)}" id="r{i}">
  <header class="rijkop">
    <span class="nr">{i:02d}</span>
    <h2>{html.escape(locatie)}</h2>
    <div class="chips">{chips}</div>
  </header>
  <p class="toelichting">{html.escape(toelichting)}</p>
  <div class="kolommen">
    <section class="kol kol-oud" aria-label="Origineel">
      <div class="kollabel">Origineel <span class="modus">{modus}</span></div>
      {blokken(oude, diff_o)}
    </section>
    <section class="kol kol-nieuw" aria-label="Nieuw">
      <div class="kollabel">Nieuw</div>
      {blokken(nieuwe, diff_n)}
    </section>
  </div>
</article>""")

    filters = "".join(
        f'<button type="button" class="filter" data-filter="{s}" aria-pressed="false">{lab} <span>{teller[s]}</span></button>'
        for s, lab in SOORTEN.items() if teller[s] > 0)   # soorten zonder passages niet tonen

    pagina = PAGINA.replace("{{FILTERS}}", filters).replace("{{RIJEN}}", "\n".join(rijen_html)) \
        .replace("{{N_RIJEN}}", str(len(KOPPELING)))
    UIT.parent.mkdir(parents=True, exist_ok=True)
    UIT.write_text(pagina, encoding="utf-8")
    print(f"geschreven: {UIT.relative_to(ROOT)} ({len(KOPPELING)} passages)")


PAGINA = r"""<title>Tekstvergelijking §6.1</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,600;1,6..72,400&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
  :root {
    --ink: #16202a; --ink-2: #3f5060; --muted: #65798a;
    --paper: #f2f5f6; --surface: #ffffff; --rule: #d5dee3; --rule-soft: #e6ecef;
    --accent: #12606b; --accent-soft: #e2eff0;
    --del-bg: #f7e1df; --del-ink: #8f2a2a; --ins-bg: #dcefe5; --ins-ink: #1f5a3d;
    --c-interpretatie: #a02e2e; --c-cijfer: #8d5f16; --c-nieuw: #2e6b52;
    --c-geschrapt: #6b6f75; --c-redactie: #12606b; --c-figuur: #5a4f8f;
    --num: #e9eef1;
    --f-display: "Newsreader", Georgia, serif;
    --f-body: "IBM Plex Sans", "Segoe UI", system-ui, sans-serif;
    --f-mono: "IBM Plex Mono", ui-monospace, Menlo, monospace;
  }
  @media (prefers-color-scheme: dark) {
    :root:not([data-theme="light"]) {
      --ink: #e3ebef; --ink-2: #b4c3cd; --muted: #8598a6;
      --paper: #0f151a; --surface: #161e25; --rule: #2b3741; --rule-soft: #212b33;
      --accent: #5bbac6; --accent-soft: #163034;
      --del-bg: #3a1f22; --del-ink: #f0a9a9; --ins-bg: #183327; --ins-ink: #9bd9b6;
      --c-interpretatie: #e59090; --c-cijfer: #d4a75c; --c-nieuw: #83c5a4;
      --c-geschrapt: #a3a8ae; --c-redactie: #5bbac6; --c-figuur: #aea4e6;
      --num: #1f2a32;
    }
  }
  :root[data-theme="dark"] {
    --ink: #e3ebef; --ink-2: #b4c3cd; --muted: #8598a6;
    --paper: #0f151a; --surface: #161e25; --rule: #2b3741; --rule-soft: #212b33;
    --accent: #5bbac6; --accent-soft: #163034;
    --del-bg: #3a1f22; --del-ink: #f0a9a9; --ins-bg: #183327; --ins-ink: #9bd9b6;
    --c-interpretatie: #e59090; --c-cijfer: #d4a75c; --c-nieuw: #83c5a4;
    --c-geschrapt: #a3a8ae; --c-redactie: #5bbac6; --c-figuur: #aea4e6;
    --num: #1f2a32;
  }
  * { box-sizing: border-box; }
  body { background: var(--paper); color: var(--ink); font-family: var(--f-body); font-size: 15px;
         line-height: 1.6; -webkit-font-smoothing: antialiased; }
  .wrap { max-width: 78rem; margin: 0 auto; padding-inline: 20px; padding-block: 0 80px; }

  header.kop { padding-block: 44px 24px; border-bottom: 2px solid var(--ink); display: grid; gap: 14px; }
  .eyebrow { font-family: var(--f-mono); font-size: .72rem; letter-spacing: .13em; text-transform: uppercase; color: var(--accent); }
  h1 { font-family: var(--f-display); font-weight: 600; font-size: clamp(1.9rem, 5vw, 2.6rem); line-height: 1.1; margin: 0; text-wrap: balance; }
  .standfirst { font-family: var(--f-display); font-size: 1.1rem; color: var(--ink-2); margin: 0; max-width: 46rem; }
  dl.meta { display: grid; grid-template-columns: max-content 1fr; gap: 4px 18px; margin: 4px 0 0; font-size: .85rem; }
  dl.meta dt { font-family: var(--f-mono); font-size: .68rem; letter-spacing: .1em; text-transform: uppercase; color: var(--muted); padding-top: .25em; }
  dl.meta dd { margin: 0; color: var(--ink-2); }
  code { font-family: var(--f-mono); font-size: .85em; }

  .balk { position: sticky; top: env(safe-area-inset-top, 0px); z-index: 5; background: var(--paper);
          padding-block: 12px; border-bottom: 1px solid var(--rule); display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }
  .balk .lbl { font-family: var(--f-mono); font-size: .68rem; letter-spacing: .1em; text-transform: uppercase; color: var(--muted); margin-right: 4px; }
  .filter { font: 500 .8rem var(--f-body); color: var(--ink-2); background: var(--surface); border: 1px solid var(--rule);
            padding: 4px 10px; border-radius: 999px; cursor: pointer; }
  .filter span { font-family: var(--f-mono); color: var(--muted); margin-left: 2px; }
  .filter[aria-pressed="true"] { background: var(--ink); color: var(--paper); border-color: var(--ink); }
  .filter[aria-pressed="true"] span { color: var(--paper); }
  .filter:focus-visible, .toggle:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
  .legenda { display: flex; flex-wrap: wrap; gap: 14px; font-size: .8rem; color: var(--ink-2); margin-left: auto; }
  .legenda del, .legenda ins { padding: 0 3px; }

  main { display: grid; gap: 22px; margin-top: 22px; }
  .rij { background: var(--surface); border: 1px solid var(--rule); }
  .rijkop { display: flex; flex-wrap: wrap; align-items: baseline; gap: 10px 14px; padding: 14px 18px 0; }
  .nr { font-family: var(--f-mono); font-size: .78rem; color: var(--accent); }
  .rijkop h2 { font-family: var(--f-display); font-size: 1.2rem; font-weight: 600; margin: 0; }
  .chips { display: flex; flex-wrap: wrap; gap: 6px; margin-left: auto; }
  .chip { font-family: var(--f-mono); font-size: .66rem; letter-spacing: .06em; text-transform: uppercase;
          padding: 2px 7px; border: 1px solid currentColor; border-radius: 3px; }
  .chip-interpretatie { color: var(--c-interpretatie); } .chip-cijfer { color: var(--c-cijfer); }
  .chip-nieuw { color: var(--c-nieuw); } .chip-geschrapt { color: var(--c-geschrapt); }
  .chip-redactie { color: var(--c-redactie); } .chip-figuur { color: var(--c-figuur); }
  .toelichting { margin: 8px 18px 14px; padding: 10px 14px; background: var(--accent-soft); font-size: .9rem; color: var(--ink); max-width: 68rem; }

  .kolommen { display: grid; grid-template-columns: 1fr 1fr; border-top: 1px solid var(--rule-soft); }
  .kol { padding: 12px 18px 16px; min-width: 0; }
  .kol-oud { border-right: 1px solid var(--rule-soft); }
  .kol p { margin: 0 0 .8em; max-width: 42rem; }
  .kol p:last-child { margin-bottom: 0; }
  .kollabel { font-family: var(--f-mono); font-size: .66rem; letter-spacing: .12em; text-transform: uppercase; color: var(--muted); margin-bottom: 8px; display: flex; gap: 10px; }
  .kol-oud .kollabel { color: var(--c-interpretatie); } .kol-nieuw .kollabel { color: var(--c-nieuw); }
  .modus { color: var(--muted); letter-spacing: .04em; text-transform: none; }
  .kol-oud p { color: var(--ink-2); }
  .leeg { color: var(--muted); font-style: italic; }
  .vn { font-size: .85rem; color: var(--ink-2); border-left: 2px solid var(--rule); padding-left: 10px; }
  .vnlabel { font-family: var(--f-mono); font-size: .68rem; text-transform: uppercase; letter-spacing: .08em; color: var(--muted); }
  .kop { font-family: var(--f-display); font-weight: 600; font-size: 1.05rem; color: var(--ink); }
  .fig { font-family: var(--f-mono); font-size: .75rem; color: var(--muted); }
  sup.fn { font-family: var(--f-mono); font-size: .62rem; color: var(--accent); }
  del { background: var(--del-bg); color: var(--del-ink); text-decoration-thickness: 1px; }
  ins { background: var(--ins-bg); color: var(--ins-ink); text-decoration: none; }
  .num { background: var(--num); border-radius: 2px; padding: 0 2px; font-variant-numeric: tabular-nums; }
  body.geen-cijfers .num { background: none; padding: 0; }
  .toggle { font: 500 .8rem var(--f-body); color: var(--ink-2); background: none; border: 1px dashed var(--rule); padding: 4px 10px; border-radius: 999px; cursor: pointer; }

  footer { margin-top: 40px; padding-top: 16px; border-top: 1px solid var(--rule); font-size: .82rem; color: var(--muted); }

  @media (max-width: 760px) {
    .kolommen { grid-template-columns: 1fr; }
    .kol-oud { border-right: 0; border-bottom: 1px solid var(--rule-soft); }
    .chips { margin-left: 0; width: 100%; }
    .legenda { margin-left: 0; }
    .balk { position: static; }
  }
</style>

<div class="wrap">
  <header class="kop">
    <div class="eyebrow">Hoe solidair is de sociale zekerheid voor zelfstandigen? · §6.1 Macroniveau</div>
    <h1>Tekstvergelijking §6.1: origineel en herwerking</h1>
    <p class="standfirst">Passage per passage de oorspronkelijke tekst naast de herwerkte tekst, met per passage wat er veranderde en waarom.</p>
    <dl class="meta">
      <dt>Origineel</dt><dd><code>Rapport UNIZO_finaal_TC.docx</code>, §6.1, bijgehouden wijzigingen aanvaard</dd>
      <dt>Nieuw</dt><dd><code>report/templates/06-1_macro.md</code>, herwerkte versie, cijfers ingevuld (stand 22 september 2026, na nalezing door Wim)</dd>
      <dt>Lezen</dt><dd>Codes zoals G1, B1 of D6 verwijzen naar de leesnota. Waar oude en nieuwe alinea sterk overeenkomen, zijn geschrapte woorden doorgestreept en toegevoegde woorden gemarkeerd; herschreven passages staan zonder markering naast elkaar.</dd>
    </dl>
  </header>

  <div class="balk" role="toolbar" aria-label="Filter op soort wijziging">
    <span class="lbl">Toon</span>
    {{FILTERS}}
    <button type="button" class="toggle" id="toggle-cijfers" aria-pressed="true">Cijfers markeren</button>
    <span class="legenda"><span><del>geschrapt</del></span><span><ins>toegevoegd</ins></span><span><span class="num">12%</span> cijfer</span></span>
  </div>

  <main id="rijen">
    {{RIJEN}}
  </main>

  <footer>{{N_RIJEN}} passages. Gegenereerd door <code>code/tekst/vergelijk_6-1.py</code>; de koppeling tussen alinea's en de toelichting zijn met de hand opgesteld.</footer>
</div>

<script>
(function () {
  var knoppen = Array.prototype.slice.call(document.querySelectorAll('.filter'));
  var rijen = Array.prototype.slice.call(document.querySelectorAll('.rij'));
  function toepassen() {
    var actief = knoppen.filter(function (k) { return k.getAttribute('aria-pressed') === 'true'; })
                        .map(function (k) { return k.dataset.filter; });
    rijen.forEach(function (r) {
      var s = r.dataset.soorten.split(' ');
      r.hidden = actief.length > 0 && !actief.some(function (a) { return s.indexOf(a) !== -1; });
    });
  }
  knoppen.forEach(function (k) {
    k.addEventListener('click', function () {
      k.setAttribute('aria-pressed', k.getAttribute('aria-pressed') === 'true' ? 'false' : 'true');
      toepassen();
    });
  });
  var t = document.getElementById('toggle-cijfers');
  t.addEventListener('click', function () {
    var aan = t.getAttribute('aria-pressed') === 'true';
    t.setAttribute('aria-pressed', aan ? 'false' : 'true');
    document.body.classList.toggle('geen-cijfers', aan);
  });
})();
</script>
"""

if __name__ == "__main__":
    main()
