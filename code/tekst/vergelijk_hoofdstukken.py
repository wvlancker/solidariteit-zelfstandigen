"""
Tekstvergelijking hoofdstuk 1 tot 5: origineel naast herwerkte tekst, alinea per alinea.

    python code/tekst/vergelijk_hoofdstukken.py   ->  output/tekst/vergelijking_h1-5.html

Anders dan vergelijk_6-1.py en vergelijk_07.py, waar de tekst grondig herschreven is en de
koppeling met de hand gebeurde, zijn deze hoofdstukken grotendeels overgenomen. Daarom:

  - Origineel: de opgeschoonde import (code/tekst/importeer_hoofdstukken.py, functie
    schoon_hoofdstukken), dus zonder Word-restanten, zodat enkel inhoudelijke verschillen opvallen.
  - Nieuw: report/sections/0N_*.md (ingevulde templates).
  - De alinea's worden automatisch gekoppeld (difflib). Ongewijzigde alinea's worden
    samengevouwen; gewijzigde krijgen een woord-per-woordmarkering.
  - De soort wijziging en de toelichting komen uit de commentaren in de template:
        <!-- wijziging: soort1, soort2 | toelichting -->
    vlak boven de gewijzigde alinea. Een gewijzigde alinea zonder commentaar krijgt het label
    'niet toegelicht', zodat een vergeten toelichting opvalt.
"""

import difflib
import html
import importlib.util
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HIER = Path(__file__).resolve().parent
UIT = ROOT / "output" / "tekst" / "vergelijking_h1-5.html"

sys.path.insert(0, str(HIER))
import importeer_hoofdstukken as imp  # noqa: E402

# hulpfuncties en paginaopmaak hergebruiken uit de vergelijking van §6.1
_spec = importlib.util.spec_from_file_location("v61", HIER / "vergelijk_6-1.py")
v61 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(v61)

TITELS = {
    "01_inleiding.md": "1 Inleiding",
    "02_context.md": "2 De maatschappelijke context",
    "03_solidariteit.md": "3 Solidariteit in de sociale zekerheid",
    "04_sociaal_statuut.md": "4 Het sociaal statuut van de zelfstandigen",
    "05_methodologie.md": "5 Methodologie",
}
SOORTEN = dict(v61.SOORTEN, opmaak="Opmaak", **{"niet toegelicht": "Niet toegelicht"})
ANNOT = re.compile(r"^<!--\s*wijziging:\s*(.*?)\s*\|\s*(.*?)\s*-->$", re.S)


def alineas_met_annotatie(tekst):
    """Splits in alinea's. Een alinea die enkel uit een wijzigingscommentaar bestaat, hoort bij de volgende.

    Een figuur of tabel bestaat uit meerdere blokken (bijschrift, afbeelding of tabel, Noot, Bron). Een
    commentaar boven het bijschrift geldt voor het hele blok: de volgende afbeelding, tabel, Noot en Bron
    erven de toelichting, tenzij ze zelf een commentaar hebben.
    """
    uit, wachtend, vorige = [], None, None
    tekst = re.sub(r"<!--(?!\s*wijziging:).*?-->", "", tekst, flags=re.S)   # overige commentaar (bv. templatekop) weg
    for blok in [b.strip() for b in tekst.split("\n\n") if b.strip()]:
        m = ANNOT.match(blok)
        if m:
            wachtend = ([s.strip() for s in m.group(1).split(",") if s.strip()], m.group(2))
            continue
        blok = re.sub(r"<!--.*?-->", "", blok, flags=re.S).strip()
        if not blok:
            continue
        onderdeel = blok.startswith(("Noot:", "Bron:", "![", "|"))
        if wachtend is None and onderdeel and vorige is not None:
            wachtend = vorige
        uit.append((blok, wachtend))
        # een bijschrift of een onderdeel geeft zijn toelichting door aan de volgende onderdelen
        vorige = wachtend if (blok.startswith(("**Figuur", "**Tabel")) or onderdeel) else None
        wachtend = None
    return uit


def norm(t):
    return re.sub(r"\s+", " ", t).strip()


def rijen_voor(oud, nieuw):
    """Koppel alinea's. Geeft een lijst (soort, [oude], [(nieuwe, annotatie)])."""
    a = [norm(t) for t in oud]
    b = [norm(t) for t, _ in nieuw]
    sm = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
    rijen = []
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "equal":
            rijen.append(("gelijk", oud[i1:i2], nieuw[j1:j2]))
        elif op == "replace" and (i2 - i1) == (j2 - j1):
            for k in range(i2 - i1):
                rijen.append(("gewijzigd", [oud[i1 + k]], [nieuw[j1 + k]]))
        elif op == "replace":
            # ongelijk aantal: koppel elke nieuwe alinea aan de best passende oude, in volgorde
            gebruikt, vorige = set(), i1 - 1
            for j in range(j1, j2):
                best, score = None, 0.0
                for i in range(max(vorige + 1, i1), i2):
                    r = difflib.SequenceMatcher(a=a[i].split(), b=b[j].split(), autojunk=False).ratio()
                    if r > score:
                        best, score = i, r
                if best is not None and score >= 0.4:
                    for i in range(vorige + 1, best):
                        rijen.append(("geschrapt", [oud[i]], []))
                        gebruikt.add(i)
                    rijen.append(("gewijzigd", [oud[best]], [nieuw[j]]))
                    gebruikt.add(best)
                    vorige = best
                else:
                    rijen.append(("nieuw", [], [nieuw[j]]))
            for i in range(i1, i2):
                if i not in gebruikt:
                    rijen.append(("geschrapt", [oud[i]], []))
        elif op == "delete":
            for i in range(i1, i2):
                rijen.append(("geschrapt", [oud[i]], []))
        elif op == "insert":
            for j in range(j1, j2):
                rijen.append(("nieuw", [], [nieuw[j]]))
    # opeenvolgende nieuwe alinea's samennemen (bv. een nieuwe subsectie), en een geschrapte
    # alinea die direct naast nieuwe tekst staat, samen tonen als herschreven passage
    samen = []
    for r in rijen:
        vorige = samen[-1] if samen else None
        if vorige and r[0] in ("nieuw", "geschrapt") and vorige[0] in ("nieuw", "geschrapt", "herschreven"):
            soort = "nieuw" if (vorige[0] == "nieuw" and r[0] == "nieuw") else (
                "geschrapt" if (vorige[0] == "geschrapt" and r[0] == "geschrapt") else "herschreven")
            samen[-1] = (soort, vorige[1] + r[1], vorige[2] + r[2])
        else:
            samen.append(r)
    return samen


def html_alinea(t):
    """Alinea naar HTML. Tabellen (markdown of HTML uit Word) worden als tabel getoond."""
    if t.startswith("<table"):
        t = re.sub(r"<colgroup>.*?</colgroup>", "", t, flags=re.S)
        t = re.sub(r'\s(style|class)="[^"]*"', "", t)
        return f'<div class="tabel">{t}</div>'
    if t.startswith("|"):
        rijen = [r for r in t.splitlines() if r.strip().startswith("|") and not re.match(r"^\|[\s:|-]+\|$", r.strip())]
        cellen = [[v61.inline_md(c.strip()) for c in r.strip().strip("|").split("|")] for r in rijen]
        kop = "".join(f"<th>{c}</th>" for c in cellen[0])
        rest = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in cellen[1:])
        return f'<div class="tabel"><table><thead><tr>{kop}</tr></thead><tbody>{rest}</tbody></table></div>'
    return f"<p>{v61.cijfers_markeren(v61.inline_md(t))}</p>"


def bouw(titels=None, origineel=None, uit=None, label="Hoofdstuk 1 tot 5", paginatitel="Tekstvergelijking hoofdstuk 1-5",
         inleiding=None, bronlabel="hoofdstuk 1 tot 5", templatelabel="report/templates/01 tot 05", script="vergelijk_hoofdstukken.py"):
    """Bouw de vergelijkingspagina. Zonder argumenten: hoofdstuk 1 tot 5. vergelijk_micro_bijlagen.py
    roept dezelfde functie aan met eigen titels, originelen en uitvoerbestand."""
    titels = titels or TITELS
    origineel = origineel if origineel is not None else imp.schoon_hoofdstukken()
    uit = uit or UIT
    inleiding = inleiding or ("Deze hoofdstukken zijn overgenomen uit het origineel en enkel aangepast waar de leesnota "
                              "daar een concrete aanleiding voor gaf. Ongewijzigde alinea's zijn samengevouwen.")
    teller = {s: 0 for s in SOORTEN}
    secties, overzicht = [], []
    nr = 0
    for naam, titel in titels.items():
        oud = [b.strip() for b in origineel[naam].split("\n\n") if b.strip()]
        nieuw = alineas_met_annotatie((ROOT / "report" / "sections" / naam).read_text(encoding="utf-8"))
        rijen = rijen_voor(oud, nieuw)
        n_gelijk = sum(len(r[1]) for r in rijen if r[0] == "gelijk")
        n_anders = sum(1 for r in rijen if r[0] != "gelijk")
        overzicht.append(f'<tr><td><a href="#h-{naam[:2]}">{html.escape(titel)}</a></td>'
                         f'<td class="n">{len(oud)}</td><td class="n">{n_gelijk}</td><td class="n">{n_anders}</td></tr>')
        delen = [f'<h2 class="hoofdstuk" id="h-{naam[:2]}">{html.escape(titel)}</h2>']
        for soort, o, n in rijen:
            if soort == "gelijk":
                inhoud = "\n".join(html_alinea(t) for t in o)
                meervoud = "" if len(o) == 1 else "'s"
                delen.append(f'<details class="gelijk"><summary>{len(o)} alinea{meervoud} '
                             f'ongewijzigd</summary><div class="gelijk-tekst">{inhoud}</div></details>')
                continue
            nr += 1
            soorten, toelichtingen = [], []
            for _, ann in n:
                if ann:
                    soorten += [s for s in ann[0] if s not in soorten]
                    toelichtingen.append(ann[1])
            if soort == "geschrapt" and "geschrapt" not in soorten:
                soorten.append("geschrapt")
            if soort == "nieuw" and "nieuw" not in soorten:
                soorten.append("nieuw")
            if not toelichtingen:
                soorten.append("niet toegelicht")
            for s in soorten:
                teller[s] = teller.get(s, 0) + 1
            # tekst
            diff_o = diff_n = None
            if soort == "gewijzigd":
                diff_o, diff_n, _ = v61.woorddiff(o[0], n[0][0])
            kol_o = (f"<p>{v61.cijfers_markeren(diff_o)}</p>" if diff_o is not None
                     else ("\n".join(html_alinea(t) for t in o) or '<p class="leeg">Geen overeenkomstige tekst.</p>'))
            kol_n = (f"<p>{v61.cijfers_markeren(diff_n)}</p>" if diff_n is not None
                     else ("\n".join(html_alinea(t) for t, _ in n) or '<p class="leeg">Geschrapt.</p>'))
            chips = "".join(f'<span class="chip chip-{s.replace(" ", "-")}">{SOORTEN.get(s, s)}</span>' for s in soorten)
            toel = " ".join(toelichtingen) or "Geen toelichting in de template."
            modus = "woorden gemarkeerd" if diff_o is not None else {"nieuw": "nieuwe tekst", "herschreven": "herschreven"}.get(soort, "")
            delen.append(f"""
<article class="rij" data-soorten="{' '.join(s.replace(' ', '-') for s in soorten)}" id="r{nr}">
  <header class="rijkop"><span class="nr">{nr:02d}</span><div class="chips">{chips}</div></header>
  <p class="toelichting">{html.escape(toel)}</p>
  <div class="kolommen">
    <section class="kol kol-oud" aria-label="Origineel"><div class="kollabel">Origineel <span class="modus">{modus}</span></div>{kol_o}</section>
    <section class="kol kol-nieuw" aria-label="Nieuw"><div class="kollabel">Nieuw</div>{kol_n}</section>
  </div>
</article>""")
        secties.append("\n".join(delen))

    filters = "".join(
        f'<button type="button" class="filter" data-filter="{s.replace(" ", "-")}" aria-pressed="false">{lab} <span>{teller[s]}</span></button>'
        for s, lab in SOORTEN.items() if teller.get(s, 0) > 0)
    tabel = ('<table class="overzicht"><thead><tr><th>Hoofdstuk</th><th class="n">Alinea\'s origineel</th>'
             '<th class="n">Ongewijzigd</th><th class="n">Wijzigingen</th></tr></thead><tbody>'
             + "".join(overzicht) + "</tbody></table>")

    pagina = v61.PAGINA
    pagina = pagina.replace("<title>Tekstvergelijking §6.1</title>", f"<title>{paginatitel}</title>")
    pagina = pagina.replace("· §6.1 Macroniveau</div>", f"· {label}</div>")
    pagina = pagina.replace("<h1>Tekstvergelijking §6.1: origineel en herwerking</h1>",
                            f"<h1>Tekstvergelijking {label[0].lower() + label[1:]}</h1>")
    pagina = pagina.replace(
        "Passage per passage de oorspronkelijke tekst naast de herwerkte tekst, met per passage wat er veranderde en waarom.",
        inleiding)
    pagina = pagina.replace("§6.1, bijgehouden wijzigingen aanvaard</dd>",
                            f"{bronlabel}, bijgehouden wijzigingen aanvaard, zonder Word-restanten</dd>")
    pagina = pagina.replace("<code>report/templates/06-1_macro.md</code>, eerste herwerkte versie (cijfers ingevuld)",
                            f"<code>{templatelabel}</code>, met de toelichting per wijziging uit de template")
    pagina = pagina.replace("{{RIJEN}}", tabel + "\n".join(secties))
    pagina = pagina.replace("{{FILTERS}}", filters)
    pagina = pagina.replace("{{N_RIJEN}} passages. Gegenereerd door <code>code/tekst/vergelijk_6-1.py</code>; de koppeling tussen alinea's en de toelichting zijn met de hand opgesteld.",
                            f"{nr} wijzigingen. Gegenereerd door <code>code/tekst/{script}</code>; alinea's automatisch gekoppeld, toelichting uit de templates.")
    extra_css = """
  h2.hoofdstuk { font-family: var(--f-display); font-size: 1.5rem; margin: 30px 0 4px; padding-top: 10px; border-top: 2px solid var(--ink); }
  details.gelijk { border: 1px dashed var(--rule); background: var(--surface); padding: 6px 14px; font-size: .85rem; color: var(--muted); }
  details.gelijk summary { cursor: pointer; font-family: var(--f-mono); font-size: .72rem; letter-spacing: .06em; }
  details.gelijk .gelijk-tekst { color: var(--ink-2); margin-top: 8px; max-width: 70rem; }
  details.gelijk .gelijk-tekst p { margin: 0 0 .7em; }
  table.overzicht { border-collapse: collapse; width: 100%; background: var(--surface); border: 1px solid var(--rule); font-size: .9rem; }
  table.overzicht th, table.overzicht td { text-align: left; padding: 7px 12px; border-bottom: 1px solid var(--rule-soft); }
  table.overzicht th { font-family: var(--f-mono); font-size: .68rem; letter-spacing: .08em; text-transform: uppercase; color: var(--muted); }
  table.overzicht .n { text-align: right; font-variant-numeric: tabular-nums; }
  .chip-opmaak { color: var(--muted); } .chip-niet-toegelicht { color: var(--c-interpretatie); background: var(--del-bg); }
  .rijkop .chips { margin-left: 0; }
  .tabel { overflow-x: auto; margin: 0 0 .8em; }
  .tabel table { border-collapse: collapse; font-size: .78rem; }
  .tabel th, .tabel td { border: 1px solid var(--rule-soft); padding: 3px 6px; vertical-align: top; text-align: left; }
  .tabel p { margin: 0; }
  body.filter-actief details.gelijk, body.filter-actief h2.hoofdstuk { display: none; }
</style>"""
    pagina = pagina.replace("</style>", extra_css, 1)
    # bij een actieve filter ook de ongewijzigde blokken verbergen
    pagina = pagina.replace("r.hidden = actief.length > 0 && !actief.some(function (a) { return s.indexOf(a) !== -1; });",
                            "r.hidden = actief.length > 0 && !actief.some(function (a) { return s.indexOf(a) !== -1; });\n    });\n    document.body.classList.toggle('filter-actief', actief.length > 0);\n    rijen.forEach(function () {")
    uit.parent.mkdir(parents=True, exist_ok=True)
    uit.write_text(pagina, encoding="utf-8")
    print(f"geschreven: {uit.relative_to(ROOT)} ({nr} wijzigingen)")
    print({k: v for k, v in teller.items() if v})


if __name__ == "__main__":
    bouw()
