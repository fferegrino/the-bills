import json
import polars as pl
import streamlit as st


from bills import read_bills, bills_to_df

# Turn the bills into a Pandas DatagFrame

bills = read_bills()
df = bills_to_df(bills)


def calculate_values(df):
    if df.is_empty():
        return 0, 0, 0
    mean_prices = df['total'].mean()
    mean_tip = df['tip'].mean()
    total_price = df['total'].sum()
    return mean_prices, mean_tip, total_price


mean_prices, mean_tip, total_price = calculate_values(df)

mean_latitudes = df['latitude'].mean()
mean_longitudes = df['longitude'].mean()

# Get maximum and minimum values for latitude and longitude
max_lat = df['latitude'].max()
min_lat = df['latitude'].min()
max_long = df['longitude'].max()
min_long = df['longitude'].min()

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Total price", f"£{total_price:.2f}", delta=None, delta_color="normal", help=None,
              label_visibility="visible")

with col2:
    st.metric("Mean price", f"£{mean_prices:.2f}", delta=None, delta_color="normal", help=None,
              label_visibility="visible")

with col3:
    st.metric("Mean tip", f"£{mean_tip:.2f}", delta=None, delta_color="normal", help=None,
              label_visibility="visible")


import folium

from streamlit_folium import st_folium

# center on Liberty Bell, add marker
m = folium.Map(location=[mean_latitudes, mean_longitudes], zoom_start=16)

for row in df.iter_rows(named=True):
    folium.Marker(
        [row['latitude'], row['longitude']], popup=f"{row['restaurant']}", tooltip=""
    ).add_to(m)

m.fit_bounds([[min_lat, min_long], [max_lat, max_long]])

st_data = st_folium(m, width=725)

bounds = st_data['bounds']
_southWest = bounds['_southWest']
_northEast = bounds['_northEast']

filtered_range_df = df.filter(
    pl.col("latitude").is_between(_southWest['lat'], _northEast['lat']) &
    pl.col("longitude").is_between(_southWest['lng'], _northEast['lng']),
)



region_mean_prices, region_mean_tip, region_total_price = calculate_values(filtered_range_df)
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Total price", f"£{region_total_price:.2f}", delta=None, delta_color="normal", help=None,
              label_visibility="visible")

with col2:
    mean_price_kwargs = {}
    delta = region_mean_prices - mean_prices
    mean_price_kwargs["delta"] = f"{delta:.2f}"
    mean_price_kwargs["delta_color"] = "inverse"
    if delta == 0 or region_mean_prices == 0:
        delta_color = "off"
        mean_price_kwargs["delta"] = None
    st.metric("Mean price", f"£{region_mean_prices:.2f}", help=None,
              label_visibility="visible", **mean_price_kwargs)

with col3:
    st.metric("Mean tip", f"£{region_mean_tip:.2f}", delta=None, delta_color="normal", help=None,
              label_visibility="visible")
