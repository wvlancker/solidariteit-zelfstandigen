"""
Controle vóór het publiceren: wat gaat er mee naar GitHub, en wat blijft achter?

Waarom?
-------
De repository bevat naast eigen werk ook brondata die we niet mogen doorgeven
(Viren/EUROMOD-werkboek, Statbel ADI-histogram, BE-SILC-uitvoer met celaantallen).
Die staan in .gitignore, maar een regel in .gitignore werkt niet meer zodra een bestand
ooit in een commit zat. Dit script toont daarom, los van Git:

  1. welke bestanden gepubliceerd zouden worden (alles wat .gitignore niet uitsluit),
  2. of elk bestand uit de afgeschermde lijst effectief uitgesloten is,
  3. of Git die bestanden misschien al volgt (dan is `git rm --cached` nodig),
  4. hoe groot de publieke repository wordt.

Het script wijzigt niets. Het eindigt met afsluitcode 1 als er iets fout zit.

Uitvoeren:  python code/publicatie_check.py
            python code/publicatie_check.py --lijst    (volledige bestandslijst)
"""

import subprocess
import sys
from pathlib import Path

WORTEL = Path(__file__).resolve().parents[1]

# ---------------------------------------------------------------------------
# Bestanden en mappen die NOOIT gepubliceerd mogen worden (zie DATA.md).
# Elk patroon is relatief t.o.v. de projectmap en wordt met Path.glob getest.
# ---------------------------------------------------------------------------
AFGESCHERMD = [
    ("data/restricted/**/*", "Statbel ADI-histogram 2023 (microdata-afgeleide, niet herverdeelbaar)"),
    ("data/sources/micro/unizo_results_final.xlsx", "Viren/EUROMOD-werkboek met de simulaties"),
    ("data/sources/micro/correctie_pensioenen.xlsx", "Viren-correctieblad pensioenen"),
    ("data/sources/abc/*.pdf", "ABC-verslag 2022/04, publicatie van derden"),
    ("data/raw/kakwani_gewichten_besilc2024.csv", "BE-SILC-gewichten met aantal waarnemingen per cel"),
    ("data/raw/kakwani_gewichten_eq_besilc2024.csv", "BE-SILC-gewichten met aantal waarnemingen per cel"),
    ("data/raw/*.log", "Stata-logs met tussenuitvoer op BE-SILC"),
    ("archive/**/*", "archief van de oorspronkelijke projectmap"),
    ("report/import/**/*", "omzetting van de Word-versie, werkdocument"),
    ("output/tekst/**/*", "tekstvergelijkingen en leesversies voor de auteurs"),
    ("CLAUDE.md", "werkafspraken met de assistent"),
    ("ERRATA.md", "interne errata op het oude werkboek en de conceptversie van het rapport"),
    ("code/macro/04_reconcile.py", "vergelijking met het oude werkboek en de conceptcijfers"),
    ("output/checks/rapportcijfers.csv", "cijfers uit de conceptversie van het rapport"),
    ("output/checks/reconciliatie_werkboek.csv", "waarden uit het oude werkboek"),
    ("Claude outputs/**/*", "losse bestanden in de projectmap (oudere PDF's, notities, media)"),
]

# ---------------------------------------------------------------------------
# Bestanden die er WEL bij moeten zijn: zonder deze is het rapport niet
# reproduceerbaar zodra de afgeschermde brondata ontbreekt.
# ---------------------------------------------------------------------------
VERPLICHT = [
    "data/sources/micro/unizo.dta",
    "data/raw/micro_werkboek_invoer.csv",
    "data/raw/micro_pensioenen_correctie.csv",
    "data/raw/micro_schaal_invoer.csv",
    "data/raw/micro_silc_gewichten.csv",
    "data/raw/micro_silc_groepen.csv",
    "data/raw/micro_adi_gewichten.csv",
    "data/raw/kakwani_resultaten_eq_besilc2024.csv",
    "output/tables/figuurdata/fig03_inkomensverdeling.csv",
    "data/raw/codebook.csv",
    "data/sources/MANIFEST.csv",
    "DATA.md",
    "LICENSE",
    "LICENSE-tekst-en-figuren",
    "CITATION.cff",
    ".zenodo.json",
    "CHANGELOG.md",
    "README.md",
]


def git(*args):
    """Draai een git-commando in de projectmap; geeft (gelukt, uitvoer)."""
    try:
        r = subprocess.run(["git", *args], cwd=WORTEL, capture_output=True, text=True)
    except FileNotFoundError:
        return False, "git niet gevonden"
    return r.returncode == 0, r.stdout


def genegeerd(paden):
    """Welke van deze paden sluit .gitignore uit? Geeft een set met relatieve paden.

    `git check-ignore` leest .gitignore zelf, dus we hoeven de regels niet na te bouwen.

    Twee vlaggen zijn hier essentieel:

    `--no-index`: zonder die vlag zwijgt check-ignore over bestanden die al in de index
    staan. Na een `git add -A` zou het dan lijken alsof .gitignore niets uitsluit, terwijl
    de regels wel degelijk kloppen. Met `--no-index` kijken we puur naar de regels; of Git
    een uitgesloten bestand toch al volgt, controleren we apart met `git ls-files`.

    `-z`: de paden gaan als NUL-gescheiden BYTES naar git, en komen zo ook terug. Met
    gewone tekst zou Python op Windows elke \\n naar \\r\\n vertalen, waardoor git paden
    met een \\r erachter krijgt die met geen enkel bestand overeenkomen: het script meldde
    dan dat niets uitgesloten is. NUL-scheiding voorkomt ook het aanhalingstekengedoe dat
    git anders bij accenten en spaties in bestandsnamen toepast.

    Geeft None als er geen Git-repository is of Git niet geïnstalleerd is.
    """
    if not paden:
        return set()
    invoer = b"\0".join(p.encode("utf-8") for p in paden) + b"\0"
    try:
        r = subprocess.run(["git", "check-ignore", "--no-index", "-z", "--stdin"], cwd=WORTEL,
                           input=invoer, capture_output=True)   # bewust GEEN text=True
    except FileNotFoundError:
        return None
    if r.returncode not in (0, 1):     # 0 = minstens één genegeerd, 1 = geen enkel, 128 = geen repo
        return None
    return {p.decode("utf-8").replace("\\", "/") for p in r.stdout.split(b"\0") if p}


def alle_bestanden():
    """Alle bestanden in de projectmap, relatief, zonder .git zelf."""
    uit = []
    for p in WORTEL.rglob("*"):
        if p.is_file() and ".git/" not in p.as_posix().replace("\\", "/") + "/":
            rel = p.relative_to(WORTEL).as_posix()
            if not rel.startswith(".git/"):
                uit.append(rel)
    return sorted(uit)


def main(toon_lijst=False):
    fouten = []
    bestanden = alle_bestanden()
    uitgesloten = genegeerd(bestanden)
    if uitgesloten is None:
        print("Git kon .gitignore niet lezen: controle overgeslagen.")
        print("Meestal betekent dat: er is hier nog geen Git-repository. Doe eerst `git init -b main`.")
        return 1
    publiek = [b for b in bestanden if b not in uitgesloten]

    # 1. Staat elk afgeschermd bestand effectief buiten de publicatie?
    print("Afgeschermd (mag niet mee)")
    for patroon, waarom in AFGESCHERMD:
        treffers = sorted(p.relative_to(WORTEL).as_posix() for p in WORTEL.glob(patroon) if p.is_file())
        if not treffers:
            print(f"  -  {patroon:<52} niet aanwezig in deze werkkopie")
            continue
        lek = [t for t in treffers if t not in uitgesloten]
        if lek:
            print(f"  X  {patroon:<52} {len(lek)} bestand(en) NIET uitgesloten: {', '.join(lek[:3])}")
            fouten.append(f"{patroon} wordt niet uitgesloten door .gitignore")
        else:
            print(f"  ok {patroon:<52} {len(treffers)} bestand(en) uitgesloten  ({waarom})")

    # 2. Volgt Git die bestanden misschien al uit een eerdere commit?
    gelukt, gevolgd = git("ls-files")
    if gelukt:
        gevolgd = set(gevolgd.split())
        al_gevolgd = sorted(gevolgd & uitgesloten)
        if al_gevolgd:
            print("\nLET OP: Git volgt deze uitgesloten bestanden al. Haal ze uit de index met")
            print("        git rm --cached <bestand>   (het bestand zelf blijft op de schijf staan)")
            for b in al_gevolgd:
                print(f"  X  {b}")
            fouten.append(f"{len(al_gevolgd)} uitgesloten bestand(en) staan al in de Git-index")
    else:
        print("\n(nog geen Git-repository: de index kon niet gecontroleerd worden)")

    # 3. Is alles aanwezig wat nodig is om zonder brondata te reproduceren?
    print("\nNodig voor reproductie zonder brondata")
    for b in VERPLICHT:
        pad = WORTEL / b
        if not pad.exists():
            print(f"  X  {b:<55} ONTBREEKT")
            fouten.append(f"{b} ontbreekt")
        elif b in uitgesloten:
            print(f"  X  {b:<55} wordt uitgesloten door .gitignore")
            fouten.append(f"{b} wordt uitgesloten maar is nodig")
        else:
            print(f"  ok {b:<55} {pad.stat().st_size / 1024:>8,.0f} kB")

    # 4. Omvang van de publieke repository
    bytes_totaal = sum((WORTEL / b).stat().st_size for b in publiek)
    print(f"\nPubliek: {len(publiek)} bestanden, {bytes_totaal / 1024 / 1024:.1f} MB "
          f"({len(bestanden) - len(publiek)} bestanden uitgesloten)")
    per_map = {}
    for b in publiek:
        top = b.split("/")[0] if "/" in b else "(wortel)"
        per_map[top] = per_map.get(top, 0) + (WORTEL / b).stat().st_size
    for map_, n in sorted(per_map.items(), key=lambda x: -x[1]):
        print(f"  {map_:<24} {n / 1024 / 1024:>7.1f} MB")

    if toon_lijst:
        print("\nVolledige lijst van publieke bestanden:")
        for b in publiek:
            print(f"  {b}")

    if fouten:
        print(f"\n{len(fouten)} probleem(en):")
        for f in fouten:
            print(f"  - {f}")
        return 1
    print("\nGeen problemen gevonden.")
    return 0


if __name__ == "__main__":
    sys.exit(main(toon_lijst="--lijst" in sys.argv))
