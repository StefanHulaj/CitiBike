import streamlit as st
import pandas as pd 
import numpy as np
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from datetime import datetime as dt 
import os

####

path = r"C:\Users\stefa\CitiBike"

####

top20 = pd.read_csv(os.path.join(path, 'Top20.csv'),  index_col = False)

####

st.set_page_config(page_title = 'Citi Bike Strategy Dashboard', layout='wide')

####

st.title("Citi Bike Strategy Dashboard")

####

st.markdown("The dashboard will help visualize current usage trends of Citi Bike")

# ########################### DEFINE THE CHARTS ############################


## Bar chart 

## Groupby

fig = go.Figure(go.Bar(x = top20['start_station_name'], y = top20['value'], marker={'color': top20['value'],'colorscale': 'Blues'}))

fig.update_layout(
    title = 'Top 20 Most Popular Bike Stations in New York City',
    xaxis_title = 'Start Stations', 
    yaxis_title = 'Sum of Trips', 
    width = 900, height = 600
)

st.plotly_chart(fig, width=True)

####

df_1 = pd.read_csv(os.path.join(path, 'df_weather.csv'),  index_col = False)

####

## line chart 

fig_2 = make_subplots(specs=[[{"secondary_y": True}]])

fig_2.add_trace(
go.Scatter(x = df_1['date'], y = df_1['bike_rides_daily'], name = 'Daily bike rides', marker={'color': 'blue'}), secondary_y = False)

fig_2.add_trace(
go.Scatter(x=df_1['date'], y=df_1['average_tempurature'], name='Daily temperature', marker={'color': 'red'}), secondary_y=True)

st.header("Daily Bike Trips and Tempurature in New York City")
st.plotly_chart(fig_2, width=True)

####

### Add the map  ###

path_to_html = "CitiBike Bike Trips Aggregated.html"

# Read file and keep in variable 
with open(path_to_html, 'r') as f:
    html_data = f.read()

## Show in web page 
st.header("Aggregated Bike Trips in New York City")
st.components.v1.html(html_data,height = 1000)

