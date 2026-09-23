"""
Metadata voor Zenodo afleiden uit CITATION.cff

Waarom?
-------
Bij elke GitHub-release haalt Zenodo de repository op en maakt er een archiefrecord van.
De metadata van dat record (titel, auteurs, samenvatting, licentie, versie) komt uit de
repository zelf, in deze volgorde van voorrang:

    .zenodo.json   >   CITATION.cff   >   LICENSE   >   de GitHub-gegevens

Van CITATION.cff leest Zenodo maar een handvol velden, en het kan er niet uit afleiden dat
dit een rapport is, welke versie het is, of naar welke repository het verwijst. Daarom maken
we een .zenodo.json. Om te vermijden dat twee bestanden hetzelfde zeggen en na verloop van
tijd uit elkaar lopen, typen we niets twee keer: dit script LEEST CITATION.cff en SCHRIJFT
.zenodo.json. CITATION.cff blijft dus de enige plaats waar je iets aanpast.

Wat je waar aanpast
-------------------
  titel, auteurs, samenvatting, trefwoorden, licentie, versie, datum, repo-URL
                                                   -> CITATION.cff
  soort record (rapport, software, dataset)        -> SOORT hieronder
  het DOI                                          -> CITATION.cff (regel `doi:`), maar pas
                                                      nadat Zenodo het bij de eerste release
                                                      heeft aangemaakt; zie README

Uitvoer
-------
  .zenodo.json    wordt meegepubliceerd en door Zenodo gelezen bij elke release

Uitvoeren:  python code/tekst/zenodo_metadata.py
            (draait ook mee in code/run_all.py)
"""

import json
import sys
from pathlib import Path

import yaml

WORTEL = Path(__file__).resolve().parents[2]
CITATIE = WORTEL / "CITATION.cff"
UIT = WORTEL / ".zenodo.json"

# ---------------------------------------------------------------------------
# Soort record. Zenodo kent onder meer:
#   ("publication", "report")   een rapport, met de code en data als bijlage
#   ("software", None)          een softwarepakket
#   ("dataset", None)           een gegevensverzameling
# We kiezen 'report': het DOI staat in het colofon van het rapport en wordt als rapport
# geciteerd. De code en de gegevens zitten in hetzelfde record.
# ---------------------------------------------------------------------------
SOORT = ("publication", "report")

TAAL = "nld"                      # Nederlands, ISO 639-3
TOEGANG = "open"


def naam(auteur):
    """Zenodo wil 'Achternaam, Voornaam' in één veld."""
    return f"{auteur['family-names']}, {auteur['given-names']}"


def main():
    if not CITATIE.exists():
        print(f"{CITATIE.name} niet gevonden: .zenodo.json niet aangemaakt.")
        return 1
    cff = yaml.safe_load(CITATIE.read_text(encoding="utf-8"))

    creators = []
    for a in cff.get("authors", []):
        c = {"name": naam(a)}
        if a.get("affiliation"):
            c["affiliation"] = a["affiliation"]
        if a.get("orcid"):
            # Zenodo wil het kale nummer, niet de volledige URL
            c["orcid"] = a["orcid"].rsplit("/", 1)[-1]
        creators.append(c)

    meta = {
        "title": cff["title"],
        "description": " ".join(cff.get("abstract", "").split()),
        "creators": creators,
        "upload_type": SOORT[0],
        "access_right": TOEGANG,
        "license": cff.get("license", "").lower(),   # Zenodo gebruikt kleine letters: cc-by-4.0
        "language": TAAL,
        "keywords": cff.get("keywords", []),
    }
    if SOORT[1]:
        meta["publication_type"] = SOORT[1]
    if cff.get("version"):
        meta["version"] = str(cff["version"])
    if cff.get("date-released"):
        meta["publication_date"] = str(cff["date-released"])

    # Verwijzing naar de repository zelf. Zonder ingevulde URL laten we het veld weg,
    # zodat er geen plaatshouder in het Zenodo-record terechtkomt.
    repo = str(cff.get("repository-code", ""))
    if repo and "VUL-IN" not in repo:
        meta["related_identifiers"] = [
            {"identifier": repo, "relation": "isSupplementTo", "scheme": "url"}
        ]

    UIT.write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # <!-- wijziging: publicatie | controle dat het DOI overal hetzelfde is -->
    # Het DOI staat op twee plaatsen: in CITATION.cff (waaruit de lopende tekst het via de
    # sleutel {{doi}} haalt) en met de hand in het colofon van rapport.qmd. Dat colofon is
    # YAML-metadata die Quarto zelf leest, dus het kan niet ingevuld worden met een
    # plaatshouder. Hier controleren we dat de twee niet uit elkaar lopen.
    doi = str(cff.get("doi", "")).strip()
    qmd = (WORTEL / "rapport.qmd")
    if qmd.exists():
        colofon = qmd.read_text(encoding="utf-8")
        if doi and doi not in colofon:
            print(f"LET OP: CITATION.cff heeft doi {doi}, maar dat staat niet in het colofon "
                  f"van rapport.qmd. Pas het colofon aan.")
        if not doi and "VUL-IN-DOI" not in colofon:
            print("LET OP: CITATION.cff heeft nog geen doi, maar het colofon van rapport.qmd "
                  "bevat ook geen VUL-IN-DOI. Controleer welk nummer daar staat.")
        if doi and "VUL-IN-DOI" in colofon:
            print("LET OP: het colofon van rapport.qmd bevat nog VUL-IN-DOI terwijl "
                  f"CITATION.cff al doi {doi} heeft.")
    ontbreekt = [v for v in ("version", "publication_date") if v not in meta]
    print(f"geschreven: .zenodo.json ({meta['upload_type']}"
          f"{'/' + meta['publication_type'] if SOORT[1] else ''}, versie "
          f"{meta.get('version', 'niet gezet')})")
    if ontbreekt:
        print(f"LET OP: {', '.join(ontbreekt)} ontbreekt in CITATION.cff")
    if not repo or "VUL-IN" in repo:
        print("LET OP: repository-code in CITATION.cff staat nog op VUL-IN")
    return 0


if __name__ == "__main__":
    sys.exit(main())
