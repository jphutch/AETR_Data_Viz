# Data Reading
library(httr)
library(utils)
library(tigris)

# Data Processing
library(dplyr)
library(sf)
library(tidyverse)

# Data Visualization
library(ggplot2)


# Data Reading

# RMA SoB data, 2017
# Using RMA URL, get the SOB data for 2017
url <- "https://www.rma.usda.gov/sites/default/files/information-tools/sobcov_2017.zip"

# Temporary file for downloading zip file
temp_file <- tempfile()
download.file(url, temp_file)

# Unzip the file to a temporary directory
temp_dir <- tempdir()
unzip(temp_file, exdir = temp_dir)

# Define column names
rma_cols <- c(
  'year', 'state_fips', 'state_abbrv', 'FIPS', 'county_name', 
  'commodity_code', 'commodity_name', 'ins_code', 'ins_name', 
  'coverage_category', 'delivery_type', 'coverage_level', 
  'policies_sold_total', 'policies_sold_reported', 'policies_indemnified', 
  'units_reported', 'units_losses', 'quantity_type', 'units_adjusted', 
  'acres_companion', 'liability', 'premium_base', 'premium_subsidized', 
  'premium_state_sub', 'subsidy_additional', 'EFA_discount', 
  'indemnity', 'loss_ratio'
)

# Read the txt file
rma17 <- read_delim(file = file.path(temp_dir, "sobcov_2017.txt"), 
                    delim = "|", 
                    col_names = rma_cols)


# NASS Census Data, 2017
api_key <- "API Key"
base_url <- "https://quickstats.nass.usda.gov/api/api_GET/"
params <- list(key = api_key,
               source_desc = "CENSUS",
               domain_desc = "TOTAL",
               short_desc = "FARM OPERATIONS - NUMBER OF OPERATIONS",
               year = "2017",
               agg_level_desc = "COUNTY",
               format = "csv")

response <- GET(base_url, query = params)
nass17_df <- content(response, "parsed")

# Census Boundary Files
# For counties
counties <- counties(cb = T, resolution = '5m') 

# For states
states <- states(cb = T, resolution = '5m') 


# Data Processing
## RMA 

rma17 <- rma17 |>  
         # Create county FIPS
         mutate(GEOID = paste0(state_fips,FIPS)) |> 
         # Total policies by county
         summarize(policies = sum(policies_sold_total), .by = GEOID)

## NASS
nass17_df <- nass17_df |> 
             # Create county FIPS
             mutate(GEOID = paste0(state_fips_code,county_code)) |>
             # Convert to integer
             mutate(farms = as.numeric(gsub(",","",Value))) |>
             # Select just two columns
             select(GEOID, farms) 

## Census

counties <- counties |>
            shift_geometry() |> 
            select(GEOID, STUSPS, NAME) |> 
            # Continental US only
            filter(GEOID < 60,
                   STUSPS != 'AK',
                   STUSPS != 'HI')

# Only keep states in the county boundary
states  <- states |> 
           filter(STUSPS %in% pull(counties,STUSPS))

# Merge in data
df <- counties |>
  left_join(rma17, by = "GEOID") |>
  left_join(nass17_df, by = "GEOID")

df <- df |> 
      # Make variable
      mutate(policies_per_farm = policies/farms) |>
      # Fill NAs with zero
      mutate(policies_per_farm = ifelse(is.nan(policies_per_farm),0,policies_per_farm)) |>
      mutate(policies_per_farm = ifelse(is.na(policies_per_farm),0,policies_per_farm))

# Data Visualization
# Create plot
p <- ggplot() +

# Plot counties with the coloring for policies per operation
  geom_sf(data = df, 
          aes(fill = policies_per_farm), 
          color = "black",  linewidth = .1) +
          
# Plot state boundaries
  geom_sf(data = states, 
          fill = NA, 
          color = "black", linewidth = .25) +
          
# Set colormap and create colorbar
  scale_fill_viridis_c(option = 'magma', 
                       direction = -1,
                       # Create normalization for colormap
                       limits = c(0, 20),
                       name = "Policies Sold (Per Farm Operation), 2017",
                       guide = guide_colourbar(title.position = "top",
                                               title.hjust = 0.5, 
                                               barheight = 0.35, 
                                               barwidth = 25)) + 
  theme_void() +
  
# Set legend options
  theme(legend.title = element_text(hjust = 0.5, 
                                    vjust = 0.5, 
                                    face = 'bold'), 
        legend.position = 'bottom')

# Save the map
ggsave("crop_insurance_policies_map_R.png", p, width = 10, height = 6, dpi = 300)

# Display the map
print(p)