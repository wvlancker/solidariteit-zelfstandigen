"""
Stap 7: alle cijfers die in de tekst van §6.1 staan -> tekst invullen

Waarom?
-------
Een cijfer dat met de hand in een tekst wordt overgetypt, kan afwijken van de
berekening, en wordt niet mee aangepast als de data wijzigen. Daarom staan de
cijfers in de tekst als plaatshouders, bv. {{z1_ratio_2003}}, en vult dit
script ze in:

    report/templates/06-1_macro.md      tekst met plaatshouders (hierin schrijf je)
    report/sections/06-1_macro.md       ingevulde tekst (GEGENEREERD, niet bewerken)
    output/tables/tekstcijfers.csv      elk cijfer: sleutel, exacte waarde, weergave, omschrijving

Een onbekende plaatshouder in een template geeft een foutmelding, zodat er
nooit een lege of verkeerde waarde in de tekst belandt.

Afspraken over de weergave (leesnota D6)
----------------------------------------
- Bedragen per capita en indexen: RELATIEVE verandering in % ("+21%").
- Ratio's en aandelen (beroepssolidariteit, nationale solidariteit, aandelen
  financieringsbronnen): niveaus in % ("57%") en veranderingen in
  PROCENTPUNT ("-7,3 procentpunt"). Zo meet een verandering van 20 naar 30%
  niet als "+50%".

Uitvoeren:  python code/macro/07_tekstcijfers.py
"""

import re
import sys

import pandas as pd

from common import DATA_PROCESSED, DATA_RAW, OUT_TABLES, PRIJSJAAR, ROOT, zorg_voor_mappen

TEMPLATES = ROOT / "report" / "templates"
SECTIES = ROOT / "report" / "sections"


# ---------------------------------------------------------------------------
# Opmaak
# ---------------------------------------------------------------------------
def nl(x: float, dec: int = 0) -> str:
    """Getal in Nederlandse notatie: 1.234,5"""
    s = f"{abs(x):,.{dec}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return ("-" if x < 0 and float(s.replace(".", "").replace(",", ".")) != 0 else "") + s


def teken(x: float, dec: int = 0) -> str:
    """Met expliciet plus- of minteken: +21, -3"""
    s = nl(x, dec)
    if float(s.lstrip("-").replace(".", "").replace(",", ".")) == 0:
        return s.lstrip("-")          # afgerond nul: geen teken ("0,0")
    return s if s.startswith("-") else "+" + s


class Cijfers:
    """Verzamelt cijfers met hun weergave en omschrijving."""

    def __init__(self):
        self.rijen = {}

    def zet(self, sleutel, waarde, weergave, omschrijving):
        if sleutel in self.rijen:
            raise KeyError(f"dubbele sleutel: {sleutel}")
        self.rijen[sleutel] = (float(waarde), weergave, omschrijving)

    # --- hulpjes voor de vaste soorten cijfers ---
    def pct(self, sleutel, fractie, omschr, dec=0):          # niveau van ratio/aandeel: 57%
        self.zet(sleutel, fractie * 100, f"{nl(fractie * 100, dec)}%", omschr)

    def pp(self, sleutel, fractie_verschil, omschr, dec=1):  # verschil in procentpunt: -7,3 procentpunt
        self.zet(sleutel, fractie_verschil * 100, f"{teken(fractie_verschil * 100, dec)} procentpunt", omschr)

    def rel(self, sleutel, reeks, b, e, omschr, dec=0):      # relatieve verandering: +21%
        v = (reeks[e] / reeks[b] - 1) * 100
        self.zet(sleutel, v, f"{teken(v, dec)}%", omschr)

    def eur(self, sleutel, bedrag, omschr, dec=0):
        self.zet(sleutel, bedrag, f"€{nl(bedrag, dec)}", omschr)

    def mld(self, sleutel, duizend_euro, omschr, dec=1):
        v = duizend_euro / 1e6
        self.zet(sleutel, v, f"€{nl(v, dec)} miljard", omschr)

    def getal(self, sleutel, waarde, omschr, dec=0):
        self.zet(sleutel, waarde, nl(waarde, dec), omschr)

    # <!-- wijziging: publicatie | sleutel die geen getal is, voor het DOI -->
    def tekst(self, sleutel, weergave, omschr):
        """Een sleutel waarvan de waarde geen getal is, zoals het DOI.

        De filters |daling en |stijging hebben hier geen betekenis; de numerieke waarde
        blijft daarom leeg (NaN), zodat die filters een fout geven als iemand ze toch
        op zo'n sleutel toepast.
        """
        if sleutel in self.rijen:
            raise KeyError(f"dubbele sleutel: {sleutel}")
        self.rijen[sleutel] = (float("nan"), weergave, omschr)


# <!-- wijziging: publicatie | het DOI komt uit CITATION.cff, de enige plaats waar het staat -->
def doi_uit_citation():
    """Het DOI van het Zenodo-archief, gelezen uit CITATION.cff.

    Zolang er nog geen release op Zenodo staat, bestaat het DOI niet en staat de regel
    `doi:` in CITATION.cff uitgecommentarieerd. Dan geven we een duidelijk zichtbare
    plaatshouder terug, zodat niemand denkt dat de link werkt.
    """
    pad = ROOT / "CITATION.cff"
    if pad.exists():
        for regel in pad.read_text(encoding="utf-8").splitlines():
            kaal = regel.strip()
            if kaal.startswith("doi:"):                      # een uitgecommentarieerde regel
                return kaal.split(":", 1)[1].strip().strip('"\'')   # begint met '#' en valt hier af
    return "VUL-IN-DOI"


# ---------------------------------------------------------------------------
# Microdeel
# ---------------------------------------------------------------------------
# De indicatoren van het microdeel hebben 34 inkomensposities per reeks. Alle waarden op
# voorhand als sleutel registreren zou duizenden rijen in tekstcijfers.csv opleveren. Daarom
# worden de sleutels van de vorm
#
#     mi_<indicator>_<gezin>_<risico>_<type>_<maand>_<wat>
#
# aangemaakt voor elke plaatshouder die in een template voorkomt. De codes:
#   indicator  br = bijdrage/draagkracht, eq = equivalentiegraad, vv = vervangingsgraad, gg = garantiegraad
#   gezin      a = alleenstaande, k = koppel, kl / kg = koppel met partner met laag / gemiddeld loon, x = n.v.t.
#   risico     z = primaire arbeidsongeschiktheid, w = werkloosheid/overbruggingsrecht, p = pensioen, x = n.v.t.
#   type       wn, zs (zelfstandige, forfaitaire uitkering), ze (eenmanszaak), zv100vaa, zv100, zv75, zv50, zv00
#   maand      m2, m36, m712, m13, m46 (uitkeringsmaand werknemer), x = n.v.t.
#   wat        gem           gemiddelde over de 34 posities (in %)
#              vc            variatiecoëfficiënt (2 decimalen)
#              p<positie>    waarde op die positie, bv. p15000 (in %)
#              eerste_ge100  eerste positie met een waarde van minstens 100% (in euro)
#              start_tot     laatste positie (van onderaan) met dezelfde waarde als op €1.550 (in euro)
# Voorbeeld: {{mi_eq_a_z_wn_m2_gem}} = gemiddelde equivalentiegraad werknemer, ziekte, maand 2.
# Alle andere micro-sleutels (weging, zones, drempels) worden hieronder expliciet gemaakt.
MI_CODES = {
    "ind": {"br": "bijdrage_ratio", "eq": "equivalentiegraad", "vv": "vervangingsgraad", "gg": "garantiegraad"},
    "gezin": {"a": "alleen", "k": "koppel", "kl": "koppel_laag", "kg": "koppel_gem", "x": "-"},
    "risico": {"z": "ziekte", "w": "werkloosheid", "p": "pensioen", "x": "-"},
    "type": {t: t.upper() for t in ("wn", "zs", "ze", "zv100vaa", "zv100", "zv75", "zv50", "zv00")},
    "maand": {"m2": "2", "m36": "3-6", "m712": "7-12", "m13": "1-3", "m46": "4-6", "x": "-"},
}
MI_PATROON = re.compile(r"\{\{\s*(mi_(br|eq|vv|gg)_(a|k|kl|kg|x)_(z|w|p|x)_(wn|zs|ze|zv100vaa|zv100|zv75|zv50|zv00)_"
                        r"(m2|m36|m712|m13|m46|x)_(gem|vc|p\d+|eerste_ge100|start_tot))\s*(?:\|[a-z]+\s*)?\}\}")


def micro_cijfers(c):
    """Registreer de cijfers van het microdeel (zie de uitleg hierboven)."""
    ind = pd.read_csv(DATA_PROCESSED / "micro_indicatoren.csv", dtype={"maand": str})
    sv = pd.read_csv(DATA_PROCESSED / "micro_samenvatting.csv", dtype={"maand": str})

    def reeks(i, g, r, t, m):
        s = ind[(ind.indicator == i) & (ind.gezin == g) & (ind.risico == r) & (ind.type == t) & (ind.maand == m)]
        if len(s) != 34:
            raise KeyError(f"geen reeks {i} {g} {r} {t} {m} in micro_indicatoren.csv")
        return s.sort_values("positie").set_index("positie")["waarde"]

    # (a) sleutels die in de templates gebruikt worden
    gevraagd = set()
    for tpl in TEMPLATES.glob("*.md"):
        gevraagd |= {m.groups() for m in MI_PATROON.finditer(tpl.read_text(encoding="utf-8"))}
    for sleutel, i, g, r, t, m, wat in sorted(gevraagd):
        args = (MI_CODES["ind"][i], MI_CODES["gezin"][g], MI_CODES["risico"][r], MI_CODES["type"][t], MI_CODES["maand"][m])
        s = reeks(*args)
        omschr = f"{args[0]}, {args[1]}, {args[2]}, {args[3]}, maand {args[4]}"
        if wat == "gem":
            c.pct(sleutel, s.mean(), f"{omschr}: gemiddelde over de posities")
        elif wat == "vc":
            c.getal(sleutel, s.std(ddof=0) / s.mean(), f"{omschr}: variatiecoëfficiënt", 2)
        elif wat.startswith("p"):
            c.pct(sleutel, s.loc[int(wat[1:])], f"{omschr}: waarde bij €{wat[1:]}")
        elif wat == "eerste_ge100":
            boven = s[s >= 1 - 1e-9]
            if boven.empty:
                raise ValueError(f"{sleutel}: nergens 100% of meer")
            c.eur(sleutel, boven.index[0], f"{omschr}: eerste positie met minstens 100%")
        elif wat == "start_tot":
            gelijk = (s - s.iloc[0]).abs() < 1e-6
            laatste = gelijk.index[gelijk.to_numpy().cumprod().astype(bool)][-1]
            c.eur(sleutel, laatste, f"{omschr}: laatste positie met dezelfde waarde als op €1.550")

    # (b) samenvattende tabellen: alle gemiddelden en variatiecoëfficiënten die in Tabel 9, 10, B7.1
    #     en B7.2 staan, zitten al in (a) via {{mi_..._gem}} en {{mi_..._vc}} in de templates.

    # (c) weging van Tabel 8 (m01: BE-SILC 2024, variant A, typegevallen; m02: Statbel ADI 2023, hoofdscenario)
    silc = pd.read_csv(DATA_PROCESSED / "micro_kakwani_besilc2024.csv")
    adi = pd.read_csv(DATA_PROCESSED / "micro_kakwani_adi2023.csv")
    for t in ("WN", "ZE", "ZV100VAA", "ZV100", "ZV75", "ZV50", "ZV00"):
        rap = silc[(silc.groep == "rapport") & (silc.type == t)].iloc[0]
        a = silc[(silc.variant == "A") & (silc.groep == ("wn_typ" if t == "WN" else "zs_typ")) & (silc.type == t)].iloc[0]
        h = adi[(adi.scenario == "hoofd") & (adi.type == t)].iloc[0]
        for weging, rij in (("gelijk", rap), ("silc", a), ("adi", h)):
            k = f"mi_kak_{weging}_{t.lower()}"
            c.getal(k, rij["kakwani"], f"Kakwani-index {t}, weging {weging}", 2)
            c.pct(f"mi_ratio_{weging}_{t.lower()}", rij["ratio"], f"gemiddelde bijdrage/draagkracht {t}, weging {weging}")
    c.getal("mi_gini_rooster", silc[silc.groep == "rapport"]["gini"].iloc[0], "Gini-coëfficiënt van het rooster (gelijke gewichten)", 2)
    n_zs = silc[(silc.variant == "A") & (silc.groep == "zs_typ")]["n_obs"].iloc[0]
    c.getal("mi_silc_n_zelfstandigen", n_zs, "BE-SILC 2024 variant A: aantal zelfstandigen (typegevallen)")

    # (d) aandeel met een lagere levensstandaard dan €6.250 (posities onder €6.250), leesnota K8
    # <!-- wijziging: publicatie | aandeel uit de gewichten w, zodat de publieke afgeleide volstaat -->
    # De Stata-uitvoer heeft een kolom 'aandeel'; die is per variant en groep gewoon w/som(w).
    # We rekenen ze hier uit de gewichten, zodat de stap ook draait met het publieke bestand
    # zonder celaantallen (verschil: 2e-16).
    sys.path.insert(0, str(ROOT / "code" / "micro"))
    from common_micro import lees_silc_gewichten
    g_silc = lees_silc_gewichten()
    zs = g_silc[(g_silc.variant == "A") & (g_silc.groep == "zs_typ")]
    c.pct("mi_silc_zs_onder_6250", zs[zs.pos < 6250]["w"].sum() / zs["w"].sum(), "BE-SILC A: aandeel zelfstandigen op posities onder €6.250")
    g_adi = pd.read_csv(DATA_PROCESSED / "micro_gewichten_adi2023.csv")
    c.pct("mi_adi_zs_onder_6250", g_adi.loc[g_adi.pos < 6250, "w_zelfstandigen"].sum(), "ADI 2023: aandeel zelfstandigen op posities onder €6.250")

    # (e) zones van de bijdrageschaal van de eenmanszaak (m03), leesnota K2
    pos = pd.read_csv(DATA_PROCESSED / "micro_schaal_posities.csv")
    for zone, k in (("onder tussengrens", "onder"), ("degressieve schijf", "schijf"), ("boven plafond", "plafond")):
        z = pos[pos.zone == zone]
        c.eur(f"mi_zone_{k}_van", z.dpi.min(), f"zone {zone}: eerste positie")
        c.eur(f"mi_zone_{k}_tot", z.dpi.max(), f"zone {zone}: laatste positie")
    c.eur("mi_nbi_laagste_jaar", pos.nbi_maand.min() * 12, "laagste netto belastbaar inkomen eenmanszaak op het rooster, per jaar")

    # (f) snijpunten tussen twee reeksen
    def laatste_boven(a, b):
        """Laatste positie van het aaneengesloten stuk vanaf €1.550 (of vanaf het eerste snijpunt) waar a > b."""
        verschil = a - b
        boven = verschil > 0
        return boven.index[boven.to_numpy().cumprod().astype(bool)][-1]

    br = {t: reeks("bijdrage_ratio", "-", "-", t, "-") for t in ("WN", "ZE", "ZV100", "ZV75", "ZV50", "ZV00")}
    c.eur("mi_br_ze_boven_wn_tot", laatste_boven(br["ZE"], br["WN"]), "laatste positie waar eenmanszaak meer betaalt dan werknemer")
    c.eur("mi_br_zv100_boven_wn_tot", laatste_boven(br["ZV100"], br["WN"]), "idem, vennootschap 100% loon")
    for t in ("ZV75", "ZV50", "ZV00"):
        onder = br[t][(br[t] < br["WN"]) & (br[t].index >= 2250)]
        c.eur(f"mi_br_{t.lower()}_onder_wn_vanaf", onder.index[0], f"eerste positie (vanaf €2.250) waar {t} minder betaalt dan werknemer")
    eqp = {t: reeks("equivalentiegraad", "-", "pensioen", t, "-") for t in ("WN", "ZE", "ZV75")}
    c.eur("mi_eq_p_ze_boven_wn_tot", laatste_boven(eqp["ZE"], eqp["WN"]), "pensioen: laatste positie met hogere equivalentiegraad eenmanszaak dan werknemer")
    c.eur("mi_eq_p_zv75_boven_wn_tot", laatste_boven(eqp["ZV75"], eqp["WN"]), "pensioen: idem, vennootschap 75% loon")
    vz = reeks("vervangingsgraad", "alleen", "ziekte", "ZS", "-")
    vw = reeks("vervangingsgraad", "alleen", "ziekte", "WN", "7-12")
    c.eur("mi_vv_z_zs_boven_wn_tot", laatste_boven(vz + 1e-9, vw), "ziekte: laatste positie met minstens even hoge vervangingsgraad zelfstandige als werknemer (maand 7-12)")
    ggp = {t: reeks("garantiegraad", "-", "pensioen", t, "-") for t in ("WN", "ZE")}
    c.eur("mi_gg_p_wn_boven_ze_vanaf", ggp["WN"][ggp["WN"] > ggp["ZE"] + 1e-9].index[0], "pensioen: eerste positie met hoger werknemerspensioen")
    c.eur("mi_gg_p_wn_max_vanaf", ggp["WN"][ggp["WN"] >= ggp["WN"].max() - 0.01].index[0], "pensioen werknemer: eerste positie op (ongeveer) het maximum")
    # onderste posities waar een uitkering onder het referentiebudget ligt
    for sleutel, args in (("mi_gg_z_wn_m2_onder100_tot", ("alleen", "ziekte", "WN", "2")),
                          ("mi_gg_z_wn_m36_onder100_tot", ("alleen", "ziekte", "WN", "3-6")),
                          ("mi_gg_w_wn_m13_onder100_tot", ("alleen", "werkloosheid", "WN", "1-3"))):
        s = reeks("garantiegraad", *args)
        c.eur(sleutel, s[s < 1].index.max(), f"garantiegraad {args}: hoogste positie onder 100%")

    # (g) referentiebudgetten en partnerloon (invoer m05)
    inv = pd.read_csv(DATA_RAW / "micro_werkboek_invoer.csv")
    for reeks_, gezin, k, omschr in (("budget", "alleen", "mi_budget_alleen", "referentiebudget alleenstaande"),
                                     ("budget", "koppel", "mi_budget_koppel", "referentiebudget koppel met 2 kinderen"),
                                     ("partnerloon", "koppel_laag", "mi_partnerloon_laag", "netto loon partner, laag loon"),
                                     ("partnerloon", "koppel_gem", "mi_partnerloon_gem", "netto loon partner, gemiddeld loon")):
        c.eur(k, inv[(inv.reeks == reeks_) & (inv.gezin == gezin)]["waarde"].iloc[0], omschr, 2)

    # (h) pensioenparameters uit het correctieblad (m05, leesnota J1): minimum, loongrens en het
    #     maximale bruto pensioen (60% van de loongrens per maand). Zo staan ze nergens overgetypt.
    # eerste positie waar de equivalentiegraad bij pensioen niet meer verandert: zowel de bijdrage
    # als het pensioen loopt dan tegen zijn plafond, zodat de verhouding constant wordt.
    for t, k in (("ZE", "ze"), ("ZV100", "zv100")):
        s = reeks("equivalentiegraad", "-", "pensioen", t, "-")
        verandert = s.diff().abs() > 1e-9
        c.eur(f"mi_eq_p_{k}_constant_vanaf", s.index[verandert.to_numpy().nonzero()[0].max()],
              f"equivalentiegraad pensioen {t}: eerste positie van het vlakke stuk")

    pens = pd.read_csv(DATA_RAW / "micro_pensioenen_correctie.csv")
    c.eur("mi_pens_min", pens.minimum.iloc[0], "minimumpensioen alleenstaande per maand", 2)
    for typ, sleutel, naam in (("WN", "wn", "werknemer"), ("ZE", "zn", "zelfstandige")):
        maximum = pens[pens.type == typ].maximum.iloc[0]
        c.eur(f"mi_pens_max_{sleutel}", maximum, f"maximaal bruto pensioen {naam} per maand", 2)
        c.eur(f"mi_pens_grens_{sleutel}", maximum / 0.6 * 12, f"loongrens pensioenberekening {naam} per jaar", 2)
    for typ, sleutel, naam in (("WN", "wn", "werknemer"), ("ZE", "ze", "eenmanszaak"),
                               ("ZV75", "zv75", "vennootschap 75% loon"), ("ZV50", "zv50", "vennootschap 50% loon")):
        p = pens[(pens.type == typ)].set_index("positie")
        c.eur(f"mi_pens_plafond_{sleutel}_vanaf", p[p.bindend == "maximum"].index.min(),
              f"eerste positie met het maximale pensioen ({naam})")
        c.eur(f"mi_pens_minimum_{sleutel}_tot", p[p.bindend == "minimum"].index.max(),
              f"laatste positie met het minimumpensioen ({naam})")
        c.eur(f"mi_pens_netto_max_{sleutel}", p.netto.max(), f"hoogste netto pensioen ({naam})", 0)


def main():
    zorg_voor_mappen()
    c = Cijfers()

    # <!-- wijziging: publicatie | {{doi}} verwijst naar het Zenodo-archief -->
    # Het rapport verwijst voor reproduceerbaarheid naar het gearchiveerde databestand,
    # niet naar de GitHub-repository: een DOI blijft werken, een repo-URL niet
    # noodzakelijk. Het nummer staat op één plaats, in CITATION.cff.
    c.tekst("doi", doi_uit_citation(), "DOI van het gearchiveerde databestand op Zenodo")

    bs = pd.read_csv(DATA_PROCESSED / "beroepssolidariteit.csv")
    bs = bs[bs["deflator"] == "cpi"]

    def reeks(defi, naam):
        return bs[(bs["definitie"] == defi) & (bs["reeks"] == naam)].set_index("jaar")["waarde"]

    ven = pd.read_csv(DATA_PROCESSED / "vennootschappen.csv", index_col="jaar")
    wn = pd.read_csv(DATA_PROCESSED / "werknemers_opsplitsing.csv", index_col="jaar")
    ns = pd.read_csv(DATA_PROCESSED / "nationale_solidariteit.csv", index_col="jaar")
    comp = pd.read_csv(DATA_RAW / "fodsz_componenten.csv", index_col="jaar")
    bedr = pd.read_csv(DATA_RAW / "fodsz_bedragen.csv", index_col="jaar")
    prijs = pd.read_csv(DATA_RAW / "prijsindex.csv", index_col="jaar")["cpi_2013"]
    pop = pd.read_csv(DATA_PROCESSED / "populaties.csv", index_col="jaar")

    # =======================================================================
    # 1. Beroepssolidariteit: niveaus en evoluties
    # =======================================================================
    for d in ("Z1", "Z2", "W1", "W2"):
        k = d.lower()
        r = reeks(d, "ratio_bijdragen_uitgaven")
        b = reeks(d, "bijdragen_pc_reeel")
        u = reeks(d, "uitgaven_pc_reeel")
        for j in (2003, 2014, 2015, 2018, 2019, 2020, 2022, 2023):
            c.pct(f"{k}_ratio_{j}", r[j], f"beroepssolidariteit {d} in {j}")
        for bj, ej in ((2003, 2023), (2003, 2014), (2014, 2015), (2015, 2018), (2015, 2019), (2018, 2019),
                       (2019, 2020), (2019, 2022), (2019, 2023), (2015, 2023), (2022, 2023)):
            c.pp(f"{k}_ratio_pp_{bj}_{ej}", r[ej] - r[bj], f"verandering beroepssolidariteit {d} {bj}-{ej}")
            c.rel(f"{k}_bijdr_{bj}_{ej}", b, bj, ej, f"reële bijdragen per capita {d} {bj}-{ej}")
            c.rel(f"{k}_uitg_{bj}_{ej}", u, bj, ej, f"reële uitgaven per capita {d} {bj}-{ej}")
        c.rel(f"{k}_ratio_rel_2003_2023", r, 2003, 2023, f"relatieve verandering ratio {d} 2003-2023")

    # Hoeveel sneller groeiden de uitgaven per capita bij zelfstandigen dan bij werknemers?
    z1u, w1u = reeks("Z1", "uitgaven_pc_reeel"), reeks("W1", "uitgaven_pc_reeel")
    groei_z = z1u[2023] / z1u[2003] - 1
    groei_w = w1u[2023] / w1u[2003] - 1
    c.getal("uitg_groei_factor_z_w", groei_z / groei_w, "uitgavengroei p.c. Z1 gedeeld door W1, 2003-2023", 1)

    # Mechanisch effect van de verlaging van de bijdragevoet zelfstandigen (tax shift):
    # bij een ongewijzigde bijdragebasis daalt de bijdrage met 20,5/22 - 1.
    voet = (20.5 / 22 - 1) * 100
    c.zet("taxshift_voet_rel", voet, f"{nl(voet, 1)}%", "mechanische daling bijdrage bij voet 22% -> 20,5%")

    # =======================================================================
    # 2. De breuk van 2015: wat verdwijnt uit de uitgaven?
    # =======================================================================
    for p, stelsel in (("z", "zelfstandigen"), ("w", "werknemers")):
        u = bedr[f"{p}_uitgaven"]
        gb = comp[f"{p}_gezinsbijslag"]
        c.mld(f"{p}_gezinsbijslag_2013", gb[2013], f"gezinsbijslag {stelsel} 2013 (nominaal)", dec=1 if p == "w" else 2)
        c.pct(f"{p}_gezinsbijslag_aandeel_2013", gb[2013] / u[2013], f"gezinsbijslag in % van uitgaven {stelsel} 2013", 1)
        c.mld(f"{p}_uitgaven_daling_2014_2015", u[2014] - u[2015], f"daling nominale uitgaven {stelsel} 2014-2015", 1)
        c.mld(f"{p}_gezinsbijslag_2014", gb[2014], f"gezinsbijslag {stelsel} 2014", dec=1 if p == "w" else 2)
        riz = comp[f"{p}_naar_riziv"]
        c.mld(f"{p}_riziv_daling_2014_2015", riz[2014] - riz[2015], f"daling overdrachten RIZIV {stelsel} 2014-2015",
              dec=1 if p == "w" else 2)

    # =======================================================================
    # 3. Vennootschapsbijdragen
    # =======================================================================
    vbn = ven["vb_per_vennootschap_nominaal_eur"]
    for j in (2003, 2004, 2005, 2006, 2019, 2023):
        c.eur(f"vb_nom_{j}", vbn[j], f"vennootschapsbijdrage per vennootschap, nominaal, {j}")
    periode = vbn.loc[2006:2019]
    c.eur("vb_nom_min_2006_2019", periode.min(), "laagste nominale bijdrage per vennootschap 2006-2019")
    c.eur("vb_nom_max_2006_2019", periode.max(), "hoogste nominale bijdrage per vennootschap 2006-2019")
    vbr = ven["vb_per_vennootschap_reeel_eur"]
    c.eur("vb_reeel_2006", vbr[2006], f"bijdrage per vennootschap 2006, prijzen {PRIJSJAAR}")
    c.eur("vb_reeel_2023", vbr[2023], f"bijdrage per vennootschap 2023, prijzen {PRIJSJAAR}")
    c.rel("vb_reeel_2006_2023", vbr, 2006, 2023, "reële verandering bijdrage per vennootschap 2006-2023")
    c.rel("vb_reeel_2006_2019", vbr, 2006, 2019, "reële verandering bijdrage per vennootschap 2006-2019", dec=1)
    erosie = (prijs[2006] / prijs[2019] - 1) * 100
    c.zet("inflatie_erosie_2006_2019", erosie, f"{teken(erosie, 1)}%",
          "reële waardeverandering van een bevroren nominaal bedrag 2006-2019")
    n = ven["aantal_vennootschappen"]
    c.rel("aantal_venn_2003_2023", n, 2003, 2023, "groei aantal vennootschappen 2003-2023")
    c.rel("aantal_venn_2006_2023", n, 2006, 2023, "groei aantal vennootschappen 2006-2023")
    c.rel("aantal_venn_2006_2019", n, 2006, 2019, "groei aantal vennootschappen 2006-2019")
    for j in (2003, 2005, 2023):
        c.pct(f"vb_aandeel_{j}", ven["aandeel_vb_in_bijdragen"][j], f"aandeel vennootschapsbijdragen in bijdragen {j}", 1)

    # Bijdrage van de vennootschapsbijdrage aan de ratio en een contrafeitelijke indexering.
    # component = vennootschapsbijdragen / uitgaven (nominaal; prijs en populatie vallen weg)
    comp_vb = bedr["z_vennootschapsbijdragen"] / bedr["z_uitgaven"]
    # contrafeitelijk: het nominale bedrag per vennootschap van 2006 mee geïndexeerd met de CPI
    vb_idx = n * (vbn[2006] * prijs / prijs[2006]) / 1000
    comp_idx = vb_idx / bedr["z_uitgaven"]
    ratio_z1 = reeks("Z1", "ratio_bijdragen_uitgaven")
    daling = ratio_z1[2023] - ratio_z1[2006]
    c.pct("vb_comp_2006", comp_vb[2006], "vennootschapsbijdragen in % van uitgaven 2006", 1)
    c.pct("vb_comp_2023", comp_vb[2023], "vennootschapsbijdragen in % van uitgaven 2023", 1)
    c.pct("vb_comp_idx_2023", comp_idx[2023], "idem 2023 bij indexering van het bedrag van 2006", 1)
    c.pp("vb_comp_pp", comp_vb[2023] - comp_vb[2006], "verandering component 2006-2023")
    c.pp("vb_niet_indexering_pp", comp_vb[2023] - comp_idx[2023], "effect niet-indexering op de ratio 2023")
    c.pp("ratio_z1_pp_2006_2023", daling, "verandering beroepssolidariteit Z1 2006-2023")
    c.pct("vb_comp_deel_daling", (comp_vb[2023] - comp_vb[2006]) / daling, "deel van de daling 2006-2023", 0)
    c.pct("vb_idx_deel_daling", (comp_vb[2023] - comp_idx[2023]) / daling, "niet-indexering als deel van de daling", 0)
    c.mld("vb_gederfd_2023", vb_idx[2023] - bedr["z_vennootschapsbijdragen"][2023],
          "gederfde opbrengst 2023 bij indexering sinds 2006 (nominaal)", 2)

    # Conclusie: hoeveel bijdragen zijn nodig om de beroepssolidariteit van 2006 te herstellen,
    # bij de uitgaven van 2023? En welk deel daarvan levert volledige indexering van de VB?
    herstel = (ratio_z1[2006] - ratio_z1[2023]) * bedr["z_uitgaven"][2023]      # duizend euro
    gederfd = vb_idx[2023] - bedr["z_vennootschapsbijdragen"][2023]              # duizend euro
    c.getal("herstel_2006_mio", herstel / 1000, "bijkomende bijdragen 2023 nodig voor ratio van 2006 (miljoen euro)")
    c.getal("vb_gederfd_2023_mio", gederfd / 1000, "gederfde opbrengst 2023 bij indexering sinds 2006 (miljoen euro)")
    c.pct("vb_idx_deel_herstel", gederfd / herstel, "indexering VB als deel van het herstelbedrag", 0)

    # Gewone bijdragen per verzekerde
    for d in ("Z1", "Z2"):
        g = ven[f"gewone_bijdragen_pc_reeel_{d}"]
        for bj, ej in ((2003, 2023), (2006, 2023), (2006, 2019), (2003, 2015), (2015, 2019), (2019, 2023)):
            c.rel(f"gewone_{d.lower()}_{bj}_{ej}", g, bj, ej, f"reële gewone bijdragen per verzekerde {d} {bj}-{ej}")
    c.getal("venn_per_z1_2006", n[2006] / pop["Z1"][2006], "vennootschappen per verzekerde Z1 2006", 2)
    c.getal("venn_per_z1_2023", n[2023] / pop["Z1"][2023], "vennootschappen per verzekerde Z1 2023", 2)
    c.rel("pop_z1_2003_2023", pop["Z1"], 2003, 2023, "groei Z1 2003-2023")
    c.rel("pop_w1_2003_2023", pop["W1"], 2003, 2023, "groei W1 2003-2023")

    # Pensioenen als aandeel van de uitgaven zelfstandigen
    for j in (2003, 2023):
        c.pct(f"z_pensioen_aandeel_{j}", comp["z_pensioenen"][j] / bedr["z_uitgaven"][j],
              f"pensioenen in % van uitgaven zelfstandigen {j}", 0)

    # =======================================================================
    # 4. Werknemers- en werkgeversbijdragen (NBB)
    # =======================================================================
    c.pct("wg_aandeel_gem", wn["aandeel_werkgevers"].mean(), "gemiddeld aandeel werkgevers 2003-2023")
    c.pct("wg_aandeel_min", wn["aandeel_werkgevers"].min(), "laagste aandeel werkgevers")
    c.pct("wg_aandeel_max", wn["aandeel_werkgevers"].max(), "hoogste aandeel werkgevers")
    c.getal("nbb_fodsz_min", wn["verschil_nbb_fodsz_in_pct_van_fodsz"].min(), "NBB-totaal boven FOD SZ, minimum (%)")
    c.getal("nbb_fodsz_max", wn["verschil_nbb_fodsz_in_pct_van_fodsz"].max(), "NBB-totaal boven FOD SZ, maximum (%)")
    for soort in ("werknemers", "werkgevers"):
        s = wn[f"{soort}bijdragen_pc_reeel_W1"]
        for bj, ej in ((2003, 2023), (2003, 2015), (2015, 2018), (2018, 2023)):
            c.rel(f"{soort}_pc_{bj}_{ej}", s, bj, ej, f"reële {soort}bijdragen per capita W1 {bj}-{ej}")

    # =======================================================================
    # 5. Nationale solidariteit
    # =======================================================================
    for p, stelsel in (("z", "zelfstandigen"), ("w", "werknemers")):
        s = ns[f"{p}_nationale_solidariteit"]
        for j in (2000, 2007, 2009, 2014, 2015, 2016, 2017, 2019, 2020, 2022, 2023):
            c.pct(f"{p}_ns_{j}", s[j], f"nationale solidariteit {stelsel} {j}")
        # Eindjaar 2023, zoals alle reeksen (zie common.JAREN_NS)
        for bj, ej in ((2000, 2023), (2000, 2007), (2007, 2009), (2009, 2014), (2014, 2015), (2015, 2019),
                       (2019, 2020), (2019, 2022), (2022, 2023)):
            c.pp(f"{p}_ns_pp_{bj}_{ej}", s[ej] - s[bj], f"verandering nationale solidariteit {stelsel} {bj}-{ej}")
        c.rel(f"{p}_ns_rel_2000_2023", s, 2000, 2023, f"relatieve verandering NS {stelsel} 2000-2023")
        for bron in ("bijdragen", "toelagen", "alternatieve", "overige"):
            a = ns[f"{p}_aandeel_{bron}"]
            for j in (2000, 2016, 2017, 2020, 2023):
                c.pct(f"{p}_aandeel_{bron}_{j}", a[j], f"aandeel {bron} {stelsel} {j}")
        c.mld(f"{p}_toelagen_2016", comp[f"{p}_toelagen_bedrag"][2016], f"toelagen {stelsel} 2016", 1)
        c.mld(f"{p}_toelagen_2017", comp[f"{p}_toelagen_bedrag"][2017], f"toelagen {stelsel} 2017", 1)
        c.mld(f"{p}_altfin_2016", comp[f"{p}_alternatieve_bedrag"][2016], f"alternatieve financiering {stelsel} 2016", 1)
        c.mld(f"{p}_altfin_2017", comp[f"{p}_alternatieve_bedrag"][2017], f"alternatieve financiering {stelsel} 2017", 1)
        t = ns[f"{p}_toelagen_in_ns"]
        c.pct(f"{p}_toelagen_in_ns_2016", t[2016], f"toelagen binnen NS {stelsel} 2016")
        c.pct(f"{p}_toelagen_in_ns_2017", t[2017], f"toelagen binnen NS {stelsel} 2017")
        c.pct(f"{p}_toelagen_in_ns_2020", t[2020], f"toelagen binnen NS {stelsel} 2020")
        c.pct(f"{p}_toelagen_in_ns_2023", t[2023], f"toelagen binnen NS {stelsel} 2023")
        # Samenstelling van de alternatieve financiering over de rapportperiode (voetnoot btw in §6.1)
        jaren = ns.index                                           # 2000-2023, zie common.JAREN_NS
        alt = comp[f"{p}_alternatieve_bedrag"].loc[jaren]
        btw = comp[f"{p}_btw_bedrag"].loc[jaren] / alt
        rv = comp[f"{p}_rv_bedrag"].loc[jaren] / alt
        ander = 1 - btw - rv
        c.pct(f"{p}_altfin_btw_min", btw.min(), f"laagste aandeel btw in alternatieve financiering {stelsel}")
        c.pct(f"{p}_altfin_btw_max", btw.max(), f"hoogste aandeel btw in alternatieve financiering {stelsel}")
        c.pct(f"{p}_altfin_rv_max", rv.max(), f"hoogste aandeel roerende voorheffing in alternatieve financiering {stelsel}")
        c.pct(f"{p}_altfin_ander_max", ander.max(), f"hoogste aandeel andere bronnen in alternatieve financiering {stelsel}")

        # Conclusie (§7), 22 september 2026: toelagen binnen de NS in 2017-2019 (duidelijk verschil tussen
        # de stelsels, voor de coronacrisis) en het gewicht van de btw in de NS en in alle inkomsten.
        t1719 = t.loc[2017:2019]
        c.pct(f"{p}_toelagen_in_ns_1719_min", t1719.min(), f"laagste aandeel toelagen binnen NS {stelsel} 2017-2019")
        c.pct(f"{p}_toelagen_in_ns_1719_max", t1719.max(), f"hoogste aandeel toelagen binnen NS {stelsel} 2017-2019")
        # btw als deel van alle lopende ontvangsten = (btw / alternatieve financiering) x aandeel alternatieve financiering
        btw_ink = btw * ns[f"{p}_aandeel_alternatieve"].loc[jaren]
        btw_ns = btw_ink / ns[f"{p}_nationale_solidariteit"].loc[jaren]
        c.pct(f"{p}_btw_in_inkomsten_2023", btw_ink[2023], f"btw als aandeel van de inkomsten {stelsel} 2023")
        c.pct(f"{p}_btw_in_ns_2023", btw_ns[2023], f"btw als aandeel van de nationale solidariteit {stelsel} 2023")

    # ---------------------------------------------------------------------------
    # Methodologie (§5.2.1): robuustheid gezondheidsindex en definitiebreuk 2003
    # ---------------------------------------------------------------------------
    bs_alle = pd.read_csv(DATA_PROCESSED / "beroepssolidariteit.csv")
    ev = bs_alle[bs_alle["reeks"].isin(["index_bijdragen_pc", "index_uitgaven_pc"]) & (bs_alle["jaar"] == 2023)]
    ev = ev.pivot_table(index=["definitie", "reeks"], columns="deflator", values="waarde")
    verschil = ev["gezondheidsindex"] - ev["cpi"]          # indexpunten = procentpunt t.o.v. 2003
    c.zet("gi_verschil_min", verschil.min(), nl(verschil.min(), 1),
          "kleinste verschil gezondheidsindex - CPI in groei 2003-2023 (procentpunt)")
    c.zet("gi_verschil_max", verschil.max(), nl(verschil.max(), 1),
          "grootste verschil gezondheidsindex - CPI in groei 2003-2023 (procentpunt)")
    for defl, sleutel in (("cpi", "z2_bijdr_cpi_2003_2023"), ("gezondheidsindex", "z2_bijdr_gi_2003_2023")):
        w = ev.loc[("Z2", "index_bijdragen_pc"), defl] - 100
        c.zet(sleutel, w, f"{teken(w, 1)}%", f"reële bijdragen per capita Z2 2003-2023, deflator {defl}")
    gi_ratio = bs_alle[(bs_alle["reeks"] == "ratio_bijdragen_uitgaven") & (bs_alle["definitie"] == "Z1")]
    gi_ratio = gi_ratio.pivot_table(index="jaar", columns="deflator", values="waarde")
    assert (gi_ratio["cpi"] - gi_ratio["gezondheidsindex"]).abs().max() < 1e-12, "ratio hangt af van deflator?"

    rsvz = pd.read_csv(DATA_RAW / "rsvz_samenstelling.csv", index_col="jaar")
    c.getal("rsvz_helpers_2002", rsvz.loc[2002, "helpers"], "RSVZ helpers 2002")
    c.getal("rsvz_helpers_2003", rsvz.loc[2003, "helpers"], "RSVZ helpers 2003")
    c.rel("rsvz_helpers_2002_2003", rsvz["helpers"], 2002, 2003, "groei helpers 2002-2003")
    tot = rsvz["zelfstandigen"] + rsvz["helpers"]
    c.rel("rsvz_totaal_2002_2003", tot, 2002, 2003, "groei zelfstandigen en helpers 2002-2003", dec=1)

    # wijziging: nieuw | 22 september 2026, leesnota G5: het aantal helpers in de KSZ-reeks in 2003.
    # De KSZ-reeks begint in het vierde kwartaal van 2003, dus na 1 januari 2003. Dit cijfer laat zien
    # dat 2003 bij de KSZ al op het niveau NA de breuk ligt, niet op dat ervoor.
    ksz = pd.read_csv(DATA_RAW / "ksz_populatie.csv", index_col="jaar")
    c.getal("ksz_helpers_2003", ksz.loc[2003, "n13"], "KSZ helpers (n13) 2003, vierde kwartaal")

    # ---------------------------------------------------------------------------
    # Scenario rechtsvorm: groei als eenmanszaken i.p.v. vennootschappen (Bijlage 6)
    # Berekend in 03b_scenario_rechtsvorm.py; hier enkel opgemaakt.
    # ---------------------------------------------------------------------------
    kern = pd.read_csv(DATA_PROCESSED / "scenario_rechtsvorm_kern.csv", index_col="sleutel")["waarde"]
    c.getal("sr_n_extra", kern["n_extra"], "extra vennootschappen 2003-2023")
    c.eur("sr_vb_2023", kern["vb_per_venn_2023"], "gemiddelde vennootschapsbijdrage 2023")
    c.eur("sr_omslag", kern["omslag_sx"], "omslagpunt: winst buiten bijdragebasis per extra vennootschap")
    c.eur("sr_omslag_afgerond", round(kern["omslag_sx"], -2), "omslagpunt, afgerond op 100 euro")
    c.pct("sr_ratio_2023", kern["ratio_2023"], "beroepssolidariteit zelfstandigen 2023 (totalen)", 1)
    c.getal("sr_1pp_mio", kern["uitgaven_1pp_eur"] / 1e6, "1 procentpunt in miljoen euro", 0)
    c.getal("sr_delta_bl", kern["delta_bedrijfsleiders_2014_2021"], "extra bedrijfsleiders AJ2015-AJ2022")
    c.getal("sr_delta_venn", kern["delta_venn_2014_2021"], "extra vennootschappen 2014-2021")
    c.getal("sr_bl_per_venn", kern["bl_per_venn"], "extra bedrijfsleiders per extra vennootschap", 2)
    c.eur("sr_plafond_1", kern["plafond_1"], "eerste plafond 2024", 2)
    c.eur("sr_plafond_2", kern["plafond_2"], "tweede plafond 2024", 2)
    c.eur("sr_vb_typegeval", kern["vb_typegeval"], "vennootschapsbijdrage 2024, laag bedrag (typegevallen Bijlage 6)", 2)
    c.eur("sr_min_bezoldiging", kern["min_bezoldiging"], "minimumbezoldiging verlaagd tarief")
    c.pp("ratio_z1_pp_2003_2023", ratio_z1[2023] - ratio_z1[2003], "verandering beroepssolidariteit Z1 2003-2023")

    # ---------------------------------------------------------------------------
    # Opbrengst van ingrepen aan de top (conclusie §7, leesnota K6-K7), 22 september 2026.
    # Invoer: ABC-verslag 2022/04 Tabel 7 (data/raw, overgetypt en gecontroleerd in m04) en de
    # statische berekening van code/micro/m04_abc_opbrengst.py. Hier enkel opgemaakt.
    # ---------------------------------------------------------------------------
    abc = pd.read_csv(DATA_RAW / "abc_2022_tabel7.csv", index_col="schijf")
    top = abc.loc["boven_plafond"]
    c.pct("abc_plafond_personen", top["aandeel_personen"], "ABC Tabel 7: aandeel hoofdberoepers boven de maximumgrens", 1)
    c.pct("abc_plafond_inkomensmassa", top["aandeel_inkomensmassa"], "ABC Tabel 7: hun aandeel in de inkomensmassa")
    c.pct("abc_plafond_bijdragen", top["aandeel_bijdragemassa"], "ABC Tabel 7: hun aandeel in de bijdragen")
    opb = pd.read_csv(DATA_PROCESSED / "abc_opbrengst_statisch.csv", index_col="scenario")
    pl = opb.loc["geen_plafond"]
    c.pct("abc_plafond_rel", pl["opbrengst_rel"], "plafond weg: statische stijging gewone bijdragen hoofdberoepers")
    # afgerond op 10 miljoen: de onzekerheid (jaren door elkaar, afronding ABC) is groter dan 1 miljoen
    c.getal("abc_plafond_mln_laag", round(pl["hoofdberoep_mln_euro_2023"], -1), "plafond weg: ondergrens (miljoen euro, niveau 2023)")
    c.getal("abc_plafond_mln_hoog", round(pl["bovengrens_mln_euro_2023"], -1), "plafond weg: bovengrens (miljoen euro, niveau 2023)")
    c.pct("abc_plafond_kloof_laag", pl["hoofdberoep_mln_euro_2023"] / (herstel / 1000), "plafond weg: ondergrens als deel van de financieringskloof")
    c.pct("abc_plafond_kloof_hoog", pl["bovengrens_mln_euro_2023"] / (herstel / 1000), "plafond weg: bovengrens als deel van de financieringskloof")

    typ = pd.read_csv(DATA_PROCESSED / "scenario_rechtsvorm_typen.csv")
    c.eur("sr_typ2_buiten", typ.loc[1, "winst_eur"] - typ.loc[1, "bezoldiging_eur"],
          "typegeval 2: winst die niet als bezoldiging wordt uitgekeerd")

    sc = pd.read_csv(DATA_PROCESSED / "scenario_rechtsvorm.csv")
    for _, r in sc.iterrows():
        s = int(round(r["aandeel_met_zelfstandige_activiteit_s"] * 100))
        x = int(r["winst_buiten_bijdragebasis_X_eur"])
        c.pp(f"sr_pp_s{s}_x{x}", r["verschil_procentpunt"] / 100,
             f"scenario s={s}%, X={x} euro: verschil beroepssolidariteit 2023")
        v = r["verschil_procentpunt"]
        c.zet(f"sr_tab_s{s}_x{x}", v, teken(v, 1), f"scenario s={s}%, X={x} euro: procentpunt (tabelweergave)")
        c.zet(f"sr_mio_s{s}_x{x}", r["verschil_totaal_miljoen_eur"],
              f"{teken(r['verschil_totaal_miljoen_eur'])}", f"scenario s={s}%, X={x} euro: verschil in miljoen euro")

    sel = sc[(sc["aandeel_met_zelfstandige_activiteit_s"] == 0.5) & (sc["winst_buiten_bijdragebasis_X_eur"] == 10_000)]
    c.pct("sr_s50_x10000_deel_daling",
          sel["verschil_procentpunt"].iloc[0] / 100 / abs(ratio_z1[2023] - ratio_z1[2003]),
          "scenario s=50%, X=10.000 als deel van de daling 2003-2023", 0)

    typen = pd.read_csv(DATA_PROCESSED / "scenario_rechtsvorm_typen.csv")
    for i, r in typen.iterrows():
        k = f"sr_typ{i + 1}"
        c.eur(f"{k}_winst", r["winst_eur"], f"typegeval {i + 1}: winst")
        c.eur(f"{k}_bezoldiging", r["bezoldiging_eur"], f"typegeval {i + 1}: bezoldiging")
        c.eur(f"{k}_eenmanszaak", r["bijdrage_eenmanszaak_eur"], f"typegeval {i + 1}: bijdrage als eenmanszaak")
        c.eur(f"{k}_vennootschap", r["bijdrage_vennootschap_incl_vb_eur"], f"typegeval {i + 1}: bijdrage via vennootschap")
        v = r["verschil_eur"]
        c.zet(f"{k}_verschil", v, ("+" if v >= 0 else "-") + f"€{nl(abs(v))}", f"typegeval {i + 1}: verschil")

    # ---------------------------------------------------------------------------
    # Microdeel (§6.2, §5.2.2 en Bijlage 7). Berekend in code/micro/m01-m05; hier enkel opgemaakt.
    # ---------------------------------------------------------------------------
    micro_cijfers(c)

    # ---------------------------------------------------------------------------
    # Wegschrijven en templates invullen
    # ---------------------------------------------------------------------------
    df = pd.DataFrame([(k, *v) for k, v in c.rijen.items()],
                      columns=["sleutel", "waarde_exact", "weergave", "omschrijving"])
    df.to_csv(OUT_TABLES / "tekstcijfers.csv", index=False, float_format="%.10g")
    print(f"geschreven: output/tables/tekstcijfers.csv ({len(df)} cijfers)")

    SECTIES.mkdir(parents=True, exist_ok=True)
    # Plaatshouders: {{sleutel}} of {{sleutel|filter}}
    #   |daling    de waarde MOET negatief zijn; getoond zonder minteken ("daalde met 7,3 procentpunt")
    #   |stijging  de waarde MOET positief zijn; getoond zonder plusteken ("steeg met 21%")
    # Zo staat de richting in het werkwoord, en geeft het script een fout als de data
    # ooit van richting veranderen, in plaats van stilzwijgend een verkeerde zin te maken.
    # Sommige markdown-editors (en pandoc bij een omweg via Word) schrijven een liggend
    # streepje in de sleutel als "\_". Dat laten we toe en maken we hier weer ongedaan.
    patroon = re.compile(r"\{\{\s*((?:[a-z0-9]|\\?_)+)\s*(?:\|\s*(daling|stijging)\s*)?\}\}")

    def vul_in(m, bestand):
        sleutel, filt = m.group(1).replace("\\_", "_"), m.group(2)
        waarde, weergave, _ = c.rijen[sleutel]
        if filt == "daling":
            if not waarde < 0:
                raise ValueError(f"{bestand}: {sleutel} staat als daling, maar is {weergave}")
            return weergave.lstrip("-")
        if filt == "stijging":
            if not waarde > 0:
                raise ValueError(f"{bestand}: {sleutel} staat als stijging, maar is {weergave}")
            return weergave.lstrip("+")
        return weergave

    for tpl in sorted(TEMPLATES.glob("*.md")):
        tekst = tpl.read_text(encoding="utf-8")
        onbekend = sorted({m.group(1).replace("\\_", "_") for m in patroon.finditer(tekst)
                           if m.group(1).replace("\\_", "_") not in c.rijen})
        if onbekend:
            raise KeyError(f"{tpl.name}: onbekende plaatshouders {onbekend}")
        ingevuld = patroon.sub(lambda m: vul_in(m, tpl.name), tekst)
        if "{{" in ingevuld:
            # Toon waar het misloopt: regelnummer en het stuk tekst zelf.
            plek = ingevuld.index("{{")
            regel = ingevuld[:plek].count("\n") + 1
            stuk = ingevuld[plek:plek + 60].split("\n")[0]
            raise ValueError(
                f"{tpl.name}, regel {regel}: plaatshouder met ongeldige schrijfwijze: {stuk!r}. "
                "Een plaatshouder ziet eruit als {{sleutel}} of {{sleutel|daling}}, met enkel "
                "kleine letters, cijfers en liggende streepjes in de sleutel.")
        kop = ("<!-- GEGENEREERD door code/macro/07_tekstcijfers.py uit report/templates/"
               f"{tpl.name}. Niet hier bewerken: pas de template aan en draai het script opnieuw. -->\n\n")
        (SECTIES / tpl.name).write_text(kop + ingevuld, encoding="utf-8")
        print(f"ingevuld: report/sections/{tpl.name}")


if __name__ == "__main__":
    main()
