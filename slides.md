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

## The pitfalls

- **Colab's disk is temporary** — mount Drive before anything you want to keep
- **Missing values** — a fill number instead of `NaN`: **−999 for rainfall**, **99.9 for temperature**
- **No account needed** — IMD's grids download without any login or API key

Note: The fill-value pitfall is the one that silently wrecks an average — it looks like a real number until your mean comes out wildly wrong. Verified against real downloads: get_xarray() does NOT mask either one for you. Rain: millions of raw −999 cells, zero NaNs. Tmax: 222,026 of 351,726 cells were 99.9, zero NaNs. The two variables use different fill values, so a single hardcoded check for -999 silently misses the temperature case — mask by variable.

Bloom's (Evaluate): Is coding missing values as a fill number (different ones for rain vs. temperature, no less) a good design choice compared to using NaN directly? What does it gain, and what does it put at risk for someone who doesn't know to check?

---

## Clipping the grid to your area

- The grid you downloaded covers all of India — most of it isn't your study area.
- Load your shapefile, buffer it by 33 km, keep only the grid points inside.
- The buffer keeps points just outside the boundary too, so nothing at the edge gets missed.

Note: Steps to run live: (1) read the shapefile with geopandas, (2) reproject to a metric CRS via gdf.estimate_utm_crs() and buffer by 33_000 meters, (3) reproject the buffer back to lat/lon, (4) turn every grid cell into a point, (5) keep only points where .within(boundary) is True, (6) apply that as a mask with xarray's .where() and drop to a dataframe. Full code is in the notebook, not on this slide — the point for the room is just: don't process the whole country when you only need one basin.

Bloom's (Analyze): Why does buffering by 33 km in degrees give a different, wrong result depending on latitude, while buffering the same distance in meters doesn't?

---

## One row per point, not per day

```python
wide = points_df.pivot(index='time', columns=['lat', 'lon'], values='rain')
wide = wide.T   # flip it: now one row per grid point, one column per date

wide.to_csv('rain_wide.csv')
files.download('rain_wide.csv')
```

Note: points_df is one row per (time, lat, lon) -- "long" format. pivot() reshapes it to one row per date, one column per grid point; .T then flips that to one row per grid point, one column per date -- the layout most people actually expect when they open a CSV in a spreadsheet. Same files.download() pattern as the GeoPackage step: it prompts the browser to save the file locally.

---

## A 30-year climatology, built the same way

<img src="/static/climatology-map.png" alt="Raster maps of mean annual rainfall and average min/max temperature for Kolhapur district and its 33 km buffer, 1991-2020" width="900">

Note: Same pipeline as the notebook (download, mask the fill value, clip to the buffer) but over 1991-2020 -- the WMO's 30-year normal period -- computed once offline rather than live, since it's 90 file downloads instead of 12 (~8 minutes, not seconds). Rainfall is additive, so its map is the MEAN of 30 annual SUMS -- add up each year's daily totals, then average those 30 totals: 36 grid cells here for Kolhapur, ranging 504-4890mm, showing the Western Ghats gradient right at the district's edge. Temperature isn't additive -- summing daily degrees means nothing physically -- so tmin/tmax are a plain AVERAGE across every day of the 30 years, no summing step. Notice temperature is a single 1 degree x 1 degree box, bigger than the whole district -- the resolution gap from the IMD gridded data slide, visible as an honest limitation rather than a bug (labeled directly on the map).

Bloom's (Analyze): Why does rainfall get a sum-then-mean treatment here while temperature gets a direct average instead?

---

## Where's the data, where's the gap?

<div style="display:flex;gap:14px;justify-content:center;">
<img src="/static/nan-rainfall-normal.png" alt="All-India rainfall normal raster with NaN cells marked by dim dots" width="440">
<img src="/static/nan-tmean-avg.png" alt="All-India average Tmean raster with NaN cells marked by dim dots" width="440">
</div>

Note: Same 1991-2020 data, zoomed out to all of India, to make the pitfalls-slide point visible on an actual map. IMD's grid is a rectangle over India's lat/lon box -- most of that rectangle is ocean, or Pakistan, China, Nepal, Myanmar. Left map: colored boxes are real data (4964 of 17415 cells, 28.5%); the dim dots mark every NaN cell (12451 of them) -- not zero, not missing-by-accident, just never had land there. The dotted stippling stops exactly at the coastline and borders, so India's outline emerges as the clean, undotted shape. Right map: Tmean = (Tmax+Tmin)/2, the standard meteorological approximation for daily mean temperature, averaged directly across all 30 years of daily values (not summed, same rule as always for temperature) -- only 360 of 961 cells (37.5%) on the coarser 1 degree grid, dots for the other 601, Himalayan north visibly cooler than the rest of the country.

---

## Rainfall through 2025, day by day

<div style="text-align:center">
<video id="rainVid" src="/static/rain-2025.mp4" width="420" loop muted playsinline style="border-radius:8px;border:1px solid #262e39;cursor:pointer" onclick="this.paused?this.play():this.pause()"></video>
<div style="margin-top:14px;display:flex;gap:10px;justify-content:center;align-items:center;">
<button onclick="var v=document.getElementById('rainVid');v.paused?v.play():v.pause()" style="background:#1b212a;color:#e8e4da;border:1px solid #262e39;border-radius:6px;padding:8px 16px;font:700 13px 'Archivo',sans-serif;cursor:pointer;">Play / Pause</button>
<button onclick="var v=document.getElementById('rainVid');v.playbackRate=Math.max(0.25,v.playbackRate-0.25);document.getElementById('speedLbl').textContent=v.playbackRate.toFixed(2)+'x'" style="background:#1b212a;color:#e8e4da;border:1px solid #262e39;border-radius:6px;padding:8px 16px;font:700 13px 'Archivo',sans-serif;cursor:pointer;">− Speed</button>
<span id="speedLbl" style="color:#f2a93b;font-weight:700;min-width:3.5em;">1.00x</span>
<button onclick="var v=document.getElementById('rainVid');v.playbackRate=Math.min(4,v.playbackRate+0.25);document.getElementById('speedLbl').textContent=v.playbackRate.toFixed(2)+'x'" style="background:#1b212a;color:#e8e4da;border:1px solid #262e39;border-radius:6px;padding:8px 16px;font:700 13px 'Archivo',sans-serif;cursor:pointer;">+ Speed</button>
</div>
<div style="margin-top:8px;"><a href="/static/rain-2025.gif" style="color:#f2a93b;font-size:13px;">Download the .gif instead</a></div>
</div>

Note: 365 days of real IMD rainfall for 2025, one raster frame per day, same fixed 0-100mm color scale throughout so days are actually comparable. GIFs have no native pause or speed API in a browser, so the player above is a video encoding of the identical frames -- click it or the button to play/pause, use +/- Speed to change playback rate live. The literal .gif file (same 365 frames, ~11MB) is linked below for anyone who wants the file itself rather than the interactive version. Watch the color sweep north and east through June -- that's monsoon onset, visible day by day instead of as one static number.

Bloom's (Understand): Why does the color scale need to stay fixed across all 365 frames instead of auto-scaling to each day's own max value?

---

## Real-time rainfall, no archive required

```python
from datetime import date, timedelta
import imdlib as imd

yesterday = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
data = imd.get_real_data("rain", yesterday, yesterday, file_dir="./")
```

Note: get_real_data() is get_data()'s near-real-time sibling -- same 0.25 degree binary grid, same -999 fill value, but serving the last few days instead of the 1901-present archive, so it's the call for "how much rain fell yesterday" rather than a historical study. Mask exactly the same way -- ds.where(ds["rain"] > -999.0) -- then pcolormesh over lon/lat with a turbo colormap for a quick all-India map. Full download-to-PNG script is realtime_rainfall.py in the repo root, not on this slide.

Bloom's (Apply): You already have a working get_data() call for 2020-2023. What two arguments change to turn it into a get_real_data() call for just yesterday?

---

# Your turn

Open a fresh Colab notebook. Pick a state or basin in India — we'll pull its IMD rainfall grid this session.

Note: Live demo next — share the notebook link in chat and follow along. Same rules as always: ask if a cell doesn't make sense before we move on.

Bloom's (Create): Propose a rule for picking a buffer distance other than 33 km for your own basin — what would it depend on, and how would you justify the number you pick?

---

## Open the notebook

<img src="/static/qr-colab.png" alt="QR code to open the notebook in Colab" width="220">

[![Open In Colab](/static/vendor/colab-badge.svg)](https://colab.research.google.com/github/anantrajj7-sketch/lecture-deck/blob/main/imd_gridded_clip_exercise.ipynb)

colab.research.google.com/github/anantrajj7-sketch/lecture-deck

Note: QR points straight to "Open in Colab" for imd_gridded_clip_exercise.ipynb on GitHub — scanning it launches a ready-to-run copy, no setup needed. The badge underneath is the same link, clickable — it's also pinned to the top of the notebook itself. Full URL for anyone who'd rather type it: https://colab.research.google.com/github/anantrajj7-sketch/lecture-deck/blob/main/imd_gridded_clip_exercise.ipynb
