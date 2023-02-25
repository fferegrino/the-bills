import polars as pl
import streamlit as st

from map_utils import get_bill_popup


import folium

from streamlit_folium import st_folium

from bills import read_bills, bills_to_df

# Turn the bills into a Pandas DatagFrame

st.set_page_config(
    page_title="The Bills",
    page_icon="🧾",
    layout="wide",
    menu_items={},
)

bills = read_bills()

# Create a dictionary using the hash as the key and the bill as the value
bills_dict = {bill["hash"]: bill for bill in bills}

df = bills_to_df(bills)


def aggregate_values(frame):
    if frame.is_empty():
        return 0, 0, 0
    _mean_prices = frame["total"].mean()
    _mean_tip = frame["tip"].mean()
    _total_price = frame["total"].sum()
    return _mean_prices, _mean_tip, _total_price


mean_prices, mean_tip, total_price = aggregate_values(df)

mean_latitudes = df["latitude"].mean()
mean_longitudes = df["longitude"].mean()

# Get maximum and minimum values for latitude and longitude
max_lat = df["latitude"].max()
min_lat = df["latitude"].min()
max_long = df["longitude"].max()
min_long = df["longitude"].min()

st.title("The Bills")

left_panel, right_panel = st.columns(2)


with left_panel:
    # center on Liberty Bell, add marker
    m = folium.Map(location=[mean_latitudes, mean_longitudes], zoom_start=16)

    for row in df.iter_rows(named=True):
        bill = bills_dict[row["hash"]]

        lis = get_bill_popup(bill)

        popup = folium.Popup(lis, max_width=300, min_width=300)
        folium.Marker([row["latitude"], row["longitude"]], popup=popup, tooltip=row["restaurant"]).add_to(m)

    m.fit_bounds([[min_lat, min_long], [max_lat, max_long]])

    st_data = st_folium(m, width=725, height=500)

    bounds = st_data["bounds"]
    _southWest = bounds["_southWest"]
    _northEast = bounds["_northEast"]

    filtered_range_df = df.filter(
        pl.col("latitude").is_between(_southWest["lat"], _northEast["lat"])
        & pl.col("longitude").is_between(_southWest["lng"], _northEast["lng"]),
    )


# Right panel
with right_panel:
    st.header("Historic totals")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            "Total price",
            f"£{total_price:.2f}",
            delta=None,
            delta_color="normal",
            help=None,
            label_visibility="visible",
        )
    with col2:
        st.metric(
            "Mean price", f"£{mean_prices:.2f}", delta=None, delta_color="normal", help=None, label_visibility="visible"
        )
    with col3:
        st.metric(
            "Mean tip", f"£{mean_tip:.2f}", delta=None, delta_color="normal", help=None, label_visibility="visible"
        )

    st.header("In the map")
    region_mean_prices, region_mean_tip, region_total_price = aggregate_values(filtered_range_df)
    col1, col2, col3 = st.columns(3)

    def get_filtered_metric_args(value, mean_value):
        delta = value - mean_value
        kwargs = {
            "help": None,
            "label_visibility": "visible",
            "delta": f"£{delta:.2f}",
            "delta_color": "inverse",
        }
        if delta == 0 or value == 0:
            kwargs["delta_color"] = "off"
            kwargs["delta"] = None
        return kwargs

    with col1:
        mean_price_kwargs = get_filtered_metric_args(region_total_price, total_price)
        st.metric("Total price", f"£{region_total_price:.2f}", **mean_price_kwargs)

    with col2:
        mean_price_kwargs = get_filtered_metric_args(region_mean_prices, mean_prices)
        st.metric("Mean price", f"£{region_mean_prices:.2f}", **mean_price_kwargs)

    with col3:
        mean_tip_kwargs = get_filtered_metric_args(region_mean_tip, mean_tip)
        st.metric("Mean tip", f"£{region_mean_tip:.2f}", **mean_tip_kwargs)
