--[[
figuren.lua: zet de figuurconventie uit report/sections/*.md om naar een echte figuur.

In de markdown ziet een figuur er zo uit (vier opeenvolgende alinea's):

    **Figuur 4.** Beroepssolidariteit: reële bijdragen ...
    ![](../../output/figures/fig04_beroepssolidariteit_Z1_W1.png)
    Noot: bijdragen en uitgaven gecorrigeerd ...
    Bron: eigen berekeningen op basis van ...

Die vorm blijft leesbaar in elke markdownviewer (GitHub, VS Code). Deze filter
maakt er bij het opmaken één Quarto-figuur van:
  - bijschrift bovenaan, automatisch genummerd ("Figuur 4.")
  - afbeelding over de volledige tekstbreedte
  - Noot en Bron in kleinere letter onder de afbeelding
  - alles samen op één pagina (een figuur wordt nooit over twee pagina's gesplitst)

Het nummer in de markdown ("Figuur 4.") wordt enkel gecontroleerd, niet gebruikt:
de PDF nummert zelf. Wijkt het af, dan verschijnt een waarschuwing bij het renderen.
Bijlagefiguren ("Figuur B4.1.") tellen niet mee: hun nummer wordt letterlijk overgenomen.
]]

-- Afbeeldingspaden in sections/ zijn relatief tegenover report/sections/.
-- Na het samenvoegen in rapport.qmd (in de root van het project) wordt dat "output/...".
local function pad_corrigeren(src)
  return (src:gsub("^%.%./%.%./", ""))
end

-- Is deze alinea het begin van een figuur? Zo ja: geef nummer en bijschrift terug.
local function figuurkop(blok)
  if blok.t ~= "Para" or #blok.content < 1 then return nil end
  local eerste = blok.content[1]
  if eerste.t ~= "Strong" then return nil end
  local label = pandoc.utils.stringify(eerste)
  local nummer = label:match("^Figuur%s+([%w%.%-]+)%.$")
  if not nummer then return nil end
  -- bijschrift = alles na het vetgedrukte label, zonder de spatie ervoor
  local bijschrift = pandoc.List()
  for i = 2, #blok.content do bijschrift:insert(blok.content[i]) end
  while #bijschrift > 0 and (bijschrift[1].t == "Space" or bijschrift[1].t == "SoftBreak") do
    bijschrift:remove(1)
  end
  return nummer, bijschrift
end

-- Alinea die enkel uit één afbeelding bestaat?
local function enkel_afbeelding(blok)
  if blok == nil then return nil end
  if blok.t == "Para" and #blok.content == 1 and blok.content[1].t == "Image" then
    return blok.content[1]
  end
  if blok.t == "Figure" then  -- pandoc maakt soms zelf al een figuur
    local img = nil
    blok:walk({ Image = function(el) img = el end })
    return img
  end
  return nil
end

-- Een wijzigingscommentaar (<!-- wijziging: ... -->) tussen de onderdelen van een figuur mag de
-- groepering niet breken: die commentaren verdwijnen toch uit de PDF.
local function is_commentaar(blok)
  return blok ~= nil and blok.t == "RawBlock" and blok.format == "html"
     and blok.text:match("^%s*<!%-%-") ~= nil
end

-- Eerstvolgende blok dat geen commentaar is, met zijn index.
local function volgende(blokken, j)
  while is_commentaar(blokken[j]) do j = j + 1 end
  return blokken[j], j
end

-- Alinea die begint met "Noot:" of "Bron:"?
local function is_noot(blok)
  if blok == nil or blok.t ~= "Para" then return false end
  local tekst = pandoc.utils.stringify(blok)
  return tekst:match("^Noot:") ~= nil or tekst:match("^Bron:") ~= nil
end

local teller = 0

function Pandoc(doc)
  local uit = pandoc.List()
  local blokken = doc.blocks
  local i = 1
  -- de demo in rapport.qmd laat de figuurteller bij 3 starten; lees dat om de controle correct te doen
  local startteller = tonumber(pandoc.utils.stringify(doc.meta["figuur-start"] or "0")) or 0
  teller = startteller

  while i <= #blokken do
    local nummer, bijschrift = figuurkop(blokken[i])
    local blok_na_kop, na_kop = volgende(blokken, i + 1)
    local img = nummer and enkel_afbeelding(blok_na_kop)
    if nummer and img and not nummer:match("^%d+$") then
      -- Bijlagefiguur ("Figuur B4.1."): niet mee in de doorlopende nummering van het rapport.
      -- Het nummer uit de markdown wordt letterlijk overgenomen; de opmaak (bijschrift boven,
      -- noot eronder, nooit gesplitst) doet #bijlagefiguur in _typst/typst-template.typ.
      local bestand = pad_corrigeren(img.src)
      local afbeelding = pandoc.Image({}, bestand, "", pandoc.Attr("", {}, { width = "100%" }))
      local j = na_kop + 1
      local noten = pandoc.List()
      local blok
      blok, j = volgende(blokken, j)
      while is_noot(blok) do
        noten:insert(blok)
        blok, j = volgende(blokken, j + 1)
      end
      uit:insert(pandoc.RawBlock("typst", '#bijlagefiguur(nummer: "' .. nummer .. '", ['))
      uit:insert(pandoc.Plain(bijschrift))
      uit:insert(pandoc.RawBlock("typst", "], ["))
      uit:insert(pandoc.Para({ afbeelding }))
      uit:extend(noten)
      uit:insert(pandoc.RawBlock("typst", "])"))
      i = j
    elseif nummer and img then
      teller = teller + 1
      if tostring(teller) ~= nummer then
        io.stderr:write(string.format(
          "WAARSCHUWING figuren.lua: markdown zegt 'Figuur %s', de PDF nummert %d (%s)\n",
          nummer, teller, img.src))
      end

      -- afbeelding over de tekstbreedte
      local bestand = pad_corrigeren(img.src)
      local afbeelding = pandoc.Image({}, bestand, "", pandoc.Attr("", {}, { width = "100%" }))

      -- Noot en Bron verzamelen
      local noten = pandoc.List()
      local j = na_kop + 1
      local blok
      blok, j = volgende(blokken, j)
      while is_noot(blok) do
        noten:insert(blok)
        blok, j = volgende(blokken, j + 1)
      end

      -- identificatie op basis van de bestandsnaam: fig-fig04_beroepssolidariteit_Z1_W1
      local id = "fig-" .. bestand:match("([^/]+)%.%w+$"):gsub("[^%w%-_]", "-")

      -- inhoud van de figuur: afbeelding, dan de noten in een #figuurnoot[...]-blok
      -- (figuurnoot is gedefinieerd in _typst/typst-template.typ)
      local inhoud = pandoc.List({ pandoc.Para({ afbeelding }) })
      if #noten > 0 then
        inhoud:insert(pandoc.RawBlock("typst", "#figuurnoot["))
        inhoud:extend(noten)
        inhoud:insert(pandoc.RawBlock("typst", "]"))
      end
      -- Quarto herkent een Div met id 'fig-...' als figuur; de laatste alinea is het bijschrift
      inhoud:insert(pandoc.Para(bijschrift))
      uit:insert(pandoc.Div(inhoud, pandoc.Attr(id)))
      i = j
    else
      uit:insert(blokken[i])
      i = i + 1
    end
  end
  doc.blocks = uit
  return doc
end
