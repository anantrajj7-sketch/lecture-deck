"""
Download yesterday's real-time IMD gridded rainfall (0.25 deg) and plot it.

Requires: imdlib, xarray, matplotlib
    pip install imdlib matplotlib
"""

from datetime import date, timedelta

import imdlib as imd
import matplotlib.pyplot as plt

# ---------------------------------------------------------------
# 1. Work out yesterday's date
#    imdlib itself needs YYYY-MM-DD (it feeds this to pd.date_range);
#    display_date is the DD-MM-YYYY form used for output and the title.
# ---------------------------------------------------------------
yesterday_dt = date.today() - timedelta(days=1)
api_date = yesterday_dt.strftime("%Y-%m-%d")
display_date = yesterday_dt.strftime("%d-%m-%Y")
print(f"Downloading real-time IMD rainfall for {display_date}")

# ---------------------------------------------------------------
# 2. Download the real-time data
#    var_type: "rain" -> daily rainfall @ 0.25 deg resolution
#    Files are saved into file_dir (current folder here)
# ---------------------------------------------------------------
data = imd.get_real_data("rain", api_date, api_date, file_dir="./")

# ---------------------------------------------------------------
# 3. Convert to an xarray Dataset and mask no-data cells
#    IMD uses -999.0 over ocean / outside the domain
# ---------------------------------------------------------------
ds = data.get_xarray()
ds = ds.where(ds["rain"] > -999.0)

rain = ds["rain"].isel(time=0)   # single day -> 2D field (lat x lon)

# ---------------------------------------------------------------
# 4. Plot with matplotlib
# ---------------------------------------------------------------
fig, ax = plt.subplots(figsize=(8, 9))

mesh = ax.pcolormesh(
    ds["lon"], ds["lat"], rain,
    cmap="turbo", shading="auto",
)

cbar = fig.colorbar(mesh, ax=ax, shrink=0.8, pad=0.02)
cbar.set_label("Rainfall (mm)")

ax.set_title(f"IMD Daily Rainfall — {display_date}")
ax.set_xlabel("Longitude (E)")
ax.set_ylabel("Latitude (N)")
ax.set_aspect("equal")

plt.tight_layout()
plt.savefig(f"imd_rainfall_{display_date}.png", dpi=150)
plt.show()
