"""
Stap 3: alle indicatoren van het macrodeel berekenen -> data/processed/*.csv

Dit script vervangt ALLE formules uit het werkboek van Willem. Het leest enkel
data/raw/*.csv (de overgenomen inputs) en schrijft:

  populaties.csv              W1, W2, Z1, Z2 en het aandeel zelfstandigen (Figuur 1, Bijlage 2)
  samenstelling.csv           samenstelling zelfstandigenpopulatie RSVZ (Figuur 2)
  beroepssolidariteit.csv     reële bijdragen/uitgaven per capita, indexen, ratio (Figuur 4, B4.1)
  vennootschappen.csv         gewone en vennootschapsbijdragen (Figuur 5, B4.2)
  werknemers_opsplitsing.csv  werknemers- en werkgeversbijdragen NBB (Figuur B5.1)
  nationale_solidariteit.csv  aandelen financieringsbronnen (Figuur 6, 7)
  perioden.csv                procentuele veranderingen over de periodes uit de tekst

Begrippen (kort)
----------------
  nominaal   bedrag in euro van dat jaar
  reëel      bedrag omgerekend naar prijzen van 2024, zodat inflatie wegvalt
  per capita gedeeld door het aantal verzekerden
  index      waarde t.o.v. het basisjaar, basisjaar = 100
  ratio      reële bijdragen per capita / reële uitgaven per capita
             (= beroepssolidariteit; populatie en inflatie vallen hier weg,
             want teller en noemer worden door hetzelfde getal gedeeld)

Uitvoeren:  python code/macro/03_indicators.py
"""

import pandas as pd

from common import (BASISJAAR_BS, BASISJAAR_NS, DATA_PROCESSED, DATA_RAW, JAREN_BS, JAREN_NS,
                    JAREN_NS_RECONCILIATIE, PRIJSJAAR,
                    index, procentpunt_verschil, relatieve_verandering, zorg_voor_mappen)


def lees(naam: str) -> pd.DataFrame:
    return pd.read_csv(DATA_RAW / f"{naam}.csv", index_col="jaar")


# ===========================================================================
# 1. Populaties (KSZ-nomenclatuur, zie Tabel 5 in het rapport)
# ===========================================================================
def populaties(ksz: pd.DataFrame) -> pd.DataFrame:
    p = pd.DataFrame(index=ksz.index)
    # W1: iedereen met hoofdactiviteit in loondienst
    p["W1"] = ksz["n11"] + ksz["n141"]
    # W2: W1 plus wie ook in loondienst werkt maar voornamelijk zelfstandig is
    p["W2"] = ksz["n11"] + ksz["n141"] + ksz["n142"] + ksz["n143"]
    # Z1: iedereen met hoofdactiviteit als zelfstandige of helper
    p["Z1"] = ksz["n12"] + ksz["n13"] + ksz["n142"] + ksz["n143"]
    # Z2: Z1 plus wie ook zelfstandig werkt maar voornamelijk in loondienst
    p["Z2"] = ksz["n12"] + ksz["n13"] + ksz["n141"] + ksz["n142"] + ksz["n143"]
    # Let op: W2 en Z1 overlappen (n142, n143), net als W1 en Z2 (n141).
    # Daarom is 'werkende bevolking' = Z1 + W1 (zonder dubbeltellingen).
    p["werkende_bevolking"] = p["Z1"] + p["W1"]
    p["aandeel_zelfstandigen_Z1"] = p["Z1"] / p["werkende_bevolking"]
    p["aandeel_werknemers_W1"] = p["W1"] / p["werkende_bevolking"]
    for k in ("W1", "W2", "Z1", "Z2"):
        p[f"index_{k}"] = index(p[k], BASISJAAR_BS)
    return p


# ===========================================================================
# 2. Samenstelling zelfstandigenpopulatie (RSVZ)
# ===========================================================================
def samenstelling(rsvz: pd.DataFrame) -> pd.DataFrame:
    s = rsvz.copy()
    s["totaal_hoedanigheid"] = s["zelfstandigen"] + s["helpers"]
    aard = ["hoofdberoep", "bijberoep", "actief_na_pensioen"]
    s["totaal_aard"] = s[aard].sum(axis=1)
    for a in aard:
        s[f"aandeel_{a}"] = s[a] / s["totaal_aard"]
        s[f"index_{a}"] = index(s[a], BASISJAAR_BS)
    sectoren = ["landbouw", "visserij", "nijverheid", "handel", "vrije_beroepen", "diensten", "diversen"]
    s["totaal_sector"] = s[sectoren].sum(axis=1)
    # Landbouw en visserij worden in Figuur 2C samengenomen
    s["landbouw_visserij"] = s["landbouw"] + s["visserij"]
    for sec in ["landbouw_visserij", "nijverheid", "handel", "vrije_beroepen", "diensten", "diversen"]:
        s[f"aandeel_{sec}"] = s[sec] / s["totaal_sector"]
    s["index_vennootschappen"] = index(s["vennootschappen"], BASISJAAR_BS)
    s["index_zelfstandigen_rsvz"] = index(s["totaal_hoedanigheid"], BASISJAAR_BS)
    return s


# ===========================================================================
# 3. Beroepssolidariteit
# ===========================================================================
def omzettingsfactor(prijsindex: pd.Series) -> pd.Series:
    """Factor om nominale bedragen van jaar t om te zetten naar prijzen van 2024.

    reëel_t = nominaal_t * (index_2024 / index_t)
    Het rebasen van de index naar 2024 = 100 (zoals in het werkboek) verandert
    deze factor niet, dus we delen rechtstreeks.
    """
    return prijsindex.loc[PRIJSJAAR] / prijsindex


def beroepssolidariteit(bedragen: pd.DataFrame, pop: pd.DataFrame, prijs: pd.DataFrame) -> pd.DataFrame:
    """Lang formaat: één rij per jaar x stelsel x definitie x deflator x reeks."""
    rijen = []
    jaren = JAREN_BS
    for deflator, kol in (("cpi", "cpi_2013"), ("gezondheidsindex", "gezondheidsindex_2013")):
        factor = omzettingsfactor(prijs[kol]).loc[jaren]
        for stelsel, prefix, definities in (("zelfstandigen", "z", ("Z1", "Z2")),
                                            ("werknemers", "w", ("W1", "W2"))):
            bijdragen_reeel = bedragen[f"{prefix}_bijdragen"].loc[jaren] * factor
            uitgaven_reeel = bedragen[f"{prefix}_uitgaven"].loc[jaren] * factor
            for d in definities:
                n = pop[d].loc[jaren]
                reeksen = {
                    "populatie": n,
                    "index_populatie": index(n, BASISJAAR_BS),
                    # duizend euro / persoon = duizend euro per capita
                    "bijdragen_pc_reeel": bijdragen_reeel / n,
                    "uitgaven_pc_reeel": uitgaven_reeel / n,
                }
                reeksen["index_bijdragen_pc"] = index(reeksen["bijdragen_pc_reeel"], BASISJAAR_BS)
                reeksen["index_uitgaven_pc"] = index(reeksen["uitgaven_pc_reeel"], BASISJAAR_BS)
                reeksen["ratio_bijdragen_uitgaven"] = reeksen["bijdragen_pc_reeel"] / reeksen["uitgaven_pc_reeel"]
                for reeks, s in reeksen.items():
                    for jaar, w in s.items():
                        rijen.append((jaar, stelsel, d, deflator, reeks, w))
    return pd.DataFrame(rijen, columns=["jaar", "stelsel", "definitie", "deflator", "reeks", "waarde"])


# ===========================================================================
# 4. Vennootschapsbijdragen en gewone bijdragen (zelfstandigen)
# ===========================================================================
def vennootschappen(bedragen: pd.DataFrame, pop: pd.DataFrame, rsvz: pd.DataFrame,
                    prijs: pd.DataFrame) -> pd.DataFrame:
    jaren = JAREN_BS
    factor = omzettingsfactor(prijs["cpi_2013"]).loc[jaren]
    v = pd.DataFrame(index=pd.Index(jaren, name="jaar"))
    v["aantal_vennootschappen"] = rsvz["vennootschappen"].loc[jaren]
    v["vennootschapsbijdragen_nominaal"] = bedragen["z_vennootschapsbijdragen"].loc[jaren]
    v["vennootschapsbijdragen_reeel"] = v["vennootschapsbijdragen_nominaal"] * factor
    # Per vennootschap in EURO (bedragen staan in duizend euro, dus x 1000)
    v["vb_per_vennootschap_nominaal_eur"] = v["vennootschapsbijdragen_nominaal"] * 1000 / v["aantal_vennootschappen"]
    v["vb_per_vennootschap_reeel_eur"] = v["vennootschapsbijdragen_reeel"] * 1000 / v["aantal_vennootschappen"]
    v["index_aantal_vennootschappen"] = index(v["aantal_vennootschappen"], BASISJAAR_BS)
    v["index_vb_per_vennootschap"] = index(v["vb_per_vennootschap_reeel_eur"], BASISJAAR_BS)

    v["gewone_bijdragen_reeel"] = bedragen["z_gewone_bijdragen"].loc[jaren] * factor
    for d in ("Z1", "Z2"):
        v[f"populatie_{d}"] = pop[d].loc[jaren]
        v[f"index_populatie_{d}"] = index(pop[d].loc[jaren], BASISJAAR_BS)
        v[f"gewone_bijdragen_pc_reeel_{d}"] = v["gewone_bijdragen_reeel"] * 1000 / pop[d].loc[jaren]
        v[f"index_gewone_bijdragen_pc_{d}"] = index(v[f"gewone_bijdragen_pc_reeel_{d}"], BASISJAAR_BS)

    v["aandeel_vb_in_bijdragen"] = bedragen["z_vennootschapsbijdragen"].loc[jaren] / bedragen["z_bijdragen"].loc[jaren]
    v["aandeel_gewone_in_bijdragen"] = bedragen["z_gewone_bijdragen"].loc[jaren] / bedragen["z_bijdragen"].loc[jaren]
    return v


# ===========================================================================
# 5. Werknemers- en werkgeversbijdragen (NBB, Bijlage 5)
# ===========================================================================
def werknemers_opsplitsing(nbb: pd.DataFrame, bedragen: pd.DataFrame, pop: pd.DataFrame,
                           prijs: pd.DataFrame) -> pd.DataFrame:
    jaren = JAREN_BS
    factor = omzettingsfactor(prijs["cpi_2013"]).loc[jaren]
    o = pd.DataFrame(index=pd.Index(jaren, name="jaar"))
    o["werknemersbijdragen_nominaal"] = nbb["werknemersbijdragen_d613"].loc[jaren]
    o["werkgeversbijdragen_nominaal"] = nbb["werkgeversbijdragen_d611"].loc[jaren]
    o["totaal_nbb"] = o["werknemersbijdragen_nominaal"] + o["werkgeversbijdragen_nominaal"]
    o["aandeel_werknemers"] = o["werknemersbijdragen_nominaal"] / o["totaal_nbb"]
    o["aandeel_werkgevers"] = o["werkgeversbijdragen_nominaal"] / o["totaal_nbb"]

    # Vergelijking met het FOD SZ-totaal van HETZELFDE jaar (correctie G3:
    # het werkboek vergeleek NBB-jaar t met FOD SZ-jaar t-3).
    o["totaal_fodsz"] = bedragen["w_bijdragen"].loc[jaren]
    o["verschil_nbb_fodsz_in_pct_van_fodsz"] = (o["totaal_nbb"] / o["totaal_fodsz"] - 1) * 100

    for d in ("W1", "W2"):
        n = pop[d].loc[jaren]
        o[f"index_populatie_{d}"] = index(n, BASISJAAR_BS)
        for soort in ("werknemers", "werkgevers"):
            pc = o[f"{soort}bijdragen_nominaal"] * factor / n
            o[f"{soort}bijdragen_pc_reeel_{d}"] = pc
            o[f"index_{soort}bijdragen_pc_{d}"] = index(pc, BASISJAAR_BS)
    return o


# ===========================================================================
# 6. Nationale solidariteit
# ===========================================================================
def nationale_solidariteit(aandelen: pd.DataFrame, jaren: list | None = None) -> pd.DataFrame:
    # Standaard de rapportperiode (2000-2023); 04_reconcile.py vraagt 2000-2024.
    jaren = JAREN_NS if jaren is None else jaren
    n = pd.DataFrame(index=pd.Index(jaren, name="jaar"))
    for stelsel, p in (("zelfstandigen", "z"), ("werknemers", "w")):
        a = aandelen.loc[jaren]
        for bron in ("bijdragen", "toelagen", "alternatieve", "overige"):
            n[f"{p}_aandeel_{bron}"] = a[f"{p}_aandeel_{bron}"]
        # Nationale solidariteit = toelagen van publieke overheden + alternatieve financiering
        n[f"{p}_nationale_solidariteit"] = a[f"{p}_aandeel_toelagen"] + a[f"{p}_aandeel_alternatieve"]
        n[f"{p}_index_nationale_solidariteit"] = index(n[f"{p}_nationale_solidariteit"], BASISJAAR_NS)
        n[f"{p}_toelagen_in_ns"] = a[f"{p}_aandeel_toelagen"] / n[f"{p}_nationale_solidariteit"]
        n[f"{p}_alternatieve_in_ns"] = a[f"{p}_aandeel_alternatieve"] / n[f"{p}_nationale_solidariteit"]
        # Controle: de vier aandelen moeten optellen tot 1
        som = a[[f"{p}_aandeel_{b}" for b in ("bijdragen", "toelagen", "alternatieve", "overige")]].sum(axis=1)
        assert (som - 1).abs().max() < 1e-9, f"aandelen {stelsel} tellen niet op tot 1"
    return n


# ===========================================================================
# 7. Periodes uit de tekst: correcte procentuele veranderingen
# ===========================================================================
# De periodes zoals ze in het werkboek berekend zijn. De tekst van het rapport
# gebruikt soms andere labels (bv. '2008-2009' voor wat 2007-2009 is berekend).
PERIODES_BS = [(2003, 2014), (2014, 2015), (2015, 2019), (2003, 2019), (2019, 2020), (2020, 2022),
               (2019, 2022), (2003, 2022), (2022, 2023), (2019, 2023), (2003, 2023)]
PERIODES_NS = [(2000, 2007), (2007, 2009), (2009, 2014), (2014, 2015), (2015, 2019), (2019, 2020),
               (2020, 2022), (2019, 2022), (2022, 2023), (2000, 2023), (2003, 2023)]


def perioden(bs: pd.DataFrame, ns: pd.DataFrame) -> pd.DataFrame:
    rijen = []
    cpi = bs[bs["deflator"] == "cpi"]
    for (stelsel, d), g in cpi.groupby(["stelsel", "definitie"]):
        wide = g.pivot(index="jaar", columns="reeks", values="waarde")
        for reeks, soort in (("bijdragen_pc_reeel", "bedrag"), ("uitgaven_pc_reeel", "bedrag"),
                             ("ratio_bijdragen_uitgaven", "ratio")):
            for b, e in PERIODES_BS:
                rijen.append({
                    "domein": "beroepssolidariteit", "stelsel": stelsel, "definitie": d, "reeks": reeks,
                    "periode": f"{b}-{e}", "begin": b, "eind": e,
                    "relatieve_verandering_pct": relatieve_verandering(wide[reeks], b, e),
                    "procentpunt_verschil": procentpunt_verschil(wide[reeks], b, e) if soort == "ratio" else None,
                })
    for stelsel, p in (("zelfstandigen", "z"), ("werknemers", "w")):
        for reeks in ("nationale_solidariteit", "aandeel_bijdragen", "aandeel_toelagen", "aandeel_alternatieve",
                      "aandeel_overige"):
            s = ns[f"{p}_{reeks}"]
            for b, e in PERIODES_NS:
                rijen.append({
                    "domein": "nationale_solidariteit", "stelsel": stelsel, "definitie": "", "reeks": reeks,
                    "periode": f"{b}-{e}", "begin": b, "eind": e,
                    "relatieve_verandering_pct": relatieve_verandering(s, b, e),
                    "procentpunt_verschil": procentpunt_verschil(s, b, e),
                })
    return pd.DataFrame(rijen)


def main() -> None:
    zorg_voor_mappen()
    ksz, rsvz = lees("ksz_populatie"), lees("rsvz_samenstelling")
    prijs, bedragen = lees("prijsindex"), lees("fodsz_bedragen")
    aandelen, nbb = lees("fodsz_aandelen"), lees("nbb_bijdragen")

    pop = populaties(ksz)
    sam = samenstelling(rsvz)
    bs = beroepssolidariteit(bedragen, pop, prijs)
    ven = vennootschappen(bedragen, pop, rsvz, prijs)
    wn = werknemers_opsplitsing(nbb, bedragen, pop, prijs)
    ns = nationale_solidariteit(aandelen)
    per = perioden(bs, ns)

    uit = {"populaties": pop, "samenstelling": sam, "vennootschappen": ven,
           "werknemers_opsplitsing": wn, "nationale_solidariteit": ns}
    for naam, df in uit.items():
        df.to_csv(DATA_PROCESSED / f"{naam}.csv", float_format="%.12g")
    # Enkel voor de reproductie van het oorspronkelijke werkboek (04_reconcile.py)
    nationale_solidariteit(aandelen, JAREN_NS_RECONCILIATIE).to_csv(
        DATA_PROCESSED / "nationale_solidariteit_reconciliatie.csv", float_format="%.12g")
    bs.to_csv(DATA_PROCESSED / "beroepssolidariteit.csv", index=False, float_format="%.12g")
    per.to_csv(DATA_PROCESSED / "perioden.csv", index=False, float_format="%.12g")
    print("indicatoren geschreven naar data/processed/")


if __name__ == "__main__":
    main()
