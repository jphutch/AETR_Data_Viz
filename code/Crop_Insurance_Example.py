# Data Reading
import requests
import zipfile
import io

# Data Processing
import pandas as pd
import geopandas as gpd

# Data Visualization
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from matplotlib.colorbar import ColorbarBase


# Data Reading

# RMA SoB data, 2017
# Using RMA URL, get the SOB data for 2017
url = "https://www.rma.usda.gov/sites/default/files/information-tools/sobcov_2017.zip"
response = requests.get(url,stream=True)

# Unzip the file in the current directory
z = zipfile.ZipFile(io.BytesIO(response.content))
z.extractall("./")

# Define column names
rma_cols = [
        'year', 'state_fips', 'state_abbrv', 'FIPS', 'county_name', 
        'commodity_code', 'commodity_name', 'ins_code', 'ins_name', 
        'coverage_category', 'delivery_type', 'coverage_level', 
        'policies_sold_total', 'policies_sold_reported', 'policies_indemnified', 
        'units_reported', 'units_losses', 'quantity_type', 'units_adjusted', 
        'acres_companion', 'liability', 'premium_base', 'premium_subsidized', 
        'premium_state_sub', 'subsidy_additional', 'EFA_discount', 
        'indemnity', 'loss_ratio']

# Read the txt file
rma17 = pd.read_csv("./sobcov_2017.txt", 
                         delimiter='|', 
                         header=None, 
                         names=rma_cols,
                         low_memory=False)
        
# NASS Census Data, 2017
api_key = "API-Key"
base_url = "https://quickstats.nass.usda.gov/api/api_GET/"

params = {
        'key': api_key,'source_desc': 'CENSUS',
        'source_desc': 'CENSUS',
        'domain_desc': 'TOTAL',
        "short_desc":"FARM OPERATIONS - NUMBER OF OPERATIONS", 
        'year': '2017',
        'agg_level_desc': 'COUNTY',
        }
    
response = requests.get(base_url, params=params)

nass17 = response.json()

nass17_df = pd.DataFrame(nass17['data'])

# Census Boundary Files
# For counties
counties= gpd.read_file('https://www2.census.gov/geo/tiger/GENZ2020/shp/cb_2020_us_county_5m.zip')

# For states
states = gpd.read_file('https://www2.census.gov/geo/tiger/GENZ2020/shp/cb_2020_us_state_5m.zip')


# Data Processing
## RMA

# Create county FIPS
rma17['GEOID'] = rma17['state_fips'].astype(str).str.zfill(2) \
                 + rma17['FIPS'].astype(str).str.zfill(3)

# Total policies by county
rma17 = rma17.groupby(['GEOID'])['policies_sold_total'].sum()
rma17 = rma17.reset_index()

## NASS 

# Create county FIPS
nass17_df['GEOID'] = nass17_df['state_fips_code'] + \
                     nass17_df['county_code']

# Convert to integer
nass17_df['farms'] = nass17_df['Value'].str.replace(",","")\
                                       .astype(int)

# Select just two columns
nass17_df = nass17_df[['GEOID','farms']]

## Census

# Continental US only
counties = counties[(counties['GEOID'].astype(int) < 60000) & 
                    (counties['STUSPS'] != 'AK') & 
                    (counties['STUSPS'] != 'HI')]

counties = counties.to_crs({'init': 'epsg:5070'})

# Only keep states in the county boundary
US_states =  states['STUSPS'].isin(counties['STUSPS'].unique())
states= states[US_states]

states = states.to_crs({'init': 'epsg:5070'})

# Merge in data on GEOID (FIPS)
df = counties.merge(rma17,how="left",on="GEOID")
df = df.merge(nass17_df,how="left",on="GEOID")

# Make variable
df['policies_per_farm'] = df['policies_sold_total']/df['farms']

# Fill NAs with zero
df['policies_per_farm'] = df['policies_per_farm'].fillna(0)

# Data Visualization
# Create plot
fig, ax = plt.subplots(figsize=(10, 6))

# Create normalization for colormap
norm = Normalize(vmin=0, vmax=20)

# Plot counties with the coloring for policies per operation
df.plot(ax=ax, 
        column='policies_per_farm', 
        cmap='magma_r', 
        linewidth=0.1, 
        edgecolor='black',
        norm=norm)

# Plot state boundaries
states.boundary.plot(ax=ax, 
                     color='black', 
                     linewidth=0.25)

# Remove axes
ax.set_axis_off()

# Create colorbar
cbar_ax = fig.add_axes([0.25, 0.05, 0.5, 0.03]) 
cbar = ColorbarBase(cbar_ax,
                    norm=norm,
                    cmap="magma_r",
                    orientation='horizontal',
                    ticks=[0,5,10,15,20])
cbar.set_label("Policies Sold (Per Farm Operation), 2017", 
               fontweight='bold', labelpad=10)

# Adjust layout
plt.tight_layout()
plt.subplots_adjust(bottom=0.15)

# Save the map
plt.savefig('../figures/crop_insurance_policies_map_py.png', dpi=300, bbox_inches='tight')

# Display the map
plt.show()