import streamlit as st
import pandas as pd 
import numpy as np
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from datetime import datetime as dt 
import os
import geopandas as gpd
from shapely.geometry import Point
import plotly.express as px
import osmnx as ox
import pandas as pd
from PIL import Image 

####

top20 = pd.read_csv(os.path.join('Dashboard/Top20.csv'),  index_col = False)

####

page = st.sidebar.selectbox('Select an aspect of the analysis',
   ["Intro page",  "Weather component and bike usage",
  "Most popular stations",
     "Interactive map with aggregated bike trips", "Jersey City + Hoboken Combined Choropleth Map", "Recommendations"])

####################### DEFINE THE PAGES ##########################

####

st.title("Citi Bike Strategy Dashboard")

### Intro page

if page == "Intro page":
    st.markdown("#### This dashboard aims at providing helpful insights on the expansion problems Divvy Bikes currently face.")
    st.markdown("Right now, Citi Bikes run into a situation where customers complain about bikes not being available at certain times. This analysis will look at the potential reasons behind this. The dashboard is separated into five sections:")

    st.markdown(" - Most popular stations")
    st.markdown(" - Weather component and bike usage")
    st.markdown(" - Interactive map with aggregated bike trips")
    st.markdown(" - Jersey City + Hoboken Combined Choropleth Map")
    st.markdown(" - Recommendations")
    st.markdown(" - The dropdown menu on the left 'Aspect Selector' will take you to the different aspects of the analysis out team looked at")

    myImage = Image.open("Dashboard/NJ Bikes.png")
    st.image(myImage)

####

# ########################### DEFINE THE CHARTS ############################

elif page == 'Weather component and bike usage' :

    df_1 = pd.read_csv(os.path.join('Dashboard/df_weather.csv'),  index_col = False)

## line chart 

    fig_2 = make_subplots(specs=[[{"secondary_y": True}]])

    fig_2.add_trace(
    go.Scatter(x = df_1['date'], y = df_1['bike_rides_daily'], name = 'Daily bike rides', marker={'color': 'blue'}), secondary_y = False)

    fig_2.add_trace(
    go.Scatter(x=df_1['date'], y=df_1['average_tempurature'], name='Daily temperature', marker={'color': 'red'}), secondary_y=True)

    st.header("Daily Bike Trips and Tempurature in Jersey City")
    st.plotly_chart(fig_2)

####

    st.markdown("Seasons affects number of trips. As the weather gets cooler, fewer people use CitiBike's services. Limiting the number of available bikes during the colder months should reduce upkeep and maintence costs.")

####

elif page == 'Most popular stations' :

## Bar chart 

## Groupby

    fig = go.Figure(go.Bar(x = top20['start_station_name'], y = top20['value'], marker={'color': top20['value'],'colorscale': 'Blues'}))

    fig.update_layout(
        title = 'Top 20 Most Popular Bike Stations in Jersey City',
        xaxis_title = 'Start Stations', 
        yaxis_title = 'Sum of Trips', 
        width = 900, height = 600
    )

    st.plotly_chart(fig)

####

    st.markdown("The top 4 bike stations being used during the year 2022 are significantly higher then the rest of the top 20. Cursory research shows that those stations are in Hoboken.")



### Add the map  ###

elif page == 'Interactive map with aggregated bike trips': 

    path_to_html = "Dashboard/CitiBike Bike Trips Aggregated.html"

# Read file and keep in variable 
    with open(path_to_html, 'r') as f:
        html_data = f.read()

## Show in web page 
    st.header("Aggregated Bike Trips in New York City")
    st.components.v1.html(html_data,height = 1000)

####

    st.markdown("While most bike trips start in Hoboken, they more frequently end in Jersey City. This suggests a commute between Hoboken and Jersey City.")

####

elif page == 'Jersey City + Hoboken Combined Choropleth Map' :

    df = pd.read_csv(os.path.join('Dashboard/CitiBike_final_locations_for_map_filtered.csv'),  index_col = False)

####

    st.header("Jersey City + Hoboken Combined Choropleth Map")

####

# -------------------------------------------------------------------------
# 1) Load Hoboken municipal polygon
# -------------------------------------------------------------------------
    gdf_hoboken = ox.geocode_to_gdf("Hoboken, New Jersey, USA").to_crs("EPSG:4326")

# Clean + explode multipolygons
    gdf_hoboken = gdf_hoboken.explode(index_parts=False).reset_index(drop=True)
    gdf_hoboken = gdf_hoboken[gdf_hoboken.geometry.notna()]
    gdf_hoboken = gdf_hoboken[gdf_hoboken.is_valid]

# Assign a fake "geoid" so Plotly can reference it
# (Jersey City uses census tract IDs; Hoboken is a city boundary)
    gdf_hoboken["geoid"] = "HOBOKEN_CITY"

# -------------------------------------------------------------------------
# 2) Load Jersey City census tracts
# -------------------------------------------------------------------------
    GEO_PATH = r"Dashboard/jersey_city_censustract_geojson.geojson"
    gdf_jc = gpd.read_file(GEO_PATH)

    if gdf_jc.crs is None:
        gdf_jc = gdf_jc.set_crs("EPSG:4326")
    else:
        gdf_jc = gdf_jc.to_crs("EPSG:4326")

# -------------------------------------------------------------------------
# 3) Build point GeoDataFrame
# -------------------------------------------------------------------------
    df_points = pd.DataFrame({
        "lat": df["start_lat"],
        "lon": df["start_lng"],
        "trips": df["trips"]
    }).dropna(subset=["lat", "lon"])

    gdf_points = gpd.GeoDataFrame(
        df_points,
        geometry=[Point(xy) for xy in zip(df_points["lon"], df_points["lat"])],
        crs="EPSG:4326"
    )

# -------------------------------------------------------------------------
# 4) Spatial join: assign points to JC tracts
# -------------------------------------------------------------------------
    gdf_joined_jc = gpd.sjoin(
        gdf_points,
        gdf_jc[["geoid", "geometry"]],
        how="left",
        predicate="intersects"
    )

    jc_counts = (
        gdf_joined_jc.groupby("geoid")["trips"]
                 .sum()
                 .reset_index(name="trip_sum")
    )

    gdf_jc = gdf_jc.merge(jc_counts, on="geoid", how="left")
    gdf_jc["trip_sum"] = gdf_jc["trip_sum"].fillna(0)

# -------------------------------------------------------------------------
# 5) Spatial join: assign points to Hoboken polygon
# -------------------------------------------------------------------------
    gdf_joined_hob = gpd.sjoin(
        gdf_points,
        gdf_hoboken[["geoid", "geometry"]],
        how="inner",
        predicate="intersects"
    )

# Sum trips for Hoboken
    hoboken_trip_sum = gdf_joined_hob["trips"].sum()

    gdf_hoboken["trip_sum"] = hoboken_trip_sum

# -------------------------------------------------------------------------
# 6) COMBINE BOTH sets of polygons into a single GeoDataFrame
# -------------------------------------------------------------------------
    gdf_combined = pd.concat([gdf_jc, gdf_hoboken], ignore_index=True)

# -------------------------------------------------------------------------
# 7) Single combined choropleth
# -------------------------------------------------------------------------
    fig_3 = px.choropleth_mapbox(
        gdf_combined,
        geojson=gdf_combined.__geo_interface__,
        locations="geoid",                    # JC uses tract GEOIDs, Hoboken uses "HOBOKEN_CITY"
        featureidkey="properties.geoid",
        color="trip_sum",
        color_continuous_scale="Viridis",
        opacity=0.65,
        hover_data={"geoid": True, "trip_sum": True}
    )

# Add ALL points on top
    fig_3.add_scattermapbox(
        lon=gdf_points["lon"],
        lat=gdf_points["lat"],
        mode="markers",
        name="Points",
        marker=dict(size=5, color="turquoise", opacity=0.7),
        text=gdf_points["trips"],
        hovertemplate="Trips: %{text}<extra></extra>"
    )

# Final map appearance
    fig_3.update_layout(
        mapbox=dict(
            style="carto-positron",
            center={"lat": 40.73, "lon": -74.05},
            zoom=11.7,
        ),
        margin=dict(r=0, l=0, t=0, b=0),
        title="Jersey City + Hoboken Combined Choropleth"
    )

    st.plotly_chart(fig_3)

####

    st.markdown("Most bike trips start in Hokoboken. Making sure those stations are well stocked is high priority.")
else: 

    st.header("Conclusion and recommendations") 
    bikes = Image.open("Dashboard/andrew-gook-VRLHw_rBjIw-unsplash.jpg") #source: UnSplash
    st.image(bikes)
    st.markdown("### My analysis has shown that Citi Bikes should focus on the following objectives moving forward:") 
    st.markdown("-Add more stations to locations in Jersey City to ensure that commuters have places to deposit their bikes after their commute is done.") 
    st.markdown("-Market their services to people outside of Hoboken.")
    st.markdown("-Ensure that bikes are fully stocked in all these stations during the warmer months in order to meet the higher demand, but provide a lower supply in winter and late autumn to reduce logistics costs.")
