"""
Stap 5: de figuren van het macrodeel -> output/figures/

Maakt Figuur 1, 2, 3, 4, 5, 6, 7 en de bijlagefiguren B4.1, B4.2 en B5.1,
telkens als PNG (300 dpi, voor Word) en SVG (vectorformaat). Voor elke figuur
wordt ook de geplotte data weggeschreven naar output/tables/figuurdata/, zodat
elke lijn en elke staaf controleerbaar is.

Ontwerpkeuzes (gelden voor alle figuren)
----------------------------------------
- Dezelfde inhoud als in het rapport, in een consistente huisstijl.
- Geen tweede y-as. Figuur 4 en 6 hadden in het rapport een index op de
  linkeras en een ratio/aandeel op de rechteras. Twee schalen op één as
  laten de lezer verbanden zien die er niet zijn (waar de lijnen elkaar
  kruisen hangt enkel af van de gekozen schaal). Daarom staan ze nu in twee
  panelen boven elkaar, met dezelfde tijdas.
- Kleur volgt de entiteit binnen een figuur, lijnstijl volgt de maatstaf
  (bv. doorlopend = aantal, gestreept = bijdragen per capita). Zo blijven de
  figuren leesbaar in grijstinten en voor lezers met kleurenblindheid.
- Kleuren komen uit een palet dat gevalideerd is op kleurenblindheid.
- Decimale komma en procentteken, zoals in de Nederlandstalige tekst.
- Aandelen en ratio's op een as die bij 0 begint.
- Lijnen krijgen een label aan hun eindpunt in plaats van een legenda.
- Tijdreeksen over financiering tonen twee periodebanden (tax shift 2016-2018,
  corona 2020-2022) en twee genummerde lijnen (2015 gezinsbijslag naar de
  gemeenschappen, 2017 financieringshervorming). Zie BANDEN en LIJNEN.

Figuur 3 gebruikt gegevens die Statbel persoonlijk bezorgde
(data/restricted/). Ontbreekt dat bestand, dan wordt Figuur 3 overgeslagen.

Uitvoeren:  python code/macro/05_figures.py
"""

import matplotlib

matplotlib.use("Agg")  # geen scherm nodig; enkel bestanden wegschrijven

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.ticker import FuncFormatter, MultipleLocator

from common import DATA_PROCESSED, DATA_RESTRICTED, OUT_FIGURES, OUT_TABLES, zorg_voor_mappen

# ---------------------------------------------------------------------------
# Huisstijl
# ---------------------------------------------------------------------------
KLEUR = {
    "blauw": "#2a78d6", "oranje": "#eb6834", "aqua": "#1baf7a", "geel": "#eda100",
    "magenta": "#e87ba4", "groen": "#008300", "violet": "#4a3aa7",
    "grijs": "#a9a8a2",        # neutraal: 'overige'
    "inkt": "#0b0b0b", "inkt2": "#52514e", "raster": "#e4e3de", "vlak": "#ffffff",
}
ZELF, WERKN = KLEUR["blauw"], KLEUR["oranje"]

BREEDTE = 16 / 2.54  # 16 cm, de tekstbreedte van het rapport, in inch

plt.rcParams.update({
    "font.family": "DejaVu Sans",   # zit in matplotlib zelf: overal identiek
    "font.size": 8.5,
    "axes.titlesize": 9.5,
    "axes.titleweight": "bold",
    "axes.titlelocation": "left",
    "axes.labelsize": 8.5,
    "axes.labelcolor": KLEUR["inkt2"],
    "axes.edgecolor": KLEUR["inkt2"],
    "axes.linewidth": 0.6,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "axes.grid.axis": "y",
    "axes.axisbelow": True,   # rasterlijnen achter de staven
    "grid.color": KLEUR["raster"],
    "grid.linewidth": 0.6,
    "xtick.color": KLEUR["inkt2"],
    "ytick.color": KLEUR["inkt2"],
    "xtick.major.width": 0.6,
    "ytick.major.size": 0,
    "legend.frameon": False,
    "legend.fontsize": 8,
    "lines.linewidth": 1.8,
    "figure.dpi": 100,
    "savefig.dpi": 300,
    "svg.fonttype": "none",   # tekst blijft tekst in de SVG
    "svg.hashsalt": "unizo",  # vaste interne id's in de SVG, ook voor schone Git-diffs
})


def komma(x, decimalen=0):
    """Getal met decimale komma."""
    return f"{x:,.{decimalen}f}".replace(",", "X").replace(".", ",").replace("X", ".")


PROCENT = FuncFormatter(lambda x, _: f"{komma(x * 100)}%")      # fractie -> '45%'
GETAL = FuncFormatter(lambda x, _: komma(x))


def nieuwe_figuur(*args, **kwargs):
    """plt.subplots met 'constrained layout': matplotlib schikt titels, assen en
    legenda zelf, zodat er geen overlap of lege ruimte ontstaat."""
    return plt.subplots(*args, layout="constrained", **kwargs)


def jaren_as(ax, jaren, stap=2):
    """Jaartallen op de x-as, om de `stap` jaar, zonder rasterlijnen."""
    ax.set_xlim(min(jaren) - 0.6, max(jaren) + 0.6)
    ax.set_xticks([j for j in jaren if (j - min(jaren)) % stap == 0])
    ax.tick_params(axis="x", length=3)


def legenda_boven(fig, ax_of_handles, ncol=4, y=None):
    """Eén legenda boven de figuur, gecentreerd (plaats berekent matplotlib zelf)."""
    if isinstance(ax_of_handles, tuple):
        handles, labels = ax_of_handles
    else:
        handles, labels = ax_of_handles.get_legend_handles_labels()
    fig.legend(handles, labels, loc="outside upper center", ncol=ncol,
               handlelength=2.6, columnspacing=1.6)


def bewaar(fig, naam: str, data: pd.DataFrame):
    """PNG + SVG van de figuur en CSV van de geplotte data."""
    for ext in ("png", "svg"):
        # metadata zonder datum: zo verandert het bestand niet bij elke run (schone Git-diffs)
        meta = {"Date": None} if ext == "svg" else {"Software": None}
        fig.savefig(OUT_FIGURES / f"{naam}.{ext}", bbox_inches="tight", facecolor=KLEUR["vlak"], metadata=meta)
    plt.close(fig)
    data.to_csv(OUT_TABLES / "figuurdata" / f"{naam}.csv", float_format="%.6g")
    print(f"figuur: {naam}")


def lijn(ax, x, y, label, kleur, stijl="-"):
    dash = {"-": (None), "--": (0, (5, 2.5)), ":": (0, (1.2, 1.8))}[stijl]
    kw = {"linestyle": dash} if dash else {}
    ax.plot(x, y, label=label, color=kleur, solid_capstyle="round", **kw)


def gestapeld(ax, df: pd.DataFrame, kolommen: dict, breedte=0.78):
    """Gestapelde staven (aandelen), met een smalle witte rand tussen segmenten."""
    onder = pd.Series(0.0, index=df.index)
    for kol, (label, kleur) in kolommen.items():
        ax.bar(df.index, df[kol], bottom=onder, width=breedte, label=label, color=kleur,
               edgecolor=KLEUR["vlak"], linewidth=0.5)
        onder += df[kol]
    ax.set_ylim(0, 1)
    ax.yaxis.set_major_formatter(PROCENT)
    ax.yaxis.set_major_locator(MultipleLocator(0.25))


# ---------------------------------------------------------------------------
# Beleidskader: periodebanden en genummerde breuklijnen
# ---------------------------------------------------------------------------
# Twee soorten markeringen, met een verschillende betekenis:
#
#   BANDEN  periodes waarin beleid gefaseerd ingevoerd werd (tax shift) of een
#           schok liep (corona). Een band zegt "in deze periode gebeurde dit",
#           niet "dit veroorzaakte de beweging".
#   LIJNEN  wijzigingen op één moment in wat de rekeningen bevatten of hoe het
#           stelsel gefinancierd wordt. Het nummer verwijst naar de noot onder
#           de figuur in het rapport (tekst: FIGUURNOTEN, weggeschreven naar
#           output/tables/figuurnoten.md).
#
# Bronnen: Bijlage 1 van het rapport; tax shift: bijdragevoet zelfstandigen
# 22% -> 21,5% (2016) -> 21% (2017) -> 20,5% (2018); werkgeversbijdrage
# 32,4% -> 30% (1 april 2016) -> 25% (2018).
BANDEN = [
    # (begin, eind, label, kleur)
    (2016, 2018, "Tax shift", "#f1efe8"),   # licht warm grijs
    (2020, 2022, "Corona", "#dfe4e8"),      # licht koel grijs
]
LIJNEN = [
    # (jaar, noot)
    (2015, "Zesde staatshervorming: de gezinsbijslag verdwijnt uit de federale rekeningen van de sociale "
           "zekerheid (breuk in de uitgavenreeks; bij zelfstandigen al gedeeltelijk in 2014)."),
    (2017, "Hervorming van de financiering van de sociale zekerheid (wet van 18 april 2017): basisdotatie "
           "en evenwichtsdotatie, verschuiving van toelagen naar alternatieve financiering."),
]


def beleidskader(ax, eerste_jaar, laatste_jaar, bovenste=True, banden=True):
    """Teken banden en genummerde lijnen op één paneel.

    Bandnamen en nummers komen enkel op het `bovenste` paneel. Met
    banden=False komen enkel de nummers (voor staafdiagrammen, waar een band
    achter de staven onzichtbaar zou zijn).
    """
    if banden:
        for b, e, label, kleur in BANDEN:
            if e < eerste_jaar or b > laatste_jaar:
                continue
            ax.axvspan(b - 0.5, e + 0.5, color=kleur, linewidth=0, zorder=0)
            if bovenste:
                # label gecentreerd in de band; een achtergrond in de bandkleur maskeert
                # een eventuele lijn die door het label loopt
                ax.text((b + e) / 2, 0.98, label, transform=ax.get_xaxis_transform(), ha="center", va="top",
                        fontsize=7, color=KLEUR["inkt2"], zorder=1,
                        bbox=dict(boxstyle="square,pad=0.15", fc=kleur, ec="none"))
    for nr, (jaar, _) in enumerate(LIJNEN, start=1):
        if not (eerste_jaar < jaar <= laatste_jaar):
            continue
        if banden:
            ax.axvline(jaar, color=KLEUR["inkt2"], linewidth=0.7, linestyle=(0, (2, 2)), zorder=0.5)
        if bovenste:
            ax.text(jaar, 1.02, str(nr), transform=ax.get_xaxis_transform(), ha="center", va="bottom",
                    fontsize=6.5, color="white", bbox=dict(boxstyle="circle,pad=0.18", fc=KLEUR["inkt2"], ec="none"))


def schrijf_figuurnoten():
    """De tekst bij de genummerde lijnen, klaar om als figuurnoot over te nemen."""
    regels = ["# Figuurnoten bij de genummerde lijnen", "",
              "Gegenereerd door code/macro/05_figures.py (LIJNEN en BANDEN). Van toepassing op Figuur 4, 5, 6, 7, "
              "B4.1, B4.2 en B5.1.", ""]
    regels += [f"({nr}) {jaar}: {tekst}" for nr, (jaar, tekst) in enumerate(LIJNEN, start=1)]
    regels += ["", "Grijze banden: " + "; ".join(f"{label} ({b}-{e})" for b, e, label, _ in BANDEN) + "."]
    (OUT_TABLES / "figuurnoten.md").write_text("\n".join(regels) + "\n", encoding="utf-8")


def eindlabels(ax, labels, min_afstand, symmetrisch=False):
    """Label elke lijn aan haar laatste punt, in de kleur van de lijn.

    labels: lijst van (y_laatste_waarde, x_laatste_jaar, tekst, kleur).
    Labels die dichter dan `min_afstand` (in data-eenheden) bij elkaar liggen,
    worden uit elkaar geschoven, zodat ze nooit overlappen.

    symmetrisch=False: een label dat te dicht bij het vorige ligt, schuift enkel omhoog
    (zo werkte het altijd; de meeste figuren blijven daardoor ongewijzigd).
    symmetrisch=True: labels die botsen, schuiven elk half zoveel uit elkaar, de onderste
    omlaag en de bovenste omhoog. Zo blijft elk label zo dicht mogelijk bij zijn lijn
    (toegevoegd voor Figuur 5, opmerking Wim 22 september 2026).
    """
    labels = sorted(labels, key=lambda t: t[0])
    regels = [t[2].count("\n") + 1 for t in labels]
    # nodige afstand tussen label i-1 en i: labels van twee regels hebben meer plaats nodig
    nodig = [min_afstand * (regels[i - 1] + regels[i]) / 2 for i in range(1, len(labels))]
    posities = [t[0] for t in labels]
    if not symmetrisch:
        for i in range(1, len(posities)):
            if posities[i] - posities[i - 1] < nodig[i - 1]:
                posities[i] = posities[i - 1] + nodig[i - 1]
    else:
        # Herhaaldelijk elk botsend paar evenveel uit elkaar duwen tot niets meer botst.
        for _ in range(500):
            verschoven = False
            for i in range(1, len(posities)):
                tekort = nodig[i - 1] - (posities[i] - posities[i - 1])
                if tekort > 1e-6:
                    posities[i - 1] -= tekort / 2
                    posities[i] += tekort / 2
                    verschoven = True
            if not verschoven:
                break
    for (y0, x, tekst, kleur), y in zip(labels, posities):
        ax.annotate(tekst, xy=(x, y0), xytext=(x + 0.6, y), textcoords="data", va="center", ha="left",
                    fontsize=7.8, color=kleur, fontweight="bold", annotation_clip=False)


def ruimte_rechts(ax, laatste_jaar, extra=4.5):
    """Laat rechts van de laatste waarneming ruimte voor de eindlabels."""
    lo, _ = ax.get_xlim()
    ax.set_xlim(lo, laatste_jaar + extra)
    # de x-as zelf stopt bij de laatste waarneming
    ax.spines["bottom"].set_bounds(lo, laatste_jaar + 0.6)


# ---------------------------------------------------------------------------
# Data inlezen
# ---------------------------------------------------------------------------
def lees(naam, **kw):
    return pd.read_csv(DATA_PROCESSED / f"{naam}.csv", **kw)


def bs_wide(definitie: str) -> pd.DataFrame:
    bs = lees("beroepssolidariteit")
    g = bs[(bs["deflator"] == "cpi") & (bs["definitie"] == definitie)]
    return g.pivot(index="jaar", columns="reeks", values="waarde")


# ===========================================================================
# Figuur 1: zelfstandigen en werknemers in de werkende bevolking
# ===========================================================================
def figuur1():
    p = lees("populaties", index_col="jaar")
    j = p.index
    fig, (a, b) = nieuwe_figuur(2, 1, figsize=(BREEDTE, 5.6), sharex=True)

    lijn(a, j, p["aandeel_zelfstandigen_Z1"], "Zelfstandigen (Z1)", ZELF)
    a.set_ylim(0, 0.25)
    a.yaxis.set_major_formatter(PROCENT)
    a.set_ylabel("Aandeel in werkende bevolking")
    a.set_title("(A) Aandeel zelfstandigen in de werkende bevolking")

    lijn(b, j, p["index_Z1"], "Zelfstandigen (Z1)", ZELF)
    lijn(b, j, p["index_W1"], "Werknemers (W1)", WERKN, "--")
    b.axhline(100, color=KLEUR["inkt2"], linewidth=0.6)
    b.set_ylim(80, 140)
    b.yaxis.set_major_formatter(GETAL)
    b.set_ylabel("Index (2003 = 100)")
    b.set_title("(B) Aantal")
    jaren_as(b, j)
    legenda_boven(fig, b, ncol=2, y=1.01)
    bewaar(fig, "fig01_werkende_bevolking",
           p[["Z1", "W1", "aandeel_zelfstandigen_Z1", "index_Z1", "index_W1"]])


# ===========================================================================
# Figuur 2: samenstelling zelfstandigenpopulatie (RSVZ)
# ===========================================================================
def figuur2():
    s = lees("samenstelling", index_col="jaar").loc[2003:2023]
    j = s.index
    fig, (a, b, c) = nieuwe_figuur(3, 1, figsize=(BREEDTE, 7.9), gridspec_kw={"height_ratios": [1, 1, 1.15]})
    lijn(a, j, s["index_vennootschappen"], "Vennootschappen", KLEUR["violet"])
    a.axhline(100, color=KLEUR["inkt2"], linewidth=0.6)
    a.set_ylim(0, 250)
    a.set_ylabel("Index (2003 = 100)")
    a.set_title("(A) Ondernemingsvorm: aantal vennootschappen")
    jaren_as(a, j)

    aard = {"aandeel_hoofdberoep": ("Hoofdberoep", KLEUR["blauw"]),
            "aandeel_bijberoep": ("Bijberoep", KLEUR["oranje"]),
            "aandeel_actief_na_pensioen": ("Actief na pensioen", KLEUR["aqua"])}
    gestapeld(b, s, aard)
    b.set_ylabel("Aandeel")
    b.set_title("(B) Aard van de bezigheid")
    b.legend(loc="upper center", bbox_to_anchor=(0.5, -0.14), ncol=3)
    jaren_as(b, j)

    sector = {"aandeel_landbouw_visserij": ("Landbouw en visserij", KLEUR["blauw"]),
              "aandeel_nijverheid": ("Nijverheid", KLEUR["oranje"]),
              "aandeel_handel": ("Handel", KLEUR["aqua"]),
              "aandeel_vrije_beroepen": ("Vrije beroepen", KLEUR["geel"]),
              "aandeel_diensten": ("Diensten", KLEUR["magenta"]),
              "aandeel_diversen": ("Diversen", KLEUR["groen"])}
    gestapeld(c, s, sector)
    c.set_ylabel("Aandeel")
    c.set_title("(C) Sector")
    c.legend(loc="upper center", bbox_to_anchor=(0.5, -0.14), ncol=3)
    jaren_as(c, j)
    bewaar(fig, "fig02_samenstelling_zelfstandigen",
           s[["vennootschappen", "index_vennootschappen", *aard, *sector]])


# ===========================================================================
# Figuur 3: inkomensverdeling (Statbel, niet publiek)
# ===========================================================================
def figuur3():
    # wijziging: nieuw | 23 september 2026, publicatie op GitHub: het histogram van Statbel is niet
    # publiek deelbaar, maar de figuur zelf en de aandelen die ze toont wel. Staat het bronbestand er
    # niet, dan tekenen we de figuur uit het meegeleverde figuurdatabestand. Zo blijft Figuur 3
    # reproduceerbaar vanuit de publieke repository. Zie DATA.md.
    pad = DATA_RESTRICTED / "statbel_adi_histogram_2023.xlsx"
    terugval = OUT_TABLES / "figuurdata" / "fig03_inkomensverdeling.csv"
    if pad.exists():
        delen = []
        for blad, groep in (("EMPL", "werknemers"), ("SELF", "zelfstandigen")):
            d = pd.read_excel(pad, sheet_name=blad)
            # Enkel de rijen van het histogram zelf; onderaan staan totalen en percentielen
            d = d[d["_VAR_"] == "MS_EQ_ADI_STATBEL"][["_MINPT_", "_OBSPCT_"]]
            d.columns = ["ondergrens_eur", groep]
            delen.append(d.set_index("ondergrens_eur").astype(float))
        h = pd.concat(delen, axis=1).fillna(0)
        h.index = h.index.astype(int)
    elif terugval.exists():
        print("figuur: fig03 uit figuurdata (bronhistogram niet aanwezig)")
        h = pd.read_csv(terugval).set_index("ondergrens_eur").astype(float)
        h.index = h.index.astype(int)
    else:
        print("figuur: fig03 OVERGESLAGEN (bronhistogram noch figuurdata aanwezig)")
        return

    fig, ax = nieuwe_figuur(figsize=(BREEDTE, 3.4))
    x = h.index / 1000  # in duizend euro
    w = 0.42
    ax.bar(x - w / 2, h["werknemers"], width=w, color=WERKN, label="Werknemers", linewidth=0)
    ax.bar(x + w / 2, h["zelfstandigen"], width=w, color=ZELF, label="Zelfstandigen", linewidth=0)
    ax.set_xlabel("Administratief beschikbaar equivalent jaarinkomen (duizend euro; laatste klasse = 84 of meer)")
    ax.set_ylabel("Aandeel van de groep")
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{komma(v, 1)}%"))
    ax.set_xlim(x.min() - 1, x.max() + 1)
    ax.set_xticks(range(10, 90, 10))
    ax.tick_params(axis="x", length=3)
    legenda_boven(fig, ax, ncol=2, y=1.04)
    bewaar(fig, "fig03_inkomensverdeling", h)


# ===========================================================================
# Figuur 4 / B4.1: beroepssolidariteit
# ===========================================================================
def figuur_beroepssolidariteit(def_z: str, def_w: str, naam: str):
    """Drie panelen boven elkaar: bijdragen, uitgaven, ratio.

    Zelfstandigen en werknemers staan telkens in hetzelfde paneel, zodat het
    verschil tussen de stelsels rechtstreeks te lezen is.
    """
    z, w = bs_wide(def_z), bs_wide(def_w)
    j = z.index
    fig, assen = nieuwe_figuur(3, 1, figsize=(BREEDTE, 7.6), sharex=True)
    panelen = [
        ("index_bijdragen_pc", "(A) Reële bijdragen per capita", (60, 180), GETAL, "Index (2003 = 100)", 6),
        ("index_uitgaven_pc", "(B) Reële uitgaven per capita", (60, 180), GETAL, "Index (2003 = 100)", 6),
        ("ratio_bijdragen_uitgaven", "(C) Beroepssolidariteit: bijdragen / uitgaven", (0, 1), PROCENT,
         "Bijdragen / uitgaven", 0.05),
    ]
    for i, (ax, (kol, titel, lim, fmt, ylabel, afstand)) in enumerate(zip(assen, panelen)):
        beleidskader(ax, j.min(), j.max(), bovenste=(i == 0))
        lijn(ax, j, z[kol], f"Zelfstandigen ({def_z})", ZELF)
        lijn(ax, j, w[kol], f"Werknemers ({def_w})", WERKN, "--")
        if kol != "ratio_bijdragen_uitgaven":
            ax.axhline(100, color=KLEUR["inkt2"], linewidth=0.6)
        ax.set_ylim(*lim)
        ax.yaxis.set_major_formatter(fmt)
        if kol == "ratio_bijdragen_uitgaven":
            ax.yaxis.set_major_locator(MultipleLocator(0.25))
        ax.set_ylabel(ylabel)
        ax.set_title(titel, pad=14 if i == 0 else 6)
        jaren_as(ax, j, stap=4)
        ruimte_rechts(ax, j.max())
        eindlabels(ax, [(z[kol].iloc[-1], j.max(), f"Zelfstandigen ({def_z})", ZELF),
                        (w[kol].iloc[-1], j.max(), f"Werknemers ({def_w})", WERKN)], afstand * 2)
    data = pd.concat({def_z: z, def_w: w}, axis=1)[
        [(d, r) for d in (def_z, def_w) for r in ("bijdragen_pc_reeel", "uitgaven_pc_reeel", "index_bijdragen_pc",
                                                  "index_uitgaven_pc", "ratio_bijdragen_uitgaven")]]
    data.columns = [f"{d}_{r}" for d, r in data.columns]
    bewaar(fig, naam, data)


# ===========================================================================
# Figuur 5 / B4.2: vennootschappen en zelfstandigen
# ===========================================================================
def figuur_vennootschappen(definitie: str, naam: str):
    v = lees("vennootschappen", index_col="jaar")
    j = v.index
    fig, ax = nieuwe_figuur(figsize=(BREEDTE, 3.9))
    beleidskader(ax, j.min(), j.max())
    reeksen = [
        ("index_aantal_vennootschappen", "Aantal vennootschappen", KLEUR["violet"], "-"),
        ("index_vb_per_vennootschap", "Vennootschapsbijdrage\nper vennootschap", KLEUR["violet"], "--"),
        (f"index_populatie_{definitie}", f"Aantal zelfstandigen ({definitie})", ZELF, "-"),
        (f"index_gewone_bijdragen_pc_{definitie}", "Gewone bijdragen\nper zelfstandige", ZELF, "--"),
    ]
    for kol, label, kleur, stijl in reeksen:
        lijn(ax, j, v[kol], label, kleur, stijl)
    ax.axhline(100, color=KLEUR["inkt2"], linewidth=0.6)
    ax.set_ylim(0, 250)
    ax.set_ylabel("Index (2003 = 100)\nbijdragen reëel")
    jaren_as(ax, j)
    ruimte_rechts(ax, j.max(), extra=6)
    # symmetrisch en iets krapper: zo staat het label van het aantal zelfstandigen aan zijn lijn
    # en zakt dat van de gewone bijdragen (opmerking Wim, 22 september 2026)
    eindlabels(ax, [(v[k].iloc[-1], j.max(), lab, kl) for k, lab, kl, _ in reeksen], min_afstand=13,
               symmetrisch=True)
    bewaar(fig, naam, v[["index_aantal_vennootschappen", "index_vb_per_vennootschap", f"index_populatie_{definitie}",
                         f"index_gewone_bijdragen_pc_{definitie}", "vb_per_vennootschap_reeel_eur",
                         f"gewone_bijdragen_pc_reeel_{definitie}"]])


# ===========================================================================
# Figuur 6: nationale solidariteit
# ===========================================================================
def figuur6():
    n = lees("nationale_solidariteit", index_col="jaar")
    j = n.index
    fig, (a, b) = nieuwe_figuur(2, 1, figsize=(BREEDTE, 5.8), sharex=True)
    beleidskader(a, j.min(), j.max(), bovenste=True)
    beleidskader(b, j.min(), j.max(), bovenste=False)

    lijn(a, j, n["z_nationale_solidariteit"], "Zelfstandigen", ZELF)
    lijn(a, j, n["w_nationale_solidariteit"], "Werknemers", WERKN, "--")
    a.set_ylim(0, 0.7)
    a.yaxis.set_major_formatter(PROCENT)
    a.set_ylabel("Aandeel in totale\nlopende ontvangsten")
    a.set_title("(A) Aandeel nationale solidariteit", pad=14)

    lijn(b, j, n["z_index_nationale_solidariteit"], "Zelfstandigen", ZELF)
    lijn(b, j, n["w_index_nationale_solidariteit"], "Werknemers", WERKN, "--")
    b.axhline(100, color=KLEUR["inkt2"], linewidth=0.6)
    b.set_ylim(0, 200)
    b.yaxis.set_major_formatter(GETAL)
    b.set_ylabel("Index (2000 = 100)")
    b.set_title("(B) Evolutie van dat aandeel")
    for ax, kz, kw, afstand in ((a, "z_nationale_solidariteit", "w_nationale_solidariteit", 0.06),
                                (b, "z_index_nationale_solidariteit", "w_index_nationale_solidariteit", 17)):
        jaren_as(ax, j, stap=4)
        ruimte_rechts(ax, j.max())
        eindlabels(ax, [(n[kz].iloc[-1], j.max(), "Zelfstandigen", ZELF),
                        (n[kw].iloc[-1], j.max(), "Werknemers", WERKN)], afstand)
    bewaar(fig, "fig06_nationale_solidariteit",
           n[["z_nationale_solidariteit", "w_nationale_solidariteit", "z_index_nationale_solidariteit",
              "w_index_nationale_solidariteit"]])


# ===========================================================================
# Figuur 7: inkomstenstructuur
# ===========================================================================
def figuur7():
    n = lees("nationale_solidariteit", index_col="jaar")
    fig, (a, b) = nieuwe_figuur(2, 1, figsize=(BREEDTE, 6.2), sharex=True)
    for ax, p, titel in ((a, "z", "(A) Zelfstandigen"), (b, "w", "(B) Werknemers")):
        kolommen = {f"{p}_aandeel_bijdragen": ("Bijdragen", KLEUR["blauw"]),
                    f"{p}_aandeel_toelagen": ("Toelagen van publieke overheden", KLEUR["oranje"]),
                    f"{p}_aandeel_alternatieve": ("Alternatieve financiering", KLEUR["aqua"]),
                    f"{p}_aandeel_overige": ("Overige financiering", KLEUR["grijs"])}
        gestapeld(ax, n, kolommen)
        beleidskader(ax, n.index.min(), n.index.max(), bovenste=(p == "z"), banden=False)
        ax.set_ylabel("Aandeel in totale\nlopende ontvangsten")
        ax.set_title(titel, pad=14 if p == "z" else 6)
    jaren_as(b, n.index, stap=4)
    legenda_boven(fig, a, ncol=2, y=1.04)
    bewaar(fig, "fig07_inkomstenstructuur", n[[c for c in n.columns if "_aandeel_" in c]])


# ===========================================================================
# Figuur B5.1: werknemers- en werkgeversbijdragen
# ===========================================================================
def figuurB51():
    o = lees("werknemers_opsplitsing", index_col="jaar")
    j = o.index
    fig, assen = nieuwe_figuur(2, 1, figsize=(BREEDTE, 5.6), sharex=True)
    for i, (ax, d) in enumerate(zip(assen, ("W1", "W2"))):
        beleidskader(ax, j.min(), j.max(), bovenste=(i == 0))
        reeksen = [(f"index_populatie_{d}", "Aantal werknemers", KLEUR["oranje"], "-"),
                   (f"index_werknemersbijdragen_pc_{d}", "Werknemersbijdragen\nper capita", KLEUR["oranje"], "--"),
                   (f"index_werkgeversbijdragen_pc_{d}", "Werkgeversbijdragen\nper capita", KLEUR["violet"], ":")]
        for kol, label, kleur, stijl in reeksen:
            lijn(ax, j, o[kol], label, kleur, stijl)
        ax.axhline(100, color=KLEUR["inkt2"], linewidth=0.6)
        ax.set_ylim(80, 130)
        ax.set_ylabel("Index (2003 = 100)\nbijdragen reëel")
        ax.set_title(f"({'A' if d == 'W1' else 'B'}) Populatiedefinitie {d}", pad=14 if i == 0 else 6)
        jaren_as(ax, j, stap=4)
        ruimte_rechts(ax, j.max(), extra=6)
        eindlabels(ax, [(o[k].iloc[-1], j.max(), lab, kl) for k, lab, kl, _ in reeksen], min_afstand=4.5)
    bewaar(fig, "figB5-1_werknemers_werkgeversbijdragen",
           o[[c for c in o.columns if c.startswith("index_")]])


def main():
    zorg_voor_mappen()
    (OUT_TABLES / "figuurdata").mkdir(parents=True, exist_ok=True)
    figuur1()
    figuur2()
    figuur3()
    figuur_beroepssolidariteit("Z1", "W1", "fig04_beroepssolidariteit_Z1_W1")
    figuur_vennootschappen("Z1", "fig05_vennootschappen_Z1")
    figuur6()
    figuur7()
    figuur_beroepssolidariteit("Z2", "W2", "figB4-1_beroepssolidariteit_Z2_W2")
    figuur_vennootschappen("Z2", "figB4-2_vennootschappen_Z2")
    figuurB51()
    schrijf_figuurnoten()


if __name__ == "__main__":
    main()
