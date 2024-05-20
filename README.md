# josm-ge-preset

[OpenStreetMap](https://openstreetmap.org) [tagging preset](https://josm.openstreetmap.de/wiki/Presets) for 🇬🇪 [Georgian](https://en.wikipedia.org/wiki/Georgia_(country)) POIs. Works with [JOSM](https://josm.openstreetmap.de) and [Vespucci](https://vespucci.io).


**!!!Warning!!!**

Repository's license doesn't spread on logos of POIs. They can be under protection. Represented here only as examples

## Installation

### JOSM

1. Open `Presets` → `Preset preferences` → `Active presets` → `+`
2. Paste this into `URL / File` field `https://raw.githubusercontent.com/komachi/josm-ge-preset/main/ge.xml`
3. Press `OK`
4. Press `OK` again

### Vespucci

1. Open `Preferences` → `Presets` → `Add preset`
2. Paste this into `URL` field `https://raw.githubusercontent.com/komachi/josm-ge-preset/main/ge.xml`
3. Press `OK`
4. Enable added preset with checkmark

## Merging with the Name Suggestion Index

1. Fetch the [Name Suggestion Index](https://github.com/osmlab/name-suggestion-index). We'll assume it's in `../name-suggestion-index`, i.e. `cd ..; git clone https://github.com/osmlab/name-suggestion-index` .
2. Install `python3` (if not installed)
3. `python3 ./toNSI.py ../name-suggestion-index < ge.xml`
4. Install `nodejs` (if not installed)
5. `cd ../name-suggestion-index; npm run build`
