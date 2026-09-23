"""
Stap m06: de figuren van het microdeel -> output/figures/

Maakt Figuur 8, 9, 10 en 11 (§6.2, alleenstaanden) en de bijlagefiguren B7.1, B7.2 en
B7.3 (Bijlage 7, koppels met twee kinderen), telkens als PNG (300 dpi) en SVG, plus de
geplotte data in output/tables/figuurdata/. Invoer: data/processed/micro_indicatoren.csv
(stap m05).

Zelfde huisstijl als het macrodeel
----------------------------------
Kleuren, lettertypes, lijndiktes, opmaak van getallen en de functie die figuur, SVG en
data wegschrijft, komen rechtstreeks uit code/macro/05_figures.py. Zo kan de stijl maar
op één plaats wijzigen. Specifiek voor het microdeel:

- De x-as is het netto beschikbaar maandinkomen in euro, op schaal. In het werkboek
  stonden de 34 posities op gelijke afstand, terwijl de stappen verschillen (€250 tot
  €7.000, €500 tot €10.000, €1.000 tot €15.000). Op schaal tekenen voorkomt dat de
  bovenkant van de verdeling visueel uitgerekt wordt.
- Kleur volgt het type: werknemer oranje (zoals in het macrodeel), eenmanszaak blauw
  (de kleur van de zelfstandigen in het macrodeel), de vennootschappen elk een eigen
  kleur. Lijnstijl volgt de uitkeringsmaand van de werknemer (doorlopend, gestreept,
  gestippeld), of het type bij de zelfstandigen, zodat de figuren ook in grijstinten
  leesbaar blijven.
- Lijnen krijgen een label aan hun eindpunt (€15.000), geen legenda.
- Een horizontale lijn op 100% waar die grens een betekenis heeft: volledige
  equivalentie, volledig behoud van de levensstandaard, minimale levensstandaard.
- Vennootschap met 100% loon met en zonder voordelen van alle aard lopen vrijwel gelijk
  (verschil kleiner dan 0,5 procentpunt); we tonen de variant zonder VAA, zoals bij de
  pensioenen. Enkel bij de garantiegraad voor koppels (B7.3) bestaat enkel de VAA-variant,
  maar die wordt daar niet getoond.

De pensioenen zijn herberekend volgens leesnota J1 (plafond op het inkomen, niet op het pensioen).

Uitvoeren:  python code/micro/m06_figuren.py
"""

import importlib.util
import sys

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.ticker import FuncFormatter, MultipleLocator

from common_micro import DATA_PROCESSED, ROOT

# ---------------------------------------------------------------------------
# Huisstijl overnemen uit code/macro/05_figures.py
# ---------------------------------------------------------------------------
# De bestandsnaam begint met een cijfer, dus 'import 05_figures' kan niet: we laden het
# bestand als module. Dat voert enkel de stijldefinities uit (rcParams, functies), niet
# main(). 05_figures importeert zelf 'common' uit code/macro/, dus die map moet op het pad.
MACRO = ROOT / "code" / "macro"
sys.path.insert(0, str(MACRO))
_spec = importlib.util.spec_from_file_location("stijl_macro", MACRO / "05_figures.py")
stijl = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(stijl)
sys.path.remove(str(MACRO))

KLEUR, BREEDTE, PROCENT, komma = stijl.KLEUR, stijl.BREEDTE, stijl.PROCENT, stijl.komma

# Kleur en lijnstijl per type (lijnstijl: zie DASH)
TYPE_STIJL = {
    "WN": ("Werknemer", KLEUR["oranje"], "-"),
    "ZS": ("Zelfstandige", KLEUR["blauw"], "-"),
    "ZE": ("Eenmanszaak", KLEUR["blauw"], "-"),
    "ZV100": ("Venn. 100% loon", KLEUR["violet"], "--"),
    "ZV100VAA": ("Venn. 100% loon (VAA)", KLEUR["violet"], "--"),
    "ZV75": ("Venn. 75% loon", KLEUR["aqua"], "-."),
    "ZV50": ("Venn. 50% loon", KLEUR["magenta"], ":"),
    "ZV00": ("Venn. 0% loon", KLEUR["groen"], "--."),
}
# Werknemer per uitkeringsmaand: zelfde kleur, andere lijnstijl
MAAND_STIJL = {"2": "-", "1-3": "-", "3-6": "--", "4-6": "--", "7-12": ":"}

DASH = {
    "-": None,
    "--": (0, (5, 2.5)),
    ":": (0, (1.2, 1.8)),
    "-.": (0, (6, 2, 1.5, 2)),
    "--.": (0, (3, 1.8, 1, 1.8, 1, 1.8)),
}

# Hoogte van één paneel in inch. Drie panelen plus bijschrift en noot moeten samen op één
# pagina passen: de tekstspiegel is 24,1 cm hoog, dus de figuur zelf mag hoogstens ongeveer
# 20 cm (7,9 inch) worden.
PANEELHOOGTE = 2.5

EURO = FuncFormatter(lambda x, _: f"€{komma(x)}")
X_MAX = 15000
X_EXTRA = 4300          # ruimte rechts voor de eindlabels, in euro op de x-as


# ---------------------------------------------------------------------------
# Hulpfuncties
# ---------------------------------------------------------------------------
def lees():
    return pd.read_csv(DATA_PROCESSED / "micro_indicatoren.csv", dtype={"maand": str})


def reeks(d, indicator, gezin, risico, typ, maand="-"):
    s = d[(d.indicator == indicator) & (d.gezin == gezin) & (d.risico == risico) & (d.type == typ)
          & (d.maand == maand)].sort_values("positie")
    assert len(s) == 34, (indicator, gezin, risico, typ, maand)
    return s.set_index("positie")["waarde"]


def lijn(ax, s, kleur, stijl_):
    dash = DASH[stijl_]
    kw = {"linestyle": dash} if dash else {}
    ax.plot(s.index, s.values, color=kleur, solid_capstyle="round", **kw)


def inkomens_as(ax, onderste=True):
    """x-as in euro, op schaal, met ruimte rechts voor de labels."""
    ax.set_xlim(1000, X_MAX + X_EXTRA)
    ax.set_xticks(range(2000, X_MAX + 1, 2000))
    ax.xaxis.set_major_formatter(EURO)
    ax.tick_params(axis="x", length=3)
    ax.spines["bottom"].set_bounds(1000, X_MAX + 300)
    if onderste:
        ax.set_xlabel("Netto beschikbaar maandinkomen (vóór het risico)")


def eindlabels(ax, labels, min_afstand):
    """Label aan het eindpunt van elke lijn; labels die te dicht liggen worden uit elkaar geschoven.

    Zelfde logica als eindlabels() in 05_figures.py, maar met een horizontale verschuiving in
    euro in plaats van in jaren.
    """
    # Lijnen van dezelfde kleur die op hetzelfde punt eindigen (bv. werknemer in verschillende
    # uitkeringsmaanden) krijgen één gezamenlijk label: "Werknemer (maand 2, 3-6, 7-12)".
    samengevoegd = []
    for y, tekst, kleur in labels:
        for i, (y2, tekst2, kleur2) in enumerate(samengevoegd):
            if kleur2 == kleur and abs(y2 - y) < 0.003:
                if tekst2.endswith(")") and "(maand" in tekst2 and "(maand" in tekst:
                    tekst = tekst2[:-1] + ", " + tekst.split("(maand ")[1]
                else:
                    tekst = tekst2
                samengevoegd[i] = (y2, tekst, kleur)
                break
        else:
            samengevoegd.append((y, tekst, kleur))
    labels = sorted(samengevoegd, key=lambda t: t[0])
    posities = []
    for y, tekst, kleur in labels:
        if posities and y - posities[-1] < min_afstand:
            y = posities[-1] + min_afstand
        posities.append(y)
    # Als de bovenste labels boven de as uitsteken, schuiven we de hele stapel naar beneden
    top = ax.get_ylim()[1]
    if posities and posities[-1] > top:
        verschuiving = posities[-1] - top
        posities = [p - verschuiving for p in posities]
        # en opnieuw uit elkaar van onder naar boven houden
        for i in range(len(posities) - 2, -1, -1):
            if posities[i + 1] - posities[i] < min_afstand:
                posities[i] = posities[i + 1] - min_afstand
    for (y0, tekst, kleur), y in zip(labels, posities):
        ax.annotate(tekst, xy=(X_MAX, y0), xytext=(X_MAX + 250, y), textcoords="data", va="center", ha="left",
                    fontsize=7.4, color=kleur, fontweight="bold", annotation_clip=False)


def procent_as(ax, bovengrens, stap, label, lijn100=True):
    ax.set_ylim(0, bovengrens)
    ax.yaxis.set_major_formatter(PROCENT)
    ax.yaxis.set_major_locator(MultipleLocator(stap))
    ax.set_ylabel(label)
    if lijn100:
        ax.axhline(1, color=KLEUR["inkt2"], linewidth=0.6, zorder=0.5)


def paneel(ax, d, series, titel, bovengrens, stap, ylabel, min_afstand, lijn100=True, eerste=False):
    """Eén paneel. series: lijst van (indicator, gezin, risico, type, maand, label).
    min_afstand: minimale afstand tussen eindlabels, als fractie van de hoogte van de y-as."""
    data, labels = {}, []
    for ind, gezin, risico, typ, maand, label in series:
        s = reeks(d, ind, gezin, risico, typ, maand)
        _, kleur, st = TYPE_STIJL[typ]
        if typ == "WN" and maand != "-":
            st = MAAND_STIJL[maand]
        lijn(ax, s, kleur, st)
        labels.append((s.iloc[-1], label, kleur))
        data[label] = s
    # De bovengrens van elk paneel staat vast (vergelijkbaarheid tussen panelen). Wijzigen de
    # onderliggende cijfers, dan mag een reeks niet stilzwijgend buiten beeld vallen.
    hoogste = max(s.max() for s in data.values())
    assert hoogste <= bovengrens + 1e-9, (
        f"paneel '{titel}': hoogste waarde {hoogste:.3f} ligt boven de as ({bovengrens}); "
        f"pas de bovengrens aan in m06_figuren.py")
    procent_as(ax, bovengrens, stap, ylabel, lijn100)
    ax.set_title(titel, pad=6)
    # min_afstand is een fractie van de hoogte van de as (zo blijft de afstand tussen
    # labels in centimeter gelijk, ongeacht de schaal van het paneel)
    eindlabels(ax, labels, min_afstand * bovengrens)
    return pd.DataFrame(data)


def bewaar(fig, naam, delen: dict):
    """Figuur en data wegschrijven met bewaar() uit 05_figures.py; data per paneel naast elkaar."""
    data = pd.concat(delen, axis=1)
    data.columns = [f"{p} | {c}" for p, c in data.columns]
    data.index.name = "netto_beschikbaar_maandinkomen"
    stijl.bewaar(fig, naam, data)


def types(ind, gezin, risico, lijst):
    return [(ind, gezin, risico, t, "-", TYPE_STIJL[t][0]) for t in lijst]


ZELF_BIJDRAGE = ["ZE", "ZV100", "ZV75", "ZV50", "ZV00"]


# ===========================================================================
# Figuur 8: bijdragen in verhouding tot de draagkracht
# ===========================================================================
def figuur8(d):
    fig, ax = stijl.nieuwe_figuur(figsize=(BREEDTE, 4.0))
    series = types("bijdrage_ratio", "-", "-", ["WN"] + ZELF_BIJDRAGE)
    data = paneel(ax, d, series, "", 0.40, 0.05, "Sociale bijdragen / netto\nbeschikbaar maandinkomen",
                  min_afstand=0.05, lijn100=False)
    inkomens_as(ax)
    bewaar(fig, "fig08_bijdragen_draagkracht", {"bijdrage_ratio": data})


# ===========================================================================
# Figuur 9 / B7.1: equivalentiegraad
# ===========================================================================
def figuur_equivalentie(d, gezin, naam, met_pensioen):
    n = 3 if met_pensioen else 2
    fig, assen = stijl.nieuwe_figuur(n, 1, figsize=(BREEDTE, PANEELHOOGTE * n + 0.4), sharex=True)
    delen = {}
    zelf = ["ZE", "ZV100", "ZV75", "ZV50", "ZV00"]
    delen["A ziekte"] = paneel(
        assen[0], d, [("equivalentiegraad", gezin, "ziekte", "WN", "2", "Werknemer (maand 2)")]
        + types("equivalentiegraad", gezin, "ziekte", zelf),
        "(A) Primaire arbeidsongeschiktheid", 2.75, 0.5, "Bijdrage / uitkering", 0.05)
    delen["B werkloosheid"] = paneel(
        assen[1], d, [("equivalentiegraad", gezin, "werkloosheid", "WN", "1-3", "Werknemer (maand 1-3)")]
        + types("equivalentiegraad", gezin, "werkloosheid", zelf),
        "(B) Werkloosheid / overbruggingsrecht", 2.75, 0.5, "Bijdrage / uitkering", 0.05)
    if met_pensioen:
        delen["C pensioen"] = paneel(
            assen[2], d, types("equivalentiegraad", "-", "pensioen", ["WN"] + zelf),
            # tot 200%: na de correctie van het pensioenplafond (J1) loopt de equivalentiegraad
            # van de werknemer bij €15.000 op tot ongeveer 175%
            "(C) Pensioen", 2.0, 0.5, "Bijdrage / uitkering", 0.05)
    for i, ax in enumerate(assen):
        inkomens_as(ax, onderste=(i == n - 1))
    bewaar(fig, naam, delen)


# ===========================================================================
# Figuur 10 / B7.2: vervangingsgraad
# ===========================================================================
def figuur_vervanging(d, gezin, naam, met_pensioen):
    n = 3 if met_pensioen else 2
    fig, assen = stijl.nieuwe_figuur(n, 1, figsize=(BREEDTE, PANEELHOOGTE * n + 0.4), sharex=True)
    delen = {}
    delen["A ziekte"] = paneel(
        assen[0], d, [("vervangingsgraad", gezin, "ziekte", "ZS", "-", "Zelfstandige")]
        + [("vervangingsgraad", gezin, "ziekte", "WN", m, f"Werknemer (maand {m})") for m in ("2", "3-6", "7-12")],
        "(A) Primaire arbeidsongeschiktheid", 1.25, 0.25, "Uitkering / netto\nbeschikbaar inkomen", 0.05)
    delen["B werkloosheid"] = paneel(
        assen[1], d, [("vervangingsgraad", gezin, "werkloosheid", "ZS", "-", "Zelfstandige")]
        + [("vervangingsgraad", gezin, "werkloosheid", "WN", m, f"Werknemer (maand {m})") for m in ("1-3", "4-6", "7-12")],
        "(B) Werkloosheid / overbruggingsrecht", 1.25, 0.25, "Uitkering / netto\nbeschikbaar inkomen", 0.05)
    if met_pensioen:
        delen["C pensioen"] = paneel(
            assen[2], d, types("vervangingsgraad", "-", "pensioen", ["WN", "ZE", "ZV100", "ZV75", "ZV50", "ZV00"]),
            "(C) Pensioen", 1.25, 0.25, "Uitkering / netto\nbeschikbaar inkomen", 0.05)
    for i, ax in enumerate(assen):
        inkomens_as(ax, onderste=(i == n - 1))
    bewaar(fig, naam, delen)


# ===========================================================================
# Figuur 11: garantiegraad, alleenstaanden
# ===========================================================================
def figuur11(d):
    fig, assen = stijl.nieuwe_figuur(3, 1, figsize=(BREEDTE, PANEELHOOGTE * 3 + 0.4), sharex=True)
    delen = {}
    delen["A ziekte"] = paneel(
        assen[0], d, [("garantiegraad", "alleen", "ziekte", "ZS", "-", "Zelfstandige")]
        + [("garantiegraad", "alleen", "ziekte", "WN", m, f"Werknemer (maand {m})") for m in ("2", "3-6", "7-12")],
        "(A) Primaire arbeidsongeschiktheid", 2.5, 0.5, "Uitkering /\nreferentiebudget", 0.05)
    delen["B werkloosheid"] = paneel(
        assen[1], d, [("garantiegraad", "alleen", "werkloosheid", "ZS", "-", "Zelfstandige")]
        + [("garantiegraad", "alleen", "werkloosheid", "WN", m, f"Werknemer (maand {m})") for m in ("1-3", "4-6", "7-12")],
        "(B) Werkloosheid / overbruggingsrecht", 2.5, 0.5, "Uitkering /\nreferentiebudget", 0.05)
    delen["C pensioen"] = paneel(
        assen[2], d, types("garantiegraad", "-", "pensioen", ["WN", "ZE", "ZV100", "ZV75", "ZV50", "ZV00"]),
        "(C) Pensioen", 2.5, 0.5, "Uitkering /\nreferentiebudget", 0.05)
    for i, ax in enumerate(assen):
        inkomens_as(ax, onderste=(i == 2))
    bewaar(fig, "fig11_garantiegraad_alleenstaanden", delen)


# ===========================================================================
# Figuur B7.3: garantiegraad, koppels (partner met laag loon)
# ===========================================================================
def figuurB73(d):
    fig, assen = stijl.nieuwe_figuur(2, 1, figsize=(BREEDTE, 5.9), sharex=True)
    delen = {}
    for ax, risico, titel, maanden, sleutel in (
            (assen[0], "ziekte", "(A) Primaire arbeidsongeschiktheid", ("2", "3-6", "7-12"), "A ziekte"),
            (assen[1], "werkloosheid", "(B) Werkloosheid / overbruggingsrecht", ("1-3", "4-6", "7-12"), "B werkloosheid")):
        series = types("garantiegraad", "koppel_laag", risico, ["ZE", "ZV00"]) + \
                 [("garantiegraad", "koppel_laag", risico, "WN", m, f"Werknemer (maand {m})") for m in maanden]
        delen[sleutel] = paneel(ax, d, series, titel, 2.25, 0.25, "Gezinsinkomen /\nreferentiebudget", 0.05)
    for i, ax in enumerate(assen):
        inkomens_as(ax, onderste=(i == 1))
    bewaar(fig, "figB7-3_garantiegraad_koppels", delen)


def main():
    (ROOT / "output" / "figures").mkdir(parents=True, exist_ok=True)
    (ROOT / "output" / "tables" / "figuurdata").mkdir(parents=True, exist_ok=True)
    d = lees()
    figuur8(d)
    figuur_equivalentie(d, "alleen", "fig09_equivalentiegraad_alleenstaanden", met_pensioen=True)
    figuur_vervanging(d, "alleen", "fig10_vervangingsgraad_alleenstaanden", met_pensioen=True)
    figuur11(d)
    figuur_equivalentie(d, "koppel", "figB7-1_equivalentiegraad_koppels", met_pensioen=False)
    figuur_vervanging(d, "koppel", "figB7-2_vervangingsgraad_koppels", met_pensioen=False)
    figuurB73(d)


if __name__ == "__main__":
    main()
