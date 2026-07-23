# Open-source climate data

Downloading IMD gridded data with imdlib — all in Google Colab.

Note: Welcome. Today is about going from "I need rainfall for this basin" to a file you can plot — with nothing installed on your own machine.

---

## Two shapes of data

- **Point data** — a station: one lat/lon, a time series. CSV-shaped.
- **Gridded data** — a raster over time: every cell, every timestep. NetCDF/GRIB-shaped.

Note: Everything else in this talk is a consequence of this split. Point data is small and easy. Gridded data is big and dimensional, and needs xarray. Last time you worked with point data — today it's the grid underneath it.

Bloom's (Understand): In your own words, why can't a single lat/lon point ever be downloaded on its own from IMD — what has to come with it?

---

## Quick recall

- Last time, you used imdlib to pull rainfall for **one point** — your town, say.
- Quiz: behind the scenes, did it fetch just that one number, or something bigger?

Note: Give them time to answer out loud before revealing. Answer: something bigger — a whole grid. IMD never ships a single point on its own; imdlib always downloads the full country grid first, then picks out the cell closest to your lat/lon. That's the bridge into today: what's sitting in the rest of that grid you already had?

Bloom's (Remember): this quiz question itself is the Remember-level check — recalling what imdlib actually fetched last session, before we build on it today.

---

## Why Google Colab

- Free CPU, no local Python install, nothing to configure
- Runs in the browser — a lab machine or a phone works
- Google Drive mount gives it a persistent disk

Note: The catch is the one thing everyone forgets: the runtime is thrown away when it disconnects. Anything downloaded goes to Drive, or it goes nowhere.

---

## IMD gridded data

- **Rainfall** — 0.25°×0.25°, daily, 1901–present
- **Temperature** (max/min) — 1°×1°, daily, 1951–present
- Published by IMD Pune as raw binary `.GRD` files, one per year

Note: The binary format is the whole reason this deserves its own slide — there's no header, no metadata, just a flat array. You need to know the grid shape in advance to read it correctly, which is exactly what imdlib handles for you.

---

## Getting it: IMD gridded (in Colab)

```python
!pip install -q imdlib
import imdlib as imd

imd.get_data('rain', 2020, 2023, fn_format='yearwise')
ds = imd.open_data('rain', 2020, 2023, 'yearwise')
```

Note: imdlib downloads the raw .GRD files from IMD Pune and does the binary decoding for you, handing back an xarray Dataset. `ds.get_xarray()` gives the object you'll actually plot or slice. No API key, no account.

Bloom's (Apply): If you wanted 2015–2018 temperature instead of 2020–2023 rainfall, which two arguments in imd.get_data() would you change, and to what?

---

## Opening what you downloaded

- `ds.get_xarray()` → an **xarray** Dataset — the whole grid, indexed by lat, lon, and time
- `.sel(lat=..., lon=..., method='nearest')` → pull a single point out of the grid
- `.mean(dim='time')` / `.sel(time=...)` → collapse or slice along time

Note: This is the payoff of using xarray instead of a raw array — indexing by real lat/lon/date instead of row/column numbers. It's also exactly what imdlib was doing for you behind the scenes when you pulled a single point last time.

---

## The gotchas

- **Colab's disk is temporary** — mount Drive before anything you want to keep
- **Missing values** — IMD grids use −999 as a fill value, not `NaN`; mask it explicitly
- **No account needed** — IMD's grids download without any login or API key

Note: The −999 gotcha is the one that silently wrecks an average — it looks like a real number until your mean rainfall comes out negative. imdlib's get_xarray() already masks it, but check before trusting a raw array.

Bloom's (Evaluate): Is coding missing values as −999 a good design choice compared to using NaN directly? What does it gain, and what does it put at risk for someone who doesn't know to check?

---

## Clipping the grid to your area

- The grid you downloaded covers all of India — most of it isn't your study area.
- Load your shapefile, buffer it by 33 km, keep only the grid points inside.
- The buffer keeps points just outside the boundary too, so nothing at the edge gets missed.

Note: Steps to run live: (1) read the shapefile with geopandas, (2) reproject to a metric CRS via gdf.estimate_utm_crs() and buffer by 33_000 meters, (3) reproject the buffer back to lat/lon, (4) turn every grid cell into a point, (5) keep only points where .within(boundary) is True, (6) apply that as a mask with xarray's .where() and drop to a dataframe. Full code is in the notebook, not on this slide — the point for the room is just: don't process the whole country when you only need one basin.

Bloom's (Analyze): Why does buffering by 33 km in degrees give a different, wrong result depending on latitude, while buffering the same distance in meters doesn't?

---

# Your turn

Open a fresh Colab notebook. Pick a state or basin in India — we'll pull its IMD rainfall grid this session.

Note: Live demo next — share the notebook link in chat and follow along. Same rules as always: ask if a cell doesn't make sense before we move on.

Bloom's (Create): Propose a rule for picking a buffer distance other than 33 km for your own basin — what would it depend on, and how would you justify the number you pick?
