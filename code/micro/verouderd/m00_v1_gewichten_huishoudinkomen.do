*==============================================================================
* VEROUDERD (versie 1, 17 september 2026 om 13:57). Vervangen door
* code/micro/m00_kakwani_gewichten_besilc2024.do.
* Deze versie gebruikte het huishoudinkomen hy020 (niet gestandaardiseerd) en
* alle zelfstandigen/werknemers. Bewaard omdat data/raw/kakwani_gewichten_besilc2024.csv
* en .log ermee gemaakt zijn. Niet gebruikt in rapport of leesnota-voorstellen.
*==============================================================================

*==============================================================================
* UNIZO-rapport, microdeel: gewichten voor de Kakwani-index
* BE-SILC 2024 (inkomensjaar 2023)
* Doel: verdeling van het maandelijks netto beschikbaar inkomen over de
*       34 roosterposities van de microsimulaties (EUR 1.550 tot 15.000)
* Uitvoer: kakwani_gewichten_besilc2024.csv (+ beschrijvende cijfers in log)
*==============================================================================

version 19
clear all
set more off

* --- Paden en instellingen (aanpassen) ---------------------------------------
local silc   "PAD/NAAR/besilc2024.dta"
local unizo  "C:/Users/u0116193/KU Leuven/Julie Vinck - UNIZO/Micro niveau/unizo.dta"
local uit    "C:/Users/u0116193/Projects/Unizo/data/raw"
local gewicht pb040          // persoonsgewicht; vervang indien nodig door rb050

log using "`uit'/kakwani_gewichten_besilc2024.log", replace text

use "`silc'", clear

*------------------------------------------------------------------------------
* 1. Populaties
*------------------------------------------------------------------------------
* Zelfstandige: pl040a 1 = met personeel, 2 = zonder personeel
gen byte selfemp = inlist(pl040a, 1, 2)
replace  selfemp = . if missing(pl040a)

* Werknemer: pl040a 3
gen byte employee = (pl040a == 3) if !missing(pl040a)

* Alleenstaande: huishoudtype 5 (eenpersoonshuishouden)
gen byte single = (ht == 5) if !missing(ht)

*------------------------------------------------------------------------------
* 2. Maandelijks netto beschikbaar inkomen
*------------------------------------------------------------------------------
* hy020 is een jaarbedrag op huishoudniveau; negatieve inkomens op nul
* (zoals in het rapport, voetnoot 20)
gen double dpi_m = max(hy020, 0) / 12 if !missing(hy020)
label var dpi_m "Netto beschikbaar gezinsinkomen per maand (hy020/12)"

*------------------------------------------------------------------------------
* 3. Toewijzing aan de dichtstbijzijnde roosterpositie
*------------------------------------------------------------------------------
* Het rooster uit Unizo Results Final.xlsx:
local grid 1550 1800 2000 2250 2500 2750 3000 3250 3500 3750 4000 4250 ///
           4500 4750 5000 5250 5500 5750 6000 6250 6500 6750 7000 7500  ///
           8000 8500 9000 9500 10000 11000 12000 13000 14000 15000

* Voor elke persoon zoeken we de positie met de kleinste afstand.
* Zo loopt de grens tussen twee posities precies in het midden ertussen.
* (In Stata is elk getal kleiner dan missing, dus de eerste lus vult alles in.)
gen double afstand = .
gen int    pos     = .
foreach g of local grid {
    replace pos     = `g'              if abs(dpi_m - `g') < afstand & !missing(dpi_m)
    replace afstand = abs(dpi_m - `g') if abs(dpi_m - `g') < afstand & !missing(dpi_m)
}
drop afstand
label var pos "Dichtstbijzijnde roosterpositie (EUR per maand)"

* Randen apart markeren voor de gevoeligheidsanalyse
gen byte onder_rooster = dpi_m < 1550  if !missing(dpi_m)
gen byte boven_rooster = dpi_m > 15000 if !missing(dpi_m)

*------------------------------------------------------------------------------
* 4. Beschrijvende cijfers per groep (voor controle en voor de tekst)
*------------------------------------------------------------------------------
foreach grp in zs_alleen zs_alle wn_alleen wn_alle {
    preserve
    if "`grp'" == "zs_alleen" keep if selfemp  == 1 & single == 1
    if "`grp'" == "zs_alle"   keep if selfemp  == 1
    if "`grp'" == "wn_alleen" keep if employee == 1 & single == 1
    if "`grp'" == "wn_alle"   keep if employee == 1
    keep if !missing(dpi_m, `gewicht')

    display _n as result "=== `grp' ==="
    count
    display "Ongewogen n: " r(N)

    * Gewogen percentielen van het maandinkomen
    _pctile dpi_m [pw = `gewicht'], p(10 25 50 75 90 99)
    display "P10 " %8.0f r(r1) "  P25 " %8.0f r(r2) "  mediaan " %8.0f r(r3) ///
            "  P75 " %8.0f r(r4) "  P90 " %8.0f r(r5) "  P99 " %8.0f r(r6)

    * Gewogen gemiddelde en aandelen buiten het rooster
    summarize dpi_m [aw = `gewicht']
    display "Gemiddelde: " %8.0f r(mean)
    summarize onder_rooster [aw = `gewicht']
    display "Aandeel onder EUR 1.550: " %5.1f 100*r(mean) "%"
    summarize boven_rooster [aw = `gewicht']
    display "Aandeel boven EUR 15.000: " %5.1f 100*r(mean) "%"
    restore
}

*------------------------------------------------------------------------------
* 5. Gewichten per roosterpositie exporteren
*------------------------------------------------------------------------------
tempfile resultaat
local eerste 1
foreach grp in zs_alleen zs_alle wn_alleen wn_alle {
    preserve
    if "`grp'" == "zs_alleen" keep if selfemp  == 1 & single == 1
    if "`grp'" == "zs_alle"   keep if selfemp  == 1
    if "`grp'" == "wn_alleen" keep if employee == 1 & single == 1
    if "`grp'" == "wn_alle"   keep if employee == 1
    keep if !missing(pos, `gewicht')

    gen byte een = 1
    * w = som van de gewichten (populatie), n = ongewogen aantal waarnemingen
    collapse (sum) w = `gewicht' n = een, by(pos)
    egen double wtot = total(w)
    gen double aandeel = w / wtot            // gewogen aandeel per positie
    gen str10 groep = "`grp'"
    drop wtot

    if `eerste' == 0 append using `resultaat'
    save `resultaat', replace
    local eerste 0
    restore
}

use `resultaat', clear
order groep pos n w aandeel
sort groep pos
list, sepby(groep) noobs
export delimited using "`uit'/kakwani_gewichten_besilc2024.csv", replace delimiter(";")

*------------------------------------------------------------------------------
* 6. (Optioneel) Gewogen Kakwani-index meteen in Stata
*------------------------------------------------------------------------------
* Kakwani = concentratiecoefficient van de bijdragen - Gini van het inkomen,
* beide over de roosterposities, gewogen met het bevolkingsaandeel.
* De rang is de gewogen fractionele rang: het cumulatieve aandeel tot en met
* de vorige positie plus de helft van het eigen aandeel.
* C(v) = 2 * cov_w(v, R) / gemiddelde_w(v)

tempfile gew
save `gew', replace

use "`unizo'", clear
rename INKOMEN pos
tempfile bijdr
save `bijdr', replace

foreach grp in zs_alleen zs_alle {
    use `gew', clear
    keep if groep == "`grp'"
    merge 1:1 pos using `bijdr', keep(match using) nogenerate
    replace aandeel = 0 if missing(aandeel)  // posities zonder waarnemingen
    sort pos

    * Gewogen fractionele rang
    gen double cum = sum(aandeel)
    gen double R   = cum - aandeel/2

    display _n as result "=== Kakwani, gewogen met `grp' (werknemer met wn_" ///
            substr("`grp'", 4, .) ") ==="

    * Gini van het inkomen (roosterpositie)
    quietly {
        egen double mx = total(aandeel * pos)
        egen double mR = total(aandeel * R)
        egen double cx = total(aandeel * (pos - mx) * (R - mR))
    }
    local gini = 2 * cx[1] / mx[1]
    display "Gini rooster: " %6.3f `gini'

    foreach v in ZE ZV100VAA ZV100 ZV75 ZV50 ZV00 {
        quietly egen double m_`v' = total(aandeel * `v')
        quietly egen double c_`v' = total(aandeel * (`v' - m_`v') * (R - mR))
        local conc = 2 * c_`v'[1] / m_`v'[1]
        quietly egen double r_`v' = total(aandeel * `v' / pos)
        display %-10s "`v'" "  Kakwani " %6.3f (`conc' - `gini') ///
                "   gem. bijdrage/draagkracht " %5.1f 100*r_`v'[1] "%"
    }
}

* Werknemers met hun eigen verdeling
foreach grp in wn_alleen wn_alle {
    use `gew', clear
    keep if groep == "`grp'"
    merge 1:1 pos using `bijdr', keep(match using) nogenerate
    replace aandeel = 0 if missing(aandeel)
    sort pos
    gen double cum = sum(aandeel)
    gen double R   = cum - aandeel/2
    quietly {
        egen double mx = total(aandeel * pos)
        egen double mR = total(aandeel * R)
        egen double cx = total(aandeel * (pos - mx) * (R - mR))
        egen double m_WN = total(aandeel * WN)
        egen double c_WN = total(aandeel * (WN - m_WN) * (R - mR))
        egen double r_WN = total(aandeel * WN / pos)
    }
    local gini = 2 * cx[1] / mx[1]
    display _n as result "=== Werknemer, gewogen met `grp' ==="
    display "Gini rooster: " %6.3f `gini' "   Kakwani " ///
            %6.3f (2*c_WN[1]/m_WN[1] - `gini') ///
            "   gem. bijdrage/draagkracht " %5.1f 100*r_WN[1] "%"
}

log close
