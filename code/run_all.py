"""
Draai de volledige analyse (macro en micro) van begin tot einde.

    python code/run_all.py

Volgorde:
  MACRO (code/macro/)
  01 inputs overnemen uit het werkboek     -> data/raw/
  02 inputs controleren tegen de bronnen    -> output/checks/bronverificatie.csv
  03 indicatoren berekenen                  -> data/processed/
  03b scenario rechtsvorm (eenmanszaak)     -> data/processed/scenario_rechtsvorm*.csv
  04 vergelijken met werkboek en concepttekst  -> output/checks/ (enkel intern, zie DATA.md)
  05 figuren                                -> output/figures/
  06 Excel met alles samen                  -> output/tables/

  MICRO (code/micro/, zie code/micro/LEESMIJ.md)
  m00 gewichten BE-SILC 2024 (Stata)        NIET hier: handmatig in Stata, schrijft naar data/raw/
  m01 Kakwani gewogen naar BE-SILC          -> data/processed/micro_kakwani_besilc2024.csv, controle Python = Stata
  m02 Kakwani gewogen naar ADI 2023         -> data/processed/micro_kakwani_adi2023.csv (enkel met data/restricted/)
  m03 scenario's bijdrageschaal eenmanszaak -> data/processed/micro_schaal_*.csv
  m04 opbrengst ingrepen top (ABC-tabel 7)  -> data/processed/abc_opbrengst_statisch.csv
  m05 indicatoren §6.2 uit het werkboek     -> data/raw/micro_werkboek_invoer.csv, data/processed/micro_indicatoren.csv,
                                               micro_samenvatting.csv, micro_tabellen.csv, controle in output/checks/
  m06 figuren microdeel (Fig. 8-11, B7.1-3) -> output/figures/

  TEKST
  controle_tabel7 bedragen Tabel 7 vs werkboek -> output/checks/tabel7_bedragen.csv
  07 cijfers in de tekst invullen           -> report/sections/
  figuurbronnen bron bij elke figuur        -> output/figures/BRONNEN.md, bronnen.csv
  zenodo_metadata metadata voor Zenodo      -> .zenodo.json (uit CITATION.cff)
  08 rapport opmaken (als Quarto geïnstalleerd is) -> output/rapport/rapport.pdf

Stopt bij de eerste fout. Stappen waarvan de afgeschermde brondata ontbreekt (het
Viren/EUROMOD-werkboek, het ADI-histogram, de Stata-uitvoer op BE-SILC) vertrekken van de
meegeleverde CSV-afgeleiden of slaan zichzelf over met een melding. Zie DATA.md: zonder die
brondata komt er exact dezelfde uitvoer uit, op afrondingsruis in de laatste bit na.
"""

import runpy
import shutil
import subprocess
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parent
MACRO = CODE / "macro"
MICRO = CODE / "micro"


def draai(map_, stappen):
    """Draai de scripts in map_ na elkaar, met map_ op het importpad."""
    # zodat 'from common import ...' (macro) en 'from common_micro import ...' (micro) werken
    sys.path.insert(0, str(map_))
    for stap in stappen:
        print(f"\n===== {map_.name}/{stap} =====")
        try:
            runpy.run_path(str(map_ / stap), run_name="__main__")
        except SystemExit as e:          # een stap die zichzelf overslaat (code 0) stopt de rest niet
            if e.code not in (0, None):
                raise
    sys.path.remove(str(map_))


# <!-- wijziging: publicatie | stap 04 vergelijkt met het oude werkboek en de conceptversie van het
# rapport. Die vergelijking hoort bij de interne kwaliteitscontrole en staat niet in de publieke
# repository (beslissing Wim, 23 september 2026), dus we draaien ze enkel als het script aanwezig is. -->
macro_stappen = ["01_extract_raw.py", "02_verify_sources.py", "03_indicators.py", "03b_scenario_rechtsvorm.py"]
if (MACRO / "04_reconcile.py").exists():
    macro_stappen.append("04_reconcile.py")
else:
    print("\n===== macro/04_reconcile.py =====\nniet aanwezig (interne controlestap): overgeslagen.")
macro_stappen += ["05_figures.py", "06_excel.py"]
draai(MACRO, macro_stappen)

# m02 vóór m03: m03 gebruikt de ADI-gewichten als die bestaan
draai(MICRO, ["m01_kakwani_besilc.py", "m02_kakwani_adi2023.py", "m03_scenario_bijdrageschaal.py",
              "m04_abc_opbrengst.py", "m05_werkboek_indicatoren.py", "m06_figuren.py"])

# wijziging: nieuw | 22 september 2026, leesnota J6: de bedragen van Tabel 7 worden cel per cel
# met het werkboek vergeleken. Het script stopt de pijplijn niet, het meldt enkel verschillen.
draai(CODE / "tekst", ["controle_tabel7.py"])

draai(MACRO, ["07_tekstcijfers.py"])

# <!-- wijziging: publicatie | bronvermelding naast de downloadbare figuren, en de
# Zenodo-metadata uit CITATION.cff -->
# Na 07: de onderschriften staan pas dan ingevuld in report/sections/.
draai(CODE / "tekst", ["figuurbronnen.py", "zenodo_metadata.py"])

# 08: PDF opmaken. Quarto is een apart programma (geen Python-pakket); ontbreekt het,
# dan slaan we deze stap over in plaats van te stoppen.
print("\n===== 08 rapport (Quarto) =====")
if shutil.which("quarto"):
    subprocess.run(["quarto", "render"], cwd=CODE.parent, check=True)
else:
    print("Quarto niet gevonden: PDF niet opgemaakt (zie report/LEESMIJ.md).")

print("\nKlaar.")
