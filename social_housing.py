#!/usr/bin/env python

import numpy as np
import pandas as pd
import geopandas as gpd
import plotly.express as px

MAPBOX_TOKEN_PATH = ''
MSOA_CENSUS_DATA_PATH = "MSOAs_housing.csv"
MSOA_GEOJSON_V2_PATH  = "MSOA_2021_EW_BGC_V2_1370945015033551734.geojson"
MSOA_GEOJSON_V3_PATH  = "Middle_layer_Super_Output_Areas_December_2021_Boundaries_EW_BGC_V3_4916445166053426.geojson"

msoa_raw = pd.read_csv(MSOA_CENSUS_DATA_PATH)
msoa_pivot = (
    msoa_raw.query(
        '   `Tenure of household (5 categories)` == "Rented: Social rented" '
        '&  `Country of birth (UK) (3 categories)` != "Does not apply" ')
    .rename({ 
        "Middle layer Super Output Areas Code": "MSOA21CD",
        "Middle layer Super Output Areas": "MSOA21NM" 
        }, 
        axis=1)
    .pivot_table(
        index=["MSOA21CD", "MSOA21NM"],
        columns="Country of birth (UK) (3 categories)",
        values="Observation",
        aggfunc='sum',
        fill_value=0)
    .apply(lambda x: {
            "Foreign-born %": round(x["Born outside the UK"] / x.sum() * 100, 0)
        }, 
        result_type='expand', 
        axis=1)
    .reset_index()
)

#msoa_gdf = gpd.read_file(MSOA_GEOJSON_V3_PATH)
msoa_gdf = gpd.read_file(MSOA_GEOJSON_V2_PATH)
wgs84 = msoa_gdf.to_crs(crs=4326)
gdf = wgs84.merge(msoa_pivot).set_index("MSOA21CD")

# Required for "basic" mapbox_style
# Check the documentation for px.choropleth_mapbox
token = open(MAPBOX_TOKEN_PATH).read()
px.set_mapbox_access_token(token)

fig = px.choropleth_mapbox(
    data_frame=gdf,
    geojson=gdf.geometry,
    locations=gdf.index,
    color="Foreign-born %",
    hover_name="MSOA21NM",
    hover_data="Foreign-born %",
    mapbox_style="basic"
    )

fig.update_coloraxes(colorscale="YlOrRd")
fig.update_layout(
    title=dict(text="Percentage of social housing tenants that are foreign-born")
    )
fig.update_traces(marker_line_width=0)
fig.write_html("social_housing_map.html", include_plotlyjs='directory')
