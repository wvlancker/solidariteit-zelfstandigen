"""
Tekstvergelijking §7 (conclusie): oorspronkelijke tekst naast de herwerkte tekst.

    python code/tekst/vergelijk_07.py   ->  output/tekst/vergelijking_07.html

De koppeling tussen alinea's (welke oude alinea overeenkomt met welke nieuwe)
en de toelichting per wijziging staan hieronder in KOPPELING en zijn met de
hand gemaakt. De teksten zelf worden telkens opnieuw ingelezen:
  - origineel: report/import/07_conclusie.md (+ voetnoten uit het volledige import-bestand)
  - nieuw:     report/sections/07_conclusie.md (ingevulde versie van de template)
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
ORIG = ROOT / "report" / "import" / "07_conclusie.md"
ORIG_VOLLEDIG = ROOT / "report" / "import" / "rapport_finaal_TC_volledig.md"
NIEUW = ROOT / "report" / "sections" / "07_conclusie.md"
UIT = ROOT / "output" / "tekst" / "vergelijking_07.html"


def alineas(pad):
    t = re.sub(r"<!--.*?-->", "", pad.read_text(encoding="utf-8"), flags=re.S)
    return [a.strip() for a in t.split("\n\n") if a.strip()]


# ---------------------------------------------------------------------------
# Koppeling: (oude alinea's, nieuwe alinea's, soorten wijziging, locatie, toelichting)
# Soorten: cijfer, interpretatie, nieuw, geschrapt, redactie, figuur
# Oude voetnoten: 'fn25', 'fn26'
# ---------------------------------------------------------------------------
KOPPELING = [
    ([0, 1], [0, 1], ["redactie"], "Onderzoeksvraag",
     "Inhoud ongewijzigd. Taal rechtgezet: 'des te meer relevanter' (dubbele vergrotende trap, leesnota E) wordt 'des te "
     "relevanter'; zinsbouw vereenvoudigd."),
    ([2], [2], ["redactie"], "Moeilijkheid van de vergelijking",
     "Inhoud ongewijzigd. 'Verontschuldigd' wordt 'verschuldigd' (leesnota E)."),
    ([3], [3], ["redactie"], "Aanpak",
     "Inhoud ongewijzigd; periodes zonder spaties rond het streepje."),
    ([4], [4, 5], ["interpretatie", "nieuw"], "Stelselniveau: definities",
     "Tussentitels toegevoegd (de conclusie volgt nu de opbouw stelsel, verzekerde, rechtsvorm, beleid, beperkingen). "
     "Nieuw: twee zinnen die zeggen wat een dalende beroepssolidariteit wel en niet betekent, en dat ze geen norm is "
     "(leesnota D5 en I6). Dat voorkomt de lezing 'zelfstandigen worden minder solidair'. Nieuw (22 september, op vraag "
     "van Wim): de nuance dat beroepssolidariteit geen norm is, maar wel betekenis heeft voor wederkerigheid en draagvlak, "
     "met literatuur (Campbell & Morgan, 2005; Koreh et al., 2026; van Oorschot, 2000; Reeskens & van Oorschot, 2013; "
     "Ferrera, 2005)."),
    ([5], [6], ["interpretatie", "cijfer", "geschrapt"], "Beroepssolidariteit: oorzaak van de daling",
     "Kernwijziging (leesnota B1, G2, H2). Oud: de snellere daling is 'vooral te wijten aan lagere ontvangsten per hoofd', "
     "hangt samen met vennootschappen en bijberoepers, en 'voornamelijk' met de vennootschappen. Nieuw: over de volledige "
     "periode verklaart de snellere uitgavengroei de daling (Z1 uitgaven +21%, bijdragen +7%), grotendeels door rijpende "
     "pensioenrechten en bewuste uitbreidingen; sinds 2015 dalen de bijdragen per zelfstandige (-13%), waarvan de tax shift "
     "mechanisch de helft verklaart. Geschrapt: de redenering dat bijberoepers 'in principe geen rechten openen' en dus de "
     "daling niet verklaren (ongegrond, leesnota D4), en de toeschrijving aan de vennootschappen. Niveaus en procentpunten "
     "toegevoegd. Nieuw (controle 22 september): de tax shift als beleidskeuze die de bijdragen in beide stelsels verlaagde, "
     "en de bijberoepers (Z2 -3%), die geen volwaardige rechten openen."),
    ([], [7], ["nieuw", "interpretatie"], "Vennootschapsbijdrage op stelselniveau",
     "Nieuwe alinea, overgenomen uit de herwerkte §6.1 en Bijlage 6: erosie door niet-indexering (-33% reëel sinds 2006, "
     "-1,5 procentpunt, ongeveer €139 miljoen), netto ongeveer 9% van de daling, en de kwalificatie dat de groei van het "
     "aantal vennootschappen de beroepssolidariteit niet heeft versterkt tegenover eenmanszaken (omslagpunt €2.000). "
     "Uitholling van de gewone bijdragen niet meetbaar op macroniveau; extern verankerd bij de Hoge Raad van Financiën. "
     "Op vraag van Wim (22 september) vereenvoudigd zoals §6.1.2: het omslagpunt als vergelijking van vennootschapsbijdrage "
     "en gewone bijdrage."),
    ([6], [8], ["cijfer", "interpretatie"], "Nationale solidariteit",
     "Oud: de nationale solidariteit groeit 'sterker bij de werknemers'. Nieuw: in procentpunt van dezelfde orde (+10,6 "
     "en +9,3 over 2000-2023; leesnota D6). Niveau 2023 toegevoegd (45% tegenover 30%). Samenstelling (22 september, "
     "variant A+B): het duidelijke verschil in toelagen binnen de nationale solidariteit zit in 2017-2019 (14-15% "
     "tegenover 31-36%) en is na corona kleiner (27% tegenover 32% in 2023); nieuw is dat de btw 24% van alle inkomsten "
     "van het zelfstandigenstelsel financiert, tegenover 17% bij werknemers (zelfde zin in §6.1). 'Overheidsdotatie' "
     "vervangen door 'toelagen van publieke overheden' (leesnota D1). Keerpunt 2017 behouden."),
    ([7, "fn25"], [9], ["redactie", "cijfer"], "Verdelingseffecten van de alternatieve financiering",
     "Redenering en bronnen (Decoster et al., 2007; Warren, 2008) behouden. Voetnoot 25 over het btw-aandeel is naar §6.1 "
     "verhuisd (daar voetnoot 'btw'); hier een verwijzing. De zin over de coronacrisis is onderbouwd: de schok werd "
     "opgevangen met toelagen, die in 2020 62% van de nationale solidariteit uitmaakten (zoals in §6.1)."),
    ([8], [10, 11, 12], ["redactie", "interpretatie"], "Verzekerdenniveau: definities en verticale solidariteit bijdragezijde",
     "Definities en bevinding behouden, opgesplitst in een definitiealinea en een bevindingsalinea. Nieuw: de "
     "kwalificatie dat het om persoonlijke bijdragen gaat zonder werkgeversbijdragen (leesnota A), de grens van €6.000 "
     "tot waar de eenmanszaak meer betaalt dan werknemers (uit §6.2.1), en de Kakwani-index gewogen naar BE-SILC 2024 en "
     "Statbel ADI 2023 als hoofdversie, met de ongewogen versie tussen haakjes (leesnota K1). Rechtgezet: de zelfstandigen "
     "'met lagere en middeninkomens betalen meer' klopte niet; de verhouding stijgt tot een middeninkomen en daalt pas "
     "boven het plafond."),
    ([9], [13], ["redactie", "nieuw"], "Horizontale solidariteit bijdragezijde",
     "Bevinding behouden. Nieuw: één zin dat een strakke band tussen bijdrage en uitkering niets zegt over het niveau "
     "van de bescherming (leesnota C5), zodat deze bevinding niet tegen die van de uitkeringszijde wordt uitgespeeld. "
     "De naamgeving van de indicator (equivalentie als wederkerigheid, leesnota B3) is niet aangepast: dat is een keuze "
     "voor het hele rapport. Pensioenen (J1, K10): zelfstandigen blijven netto-ontvanger omdat de maximale bijdrage "
     "onder het maximale pensioen blijft (verklaring rechtgezet op 22 september: het pensioen haalt zijn maximum bij "
     "€4.000, de bijdrage pas bij €5.250), met de kanttekening dat het om maandbedragen gaat."),
    ([10], [14], ["redactie"], "Uitkeringszijde",
     "Inhoud ongewijzigd, korter geformuleerd."),
    ([11], [15], ["redactie"], "Minimale levensstandaard",
     "'Dienovereenkomstig' geschrapt: de pensioenzin volgt niet uit de vorige. 'Pas vanaf een middeninkomen' wordt 'pas "
     "boven €2.000': de garantiegraad van werknemers ligt onder 100% tot en met €2.000 (controle 22 september). Nieuw: "
     "bij arbeidsongeschiktheid van meer dan zes maanden is de uitkering ook bij lage inkomens toereikend, en een "
     "verwijzing naar de koppels in Bijlage 7. Die verwijzing staat er nu mét cijfers: leesnota J2 is gecorrigeerd "
     "(netto uitkering samenwonende zelfstandige bij ziekte gelijk aan bruto), zodat de vervangingsgraad van 28% "
     "voor samenwonende zelfstandigen tegenover 36% voor alleenstaanden vermeld kan worden."),
    ([12], [16, 17], ["redactie", "cijfer"], "Rechtsvorm en bezoldiging",
     "Eigen tussentitel. Bevinding behouden; de gemiddelden uit Tabel 8 (7,4% bij 0% loon tegenover 26,1% bij een "
     "eenmanszaak, nu als plaatshouder: 7% tegenover 26%) toegevoegd, met de kwalificatie 'gemiddeld over de gesimuleerde "
     "inkomensposities' (leesnota B4) en de gewogen cijfers (14% tegenover 28%). Nieuw (op vraag van Wim): dividenduitkering "
     "is geen randgeval, met de terugkoppeling naar §5.2.2.4 (VVPR-bis, ongeveer 250.000 kleine vennootschappen)."),
    ([13], [18, "fn:c-kanaal"], ["interpretatie", "geschrapt", "nieuw"], "Vervennootschappelijking: gevolgen",
     "Oud: vervennootschappelijking is een probleem op stelsel- én verzekerdenniveau, en dalende beroepssolidariteit en "
     "vennootschappen 'dreigen een vicieuze cirkel te veroorzaken'. Geschrapt: de vicieuze cirkel en de voorspelling, "
     "want de versterking van twee dalingen is op macroniveau niet geobserveerd (leesnota H2). Nieuw: vooral een probleem "
     "op verzekerdenniveau; op stelselniveau een kanaalverschuiving van bijdragen naar vennootschapsbelasting en roerende "
     "voorheffing die via de nationale solidariteit terugvloeien (leesnota C1), met voetnoot dat het om kanalen gaat, "
     "niet om individuele terugbetaling. Het slot over de lagere inkomensgroepen blijft; 'overwegend op btw' wordt 'voor "
     "meer dan de helft' (54% in 2023)."),
    ([14], [19, 20, 21, 23], ["interpretatie", "geschrapt", "nieuw"], "Beleid: gewone bijdragen en maximumgrens",
     "Herschreven volgens leesnota deel I en K. Oud: 'het lijkt aangewezen de beroepssolidariteit te versterken'; progressiviteit "
     "'zet geen zoden aan de dijk' en 'zou de inkomsten verder doen dalen'; maximumgrens optrekken lost niets op want "
     "weinig zelfstandigen erboven. Geschrapt: de beroepssolidariteit als doel (I6) en de non-sequitur dat progressiviteit "
     "de opbrengst verlaagt (I5). Nieuw: onderscheid verdeling en niveau, met een statische orde van grootte op basis "
     "van ABC-verslag 2022/04 (K5). Verdeling (K2-K4, K8, herwerkt met Wim op 22 september): of men de verticale "
     "solidariteit wil versterken is een normatieve keuze; de regressiviteit ten opzichte van de levensstandaard zit "
     "boven het plafond (33% naar 12%), niet in de degressieve schijf, die enkel ten opzichte van het beroepsinkomen "
     "regressief is; de 23% bij €1.550 is het gewone tarief; een vermindering onderaan zoals de werkbonus ligt minder voor "
     "de hand, omdat een laag beroepsinkomen bij zelfstandigen mee gekozen wordt; het opbrengstneutrale pakket is "
     "geschrapt; 96-98% van de zelfstandigen heeft een lagere levensstandaard dan €6.000 (was 71%, huishoudinkomen). "
     "Maximumgrens (K6): statisch +6% bijdragen, €200-310 miljoen, met de kanttekeningen gedrag en band met de rechten; "
     "op vraag van Wim uitgedrukt als afweging tussen verticale en horizontale solidariteit."),
    ([15, "fn26"], [22, "fn:c-hervorming"], ["interpretatie", "geschrapt", "nieuw"], "Beleid: vennootschapsbijdrage",
     "Oud: de hervorming van 2004 heeft 'niet geleid tot een stijging van de bijdrage per vennootschap, het tegendeel is "
     "waar'; een verhoging en differentiatie versterkt ook de horizontale en verticale solidariteit op verzekerdenniveau. "
     "Geschrapt: de claim over 2004 (de gemiddelde bijdrage steeg in 2004-2005, zie §6.1) en de claim dat een forfait de "
     "verticale solidariteit versterkt (leesnota B5). Nieuw: diagnose erosie door niet-indexering; de hervorming van 24 "
     "april 2026 (geverifieerd: vier bedragen, balanstotaal, geïndexeerde drempel, vanaf 1 januari 2026) met één "
     "kanttekening (indexering van de bedragen; I3). De zin over de prikkel van het balanstotaal is op vraag van Wim "
     "geschrapt: loon en dividend verlagen het balanstotaal even sterk; de verbreding van de bijdragebasis "
     "naar dividenden benoemd als instrument dat wél aangrijpt, zonder aanbeveling (B5). Voetnoot 26 uitgewerkt tot "
     "bronvermelding."),
    ([], [24], ["nieuw", "cijfer"], "Beleid: de financieringskloof",
     "Nieuwe alinea (leesnota I5): herstel van de beroepssolidariteit van 2006 vraagt ongeveer €568 miljoen per jaar, "
     "volledige indexering van de vennootschapsbijdrage levert ongeveer 25% daarvan; de samenstelling van de nationale "
     "solidariteit is de eigenlijke beleidsvraag. Correctie op de leesnota, die €586 miljoen vermeldde. K7: het afschaffen "
     "van het plafond zou statisch 34-55% van de kloof dichten; 'overwegend op btw' wordt 'voor meer dan de helft'."),
    ([16], [25, 26], ["redactie", "nieuw"], "Beperkingen en verder onderzoek",
     "Bestaande beperkingen behouden. Nieuw: geen inkomensnoemer op macroniveau en geen puntschatting in Bijlage 6; "
     "gemiddelden en Kakwani-index over het simulatierooster (B4); persoonlijke bijdragen zonder werkgeversbijdragen (A); "
     "endogeniteit van rechtsvorm en bezoldiging (C6); tweede pijler (C2); wat de weging verandert en dat zelfstandigen "
     "onder de minimumdrempel ontbreken (K9). De aparte alinea met onderzoeksvragen is niet meer opgenomen. VAPZ "
     "voluit (afkortingen, 22 september 2026); 'vervangingsratio's' wordt 'vervangingsgraden' (D7)."),
    ([17], [27, 28], ["interpretatie", "redactie"], "Tot besluit",
     "Nuance van het antwoord behouden. Oud slot: 'de grote uitdaging is de beroepssolidariteit in stand te houden'. "
     "Nieuw: de uitdaging ligt minder in het niveau van de beroepssolidariteit dan in de verdeling van de lasten, binnen "
     "het stelsel en in de samenleving (consistent met I6). Taalfout 'in andere de nadruk' weggewerkt. Herschreven door "
     "Wim (22 september): verklaring van de daling aangevuld met de bijdragen sinds 2015, focus op de uitdaging binnen "
     "het stelsel (rechtsvorm en bezoldiging, leesnota F), en een slotzin over draagvlak."),
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
    oud_fn = {f"fn{n}": re.search(rf"^\[\^{n}\]: (.+)$", volledig, flags=re.M).group(1) for n in (25, 26)}
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


PAGINA = r"""<title>Tekstvergelijking conclusie</title>
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
    <div class="eyebrow">Hoe solidair is de sociale zekerheid voor zelfstandigen? · §7 Conclusie</div>
    <h1>Tekstvergelijking §7: origineel en herwerking</h1>
    <p class="standfirst">Passage per passage de oorspronkelijke tekst naast de herwerkte tekst, met per passage wat er veranderde en waarom.</p>
    <dl class="meta">
      <dt>Origineel</dt><dd><code>Rapport UNIZO_finaal_TC.docx</code>, §7 Conclusie, bijgehouden wijzigingen aanvaard</dd>
      <dt>Nieuw</dt><dd><code>report/templates/07_conclusie.md</code>, herwerkte versie van 22 september 2026 (alle cijfers als plaatshouder ingevuld, voorstellen K1-K9 verwerkt, daarna nagelezen en herschreven door Wim en gecontroleerd tegen §6; stand na de beslissingen van Wim over de openstaande punten, 22 september 2026, avond)</dd>
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

  <footer>{{N_RIJEN}} passages. Gegenereerd door <code>code/tekst/vergelijk_07.py</code>; de koppeling tussen alinea's en de toelichting zijn met de hand opgesteld.</footer>
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
