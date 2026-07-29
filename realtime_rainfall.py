"""
Download yesterday's real-time IMD gridded rainfall (0.25 deg) and plot it.

Requires: imdlib, xarray, matplotlib
    pip install imdlib matplotlib
"""

from datetime import date, timedelta

import imdlib as imd
import matplotlib.pyplot as plt

# ---------------------------------------------------------------
# 1. Work out yesterday's date in the format imdlib expects
# ---------------------------------------------------------------
yesterday = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
print(f"Downloading real-time IMD rainfall for {yesterday}")

# ---------------------------------------------------------------
# 2. Download the real-time data
#    var_type: "rain" -> daily rainfall @ 0.25 deg resolution
#    Files are saved into file_dir (current folder here)
# ---------------------------------------------------------------
data = imd.get_real_data("rain", yesterday, yesterday, file_dir="./")

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

ax.set_title(f"IMD Daily Rainfall — {yesterday}")
ax.set_xlabel("Longitude (E)")
ax.set_ylabel("Latitude (N)")
ax.set_aspect("equal")

plt.tight_layout()
plt.savefig(f"imd_rainfall_{yesterday}.png", dpi=150)
plt.show()
