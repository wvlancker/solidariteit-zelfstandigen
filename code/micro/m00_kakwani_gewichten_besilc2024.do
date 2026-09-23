*==============================================================================
* DOCUMENTATIE (toegevoegd bij opname in de repository, 17 september 2026)
*
* Stap m00 van het microdeel. Draait in Stata 19, NIET via run_all.py: de
* BE-SILC-microdata zijn niet publiek en staan niet in de repository.
* Dit is exact de versie die op 17 september 2026 om 14:12 gedraaid heeft
* (log: data/raw/kakwani_eq_besilc2024.log; elke commandoregel vanaf deel 0
* staat in die log). Enkel dit documentatieblok is erbij gekomen.
*
* Opnieuw draaien:
*   1. Zet in `silc' het pad naar het BE-SILC 2024-bestand (met pb040, hy020,
*      eq_ss, eq_inc20, pl040a, ht).
*   2. `unizo' mag ook naar de kopie in de repository wijzen:
*      C:/Users/u0116193/Projects/Unizo/data/sources/micro/unizo.dta
*   3. do code/micro/m00_kakwani_gewichten_besilc2024.do
*   4. python code/run_all.py  (m01 controleert dat Python dezelfde Kakwani-
*      indices vindt als Stata en rekent alles verder door)
*
* Uitvoer in data/raw/: kakwani_gewichten_eq_besilc2024.csv,
* kakwani_resultaten_eq_besilc2024.csv, kakwani_eq_besilc2024.log.
* Het gewichtenbestand bevat ongewogen aantallen per cel (soms n = 1): zie
* code/micro/LEESMIJ.md over delen buiten het projectteam.
*==============================================================================

*==============================================================================
* UNIZO-rapport, microdeel: gewichten voor de Kakwani-index, versie 2
* BE-SILC 2024 (inkomensjaar 2023), gestandaardiseerd netto beschikbaar inkomen
* Groepen zoals de typegevallen: alleenstaanden en koppels met kinderen
*
* Varianten van het inkomen op het rooster:
*   A  gestandaardiseerd inkomen rechtstreeks (levensstandaard)
*   B  omgerekend naar het individuele inkomen van de zelfstandige in het
*      typegeval: koppel met kinderen = eq. inkomen x 2,1 - partnerloon (laag)
*      - Groeipakket; alleenstaande = eq. inkomen          (hoofdvariant)
*   C  idem B met gemiddeld partnerloon
*
* Uitvoer (in `uit'):
*   kakwani_gewichten_eq_besilc2024.csv   gewicht per roosterpositie
*   kakwani_resultaten_eq_besilc2024.csv  Gini, Kakwani, gem. bijdrage/draagkracht
*   kakwani_eq_besilc2024.log
*==============================================================================

version 19
clear all
set more off

* --- Paden en instellingen (aanpassen) ---------------------------------------
local silc     "PAD/NAAR/besilc2024.dta"
local unizo    "C:/Users/u0116193/KU Leuven/Julie Vinck - UNIZO/Micro niveau/unizo.dta"
local uit      "C:/Users/u0116193/Projects/Unizo/data/raw"
local gewicht  pb040       // persoonsgewicht
local eqschaal eq_ss       // equivalized size
local eqink    eq_inc20    // equivalized income (jaarbedrag)

* --- Parameters van de typegevallen (Unizo Results Final.xlsx) ---------------
local partner_laag 2431.41   // netto loon partner, laag loon (67% gemiddeld loon)
local partner_gem  3092.99   // netto loon partner, gemiddeld loon
local groeipakket  368.96    // Groeipakket 2 kinderen (2 en 4 jaar)
local schaal_typ   2.1       // 1 + 0,5 + 0,3 + 0,3: twee volwassenen, twee kinderen <14

capture log close
log using "`uit'/kakwani_eq_besilc2024.log", replace text

*==============================================================================
* 0. Hulpprogramma's
*==============================================================================

*--- 0a. Inkomen toewijzen aan de dichtstbijzijnde roosterpositie -------------
*    De grens tussen twee posities ligt zo precies in het midden ertussen.
capture program drop naarrooster
program define naarrooster
    args invar uitvar
    local grid 1550 1800 2000 2250 2500 2750 3000 3250 3500 3750 4000 4250 ///
               4500 4750 5000 5250 5500 5750 6000 6250 6500 6750 7000 7500  ///
               8000 8500 9000 9500 10000 11000 12000 13000 14000 15000
    tempvar afst
    quietly gen double `afst' = .
    quietly gen int `uitvar' = .
    foreach g of local grid {
        * (in Stata is elk getal kleiner dan missing, dus de eerste positie vult alles in)
        quietly replace `uitvar' = `g'                if abs(`invar' - `g') < `afst' & !missing(`invar')
        quietly replace `afst'   = abs(`invar' - `g') if abs(`invar' - `g') < `afst' & !missing(`invar')
    }
end

*--- 0b. Groep selecteren ------------------------------------------------------
*    grp = zs_... (zelfstandigen) of wn_... (werknemers), gevolgd door
*    typ (alleenstaanden + koppels met kinderen), alleen, koppel, koppel2
capture program drop kiesgroep
program define kiesgroep
    args grp
    if substr("`grp'", 1, 2) == "zs" local st selfemp
    else                              local st employee
    local hh = substr("`grp'", 4, .)
    if "`hh'" == "typ"     keep if `st' == 1 & (hh_alleen == 1 | hh_koppelkind == 1)
    if "`hh'" == "alleen"  keep if `st' == 1 & hh_alleen == 1
    if "`hh'" == "koppel"  keep if `st' == 1 & hh_koppelkind == 1
    if "`hh'" == "koppel2" keep if `st' == 1 & hh_koppel2 == 1
end

*--- 0c. Gewogen Kakwani-index over de 34 roosterposities ----------------------
*    Verwacht in geheugen: 34 rijen met pos, aandeel (som = 1) en bijdragen.
*    R = gewogen fractionele rang (cumulatief aandeel tot vorige positie
*        + helft eigen aandeel)
*    C(v) = 2 * som[aandeel * (v - gem_v) * (R - gem_R)] / gem_v
*    Kakwani = C(bijdrage) - Gini(roosterinkomen)
capture program drop kakwani_tabel
program define kakwani_tabel
    syntax varlist, variant(string) groep(string) handle(string)
    sort pos
    tempvar cum R t
    quietly gen double `cum' = sum(aandeel)
    quietly gen double `R'   = `cum' - aandeel/2
    quietly gen double `t'   = .

    * Gini van het roosterinkomen
    quietly replace `t' = aandeel * pos
    quietly summarize `t', meanonly
    scalar sc_mx = r(sum)
    quietly replace `t' = aandeel * `R'
    quietly summarize `t', meanonly
    scalar sc_mR = r(sum)
    quietly replace `t' = aandeel * (pos - sc_mx) * (`R' - sc_mR)
    quietly summarize `t', meanonly
    scalar sc_gini = 2 * r(sum) / sc_mx

    foreach v of local varlist {
        quietly replace `t' = aandeel * `v'
        quietly summarize `t', meanonly
        scalar sc_mv = r(sum)
        quietly replace `t' = aandeel * (`v' - sc_mv) * (`R' - sc_mR)
        quietly summarize `t', meanonly
        scalar sc_kak = 2 * r(sum) / sc_mv - sc_gini
        * gewogen gemiddelde verhouding bijdrage / draagkracht
        quietly replace `t' = aandeel * `v' / pos
        quietly summarize `t', meanonly
        scalar sc_ratio = r(sum)
        post `handle' ("`variant'") ("`groep'") ("`v'") (sc_gini) (sc_kak) (sc_ratio)
        display %-3s "`variant'" %-12s "`groep'" %-10s "`v'" ///
                "  Gini " %6.3f sc_gini "  Kakwani " %6.3f sc_kak ///
                "  bijdrage/draagkracht " %5.1f 100*sc_ratio "%"
    }
end

*==============================================================================
* 1. Data en populaties
*==============================================================================
use "`silc'", clear

* Huishoudcodes nakijken (EU-SILC HX060: 5 = eenpersoonshuishouden,
* 10/11/12 = twee volwassenen met 1, 2, 3+ kinderen ten laste)
tab ht, missing

* Zelfstandige: pl040a 1 = met personeel, 2 = zonder personeel
gen byte selfemp = inlist(pl040a, 1, 2)
replace  selfemp = . if missing(pl040a)
* Werknemer: pl040a 3
gen byte employee = (pl040a == 3) if !missing(pl040a)

gen byte hh_alleen     = (ht == 5)              if !missing(ht)
gen byte hh_koppelkind = inlist(ht, 10, 11, 12) if !missing(ht)
gen byte hh_koppel2    = (ht == 11)             if !missing(ht)

*==============================================================================
* 2. Inkomensbegrippen
*==============================================================================

*--- 2a. Controles op eq_inc20 en eq_ss ---------------------------------------
* (a) eq_inc20 moet gelijk zijn aan hy020 / eq_ss (jaarbedrag)
gen double eq_check    = hy020 / `eqschaal' if !missing(hy020, `eqschaal')
gen double eq_verschil = `eqink' - eq_check
summarize `eqink' eq_check eq_verschil
quietly summarize eq_verschil
display "Maximale absolute afwijking eq_inc20 - hy020/eq_ss: " ///
        %9.2f max(abs(r(min)), abs(r(max)))
* Stopt als de afwijking groter is dan 1 euro per jaar
assert abs(eq_verschil) < 1 if !missing(eq_verschil)

* (b) eq_ss per huishoudtype: verwacht 1 bij ht==5, 2,1 bij ht==11 met jonge kinderen
tabstat `eqschaal', by(ht) statistics(min p50 max) nototal
assert `eqschaal' == 1 if ht == 5 & !missing(`eqschaal')

*--- 2b. Maandbedragen ---------------------------------------------------------
* Gestandaardiseerd maandinkomen, negatieve inkomens op nul
gen double eq_m = max(`eqink', 0) / 12 if !missing(`eqink')
label var eq_m "Gestandaardiseerd netto beschikbaar inkomen per maand (eq_inc20/12)"

* A: gestandaardiseerd inkomen rechtstreeks
gen double y_A = eq_m

* B: individueel inkomen van de zelfstandige in het typegeval, laag partnerloon
*    koppel met kinderen: gezinsinkomen van een 2+2-gezin met hetzelfde
*    gestandaardiseerde inkomen, min partnerloon en Groeipakket
gen double y_B = eq_m if hh_alleen == 1
replace    y_B = max(eq_m * `schaal_typ' - `partner_laag' - `groeipakket', 0) if hh_koppelkind == 1

* C: idem met gemiddeld partnerloon
gen double y_C = eq_m if hh_alleen == 1
replace    y_C = max(eq_m * `schaal_typ' - `partner_gem' - `groeipakket', 0) if hh_koppelkind == 1

* Roosterpositie en randen per variant
foreach c in A B C {
    naarrooster y_`c' pos_`c'
    gen byte onder_`c' = y_`c' < 1550  if !missing(y_`c')
    gen byte boven_`c' = y_`c' > 15000 if !missing(y_`c')
}

*==============================================================================
* 3. Beschrijvende cijfers per groep en variant
*==============================================================================
local groepen zs_typ zs_alleen zs_koppel zs_koppel2 wn_typ wn_alleen wn_koppel wn_koppel2

foreach grp of local groepen {
    foreach c in A B C {
        preserve
        kiesgroep `grp'
        keep if !missing(y_`c', `gewicht')
        quietly count
        local n = r(N)
        if `n' > 0 {
            _pctile y_`c' [pw = `gewicht'], p(10 50 90)
            local p10 = r(r1)
            local p50 = r(r2)
            local p90 = r(r3)
            quietly summarize onder_`c' [aw = `gewicht']
            local ond = 100 * r(mean)
            quietly summarize boven_`c' [aw = `gewicht']
            local bov = 100 * r(mean)
            display as result %-12s "`grp'" " variant `c'" as text ///
                "  n " %5.0f `n' "  P10 " %6.0f `p10' "  mediaan " %6.0f `p50' ///
                "  P90 " %6.0f `p90' "  <1550 " %4.1f `ond' "%  >15000 " %4.1f `bov' "%"
        }
        restore
    }
}

*==============================================================================
* 4. Gewichten per roosterpositie
*==============================================================================
tempfile resultaat
local eerste 1
foreach grp of local groepen {
    foreach c in A B C {
        preserve
        kiesgroep `grp'
        keep if !missing(pos_`c', `gewicht')
        gen byte een = 1
        * w = som van de gewichten, n = ongewogen aantal waarnemingen
        collapse (sum) w = `gewicht' n = een, by(pos_`c')
        rename pos_`c' pos
        egen double wtot = total(w)
        gen double aandeel = w / wtot
        drop wtot
        gen str12 groep   = "`grp'"
        gen str1  variant = "`c'"
        if `eerste' == 0 append using `resultaat'
        save `resultaat', replace
        local eerste 0
        restore
    }
}
use `resultaat', clear
order variant groep pos n w aandeel
sort variant groep pos
export delimited using "`uit'/kakwani_gewichten_eq_besilc2024.csv", replace delimiter(";")
tempfile gew
save `gew', replace

*==============================================================================
* 5. Kakwani-indices
*==============================================================================
use "`unizo'", clear
rename INKOMEN pos
tempfile bijdr
save `bijdr', replace

tempname ph
tempfile kak
postfile `ph' str1 variant str12 groep str10 type double(gini kakwani ratio) using `kak', replace

* Controle: gelijke gewichten reproduceren het rapport (ZE -0,159; WN 0,072)
use `bijdr', clear
gen double aandeel = 1/34
kakwani_tabel ZE ZV100VAA ZV100 ZV75 ZV50 ZV00 WN, variant("-") groep("rapport") handle(`ph')

foreach c in A B C {
    foreach grp of local groepen {
        use `gew', clear
        keep if variant == "`c'" & groep == "`grp'"
        merge 1:1 pos using `bijdr', keep(match using) nogenerate
        replace aandeel = 0 if missing(aandeel)       // posities zonder waarnemingen
        if substr("`grp'", 1, 2) == "zs" {
            kakwani_tabel ZE ZV100VAA ZV100 ZV75 ZV50 ZV00, variant("`c'") groep("`grp'") handle(`ph')
        }
        else {
            kakwani_tabel WN, variant("`c'") groep("`grp'") handle(`ph')
        }
    }
}
postclose `ph'

use `kak', clear
export delimited using "`uit'/kakwani_resultaten_eq_besilc2024.csv", replace delimiter(";")

log close
