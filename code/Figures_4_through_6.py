import matplotlib.pyplot as plt
import numpy as np

# Generate fake data for demonstration
np.random.seed(19680801)  # Set random seed for reproducible results
# Create two datasets with different means (3.5 and 6.5) but same standard deviation (1.75)
data1 = np.random.normal(size=(47, 2), loc=3.5, scale=1.75)  # 47 samples, 2 variables
data2 = np.random.normal(size=(47, 2), loc=6.5, scale=1.75)  # 47 samples, 2 variables
labels = list('ABCD')  # Labels for the four data columns

# Combine the datasets horizontally to create 4 columns total
data = np.concatenate([data1, data2], axis=1)

# ### Figure 4a - Standard boxplot
f, a = plt.subplots()  # Create figure and axis
# Create boxplot with black median lines and no outliers
a.boxplot(data, medianprops={'color': 'black', 'linewidth': 1}, showfliers=False)
plt.axis("off")  # Hide axis labels and ticks
plt.savefig("../figures/Figure4a.png", dpi=300, bbox_inches="tight")  # Save high-res image

# ### Figure 4b - Modified boxplot with Tufte's edits
f, a = plt.subplots()  # Create new figure and axis
# Create boxplot with no "non-data ink"
bp = a.boxplot(data, medianprops={"linewidth": 0, "linestyle": None}, showfliers=False,
               showbox=False, showcaps=False)

# Manually draw custom median lines
for median in bp['medians']:
    median.set(color='k', linewidth=0)  # Make original median line invisible
    x, y = median.get_data()  # Get median line coordinates
    # Shrink the median line to 5% of original width and center it
    xn = (x - (x.sum() / 2.)) * 0.05 + (x.sum() / 2.)
    plt.plot(xn, y, color="k", linewidth=4, zorder=4)  # Draw thick black median line

plt.axis("off")  # Hide axis
plt.savefig("../figures/Figure4b.png", dpi=300, bbox_inches="tight")  # Save image

### Figures 5 and 6 - Choropleth maps of unemployment data
from urllib.request import urlopen
import json
import pandas as pd
import matplotlib.pyplot as plt
import geopandas as gp

# Load US county shapefile data
gdf = gp.read_file("../data/cb_2018_us_county_500k.shp")
# Create FIPS codes by combining state and county codes
gdf['fips'] = gdf['STATEFP'] + gdf['COUNTYFP']

# Load unemployment data CSV
df = pd.read_csv("../data/unemployment_data.csv")
df = df.rename(columns={"FIPS_Code": "fips"})  # Standardize column name
# Ensure FIPS codes are 5-digit strings with leading zeros
df['fips'] = df['fips'].astype(str).str.zfill(5)

# Merge geographic data with unemployment data
gdf = gdf.merge(df, how="left")

# Convert unemployment rates to numeric
gdf['unemployment22'] = pd.to_numeric(gdf['Unemployment_rate_2022'], errors="coerce")
gdf['unemployment21'] = pd.to_numeric(gdf['Unemployment_rate_2021'], errors="coerce")

# Absolute change from 2021 to 2022
gdf['unemp22-21'] = (gdf['unemployment22'] - gdf['unemployment21'])

# Reproject to Albers Equal Area Conic projection for better US map display
gdf = gdf.to_crs({'init': 'epsg:5070'})

# ### Figure 5a - 2022 unemployment rate map with non-monotonic "jet" colormap
f, a = plt.subplots(figsize=(10, 4))
# Create choropleth map with jet colormap, scale from 2% to 6%
gdf.plot(column="unemployment22", legend=True, cmap="jet", vmax=6, vmin=2, ax=a, legend_kwds={'shrink': .8})
# Set map bounds to show continental US
plt.xlim(-2.5*10**6, 2.5*10**6)
plt.ylim(0, 3.4*10**6)
plt.axis("off")  # Hide axis
plt.savefig("../figures/Figure5a.png", dpi=300, bbox_inches="tight")

# ### Figure 5b - Same data with monotonic "Blues" colormap
f, a = plt.subplots(figsize=(10, 4))
# Same map but with Blues colormap instead of jet
gdf.plot(column="unemployment22", legend=True, cmap="Blues", vmax=6, vmin=2, ax=a, legend_kwds={'shrink': .8})
# Set map bounds to show continental US
plt.xlim(-2.5*10**6, 2.5*10**6)
plt.ylim(0, 3.4*10**6)
plt.axis("off")
plt.savefig("../figures/Figure5b", dpi=300, bbox_inches="tight")  # Note: missing .png extension

# ### Figure 6a - Unemployment change map, zero is diverging point
f, a = plt.subplots(figsize=(10, 4))
# Symmetric scale (-5 to +5) and custom legend ticks
gdf.plot(column="unemp22-21", legend=True, vmax=5, vmin=-5, ax=a, cmap="RdBu", 
         legend_kwds={'ticks': list(range(-5, 6)), 'shrink': .8})
# Set map bounds to show continental US
plt.xlim(-2.5*10**6, 2.5*10**6)
plt.ylim(0, 3.4*10**6)
plt.axis("off")
plt.savefig("../figures/Figure6a.png", dpi=300, bbox_inches="tight")

# ### Figure 6b - Unemployment change map, -1 is diverging point
f, a = plt.subplots(figsize=(10, 4))
# Scale from -5 to +3 percentage points, which makes diverging point -1
gdf.plot(column="unemp22-21", legend=True, vmax=3, vmin=-5, ax=a, cmap="RdBu", legend_kwds={'shrink': .8})
# Set map bounds to show continental US
plt.xlim(-2.5*10**6, 2.5*10**6)
plt.ylim(0, 3.4*10**6)
plt.axis("off")
plt.savefig("../figures/Figure6b.png", dpi=300, bbox_inches="tight")

