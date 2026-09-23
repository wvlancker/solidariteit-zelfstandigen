--[[
tabellen.lua: zet de tabelconventie uit report/sections/*.md om naar één tabelblok.

In de markdown ziet een tabel er zo uit (zoals in CLAUDE.md afgesproken):

    **Tabel 9.** Horizontale solidariteit: equivalentiegraad ...
    | | **X̅** | **VC** |
    |---|---:|---:|
    | Werknemer | 78% | 0,68 |
    Noot: X̅ = gemiddelde over de gesimuleerde inkomensposities ...
    Bron: eigen berekeningen ...

Die vorm blijft leesbaar in elke markdownviewer. Deze filter maakt er bij het opmaken
één geheel van (#tabelblok in _typst/typst-template.typ):
  - bijschrift bovenaan, in dezelfde stijl als bij de figuren, en het blijft bij de tabel
    ("sticky": het bijschrift komt nooit alleen onderaan een pagina);
  - Noot en Bron eronder in kleinere letter;
  - ruimte boven en onder, die wegvalt als het blok bovenaan een pagina begint.

Daarnaast maakt de filter de kolombreedtes bruikbaar. In de markdown bepaalt de breedte
van de streepjes in de scheidingsrij de kolombreedte. Dat levert bij overgenomen tabellen
soms een kolom van een paar procent op, waarin elk woord verticaal wordt afgebroken.
Daarom: kolommen smaller dan MINIMUM krijgen MINIMUM, en daarna worden alle breedtes
herschaald zodat ze samen de volle tekstbreedte vullen.

Het nummer in de markdown ("Tabel 9.") wordt gecontroleerd tegen de telling, net als bij
de figuren; bijlagetabellen ("Tabel B3.1.") tellen niet mee.
]]

local MINIMUM = 0.09   -- kleinste kolombreedte als aandeel van de tabelbreedte

-- Is dit blok een commentaar (<!-- wijziging: ... -->)? Dat mag de groepering niet breken.
local function is_commentaar(blok)
  return blok ~= nil and blok.t == "RawBlock" and blok.format == "html"
     and blok.text:match("^%s*<!%-%-") ~= nil
end

local function volgende(blokken, j)
  while is_commentaar(blokken[j]) do j = j + 1 end
  return blokken[j], j
end

-- Alinea van de vorm "**Tabel 9.** bijschrift"? Zo ja: nummer en bijschrift.
local function tabelkop(blok)
  if blok == nil or blok.t ~= "Para" or #blok.content < 1 then return nil end
  local eerste = blok.content[1]
  if eerste.t ~= "Strong" then return nil end
  local nummer = pandoc.utils.stringify(eerste):match("^Tabel%s+([%w%.%-]+)%.$")
  if not nummer then return nil end
  local bijschrift = pandoc.List()
  for i = 2, #blok.content do bijschrift:insert(blok.content[i]) end
  while #bijschrift > 0 and (bijschrift[1].t == "Space" or bijschrift[1].t == "SoftBreak") do
    bijschrift:remove(1)
  end
  return nummer, bijschrift
end

local function is_noot(blok)
  if blok == nil or blok.t ~= "Para" then return false end
  local tekst = pandoc.utils.stringify(blok)
  return tekst:match("^Noot:") ~= nil or tekst:match("^Bron:") ~= nil
end

-- Kolombreedtes bruikbaar maken: ondergrens, daarna herschalen naar 100%.
local function breedtes_herschalen(tabel)
  local kolommen = tabel.colspecs
  local som = 0
  for _, spec in ipairs(kolommen) do
    local w = spec[2]
    if w == nil or w == "ColWidthDefault" or type(w) ~= "number" then return end  -- automatisch: laat staan
    som = som + w
  end
  if som <= 0 then return end
  local nieuw, totaal = {}, 0
  for i, spec in ipairs(kolommen) do
    local w = spec[2] / som
    if w < MINIMUM then w = MINIMUM end
    nieuw[i] = w
    totaal = totaal + w
  end
  for i, spec in ipairs(kolommen) do
    kolommen[i] = { spec[1], nieuw[i] / totaal }
  end
  tabel.colspecs = kolommen
end

local teller = 0

function Pandoc(doc)
  local uit = pandoc.List()
  local blokken = doc.blocks
  local i = 1

  while i <= #blokken do
    local nummer, bijschrift = tabelkop(blokken[i])
    local blok_na_kop, na_kop = volgende(blokken, i + 1)
    if nummer and blok_na_kop ~= nil and blok_na_kop.t == "Table" then
      if nummer:match("^%d+$") then
        teller = teller + 1
        if tostring(teller) ~= nummer then
          io.stderr:write(string.format(
            "WAARSCHUWING tabellen.lua: markdown zegt 'Tabel %s', de PDF telt %d\n", nummer, teller))
        end
      end
      breedtes_herschalen(blok_na_kop)

      -- Noot en Bron die erop volgen, horen bij de tabel
      local noten = pandoc.List()
      local j = na_kop + 1
      local blok
      blok, j = volgende(blokken, j)
      while is_noot(blok) do
        noten:insert(blok)
        blok, j = volgende(blokken, j + 1)
      end

      uit:insert(pandoc.RawBlock("typst", '#tabelblok(nummer: "' .. nummer .. '", ['))
      uit:insert(pandoc.Plain(bijschrift))
      uit:insert(pandoc.RawBlock("typst", "], ["))
      uit:insert(blok_na_kop)
      if #noten > 0 then
        uit:insert(pandoc.RawBlock("typst", "#figuurnoot["))
        uit:extend(noten)
        uit:insert(pandoc.RawBlock("typst", "]"))
      end
      uit:insert(pandoc.RawBlock("typst", "])"))
      i = j
    else
      uit:insert(blokken[i])
      i = i + 1
    end
  end
  doc.blocks = uit
  return doc
end
