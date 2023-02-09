import json
import polars as pl
import streamlit as st
from jinja2 import Environment, FileSystemLoader, select_autoescape

env = Environment(loader=FileSystemLoader("."))


template = env.get_template("bill.html.jinja")

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


def calculate_values(df):
    if df.is_empty():
        return 0, 0, 0
    mean_prices = df["total"].mean()
    mean_tip = df["tip"].mean()
    total_price = df["total"].sum()
    return mean_prices, mean_tip, total_price


mean_prices, mean_tip, total_price = calculate_values(df)

mean_latitudes = df["latitude"].mean()
mean_longitudes = df["longitude"].mean()

# Get maximum and minimum values for latitude and longitude
max_lat = df["latitude"].max()
min_lat = df["latitude"].min()
max_long = df["longitude"].max()
min_long = df["longitude"].min()

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Total price", f"£{total_price:.2f}", delta=None, delta_color="normal", help=None, label_visibility="visible"
    )

with col2:
    st.metric(
        "Mean price", f"£{mean_prices:.2f}", delta=None, delta_color="normal", help=None, label_visibility="visible"
    )

with col3:
    st.metric("Mean tip", f"£{mean_tip:.2f}", delta=None, delta_color="normal", help=None, label_visibility="visible")

# appointment = st.slider(
#     "Schedule your appointment:",
#     value=(df["date"].min().date(), df["date"].max().date()))


import folium

from streamlit_folium import st_folium

# center on Liberty Bell, add marker
m = folium.Map(location=[mean_latitudes, mean_longitudes], zoom_start=16)


SPACE_CHAR = "-"
NBSP_CHAR = "&nbsp;"


def get_bill_popup(bill):
    max_len_name = 0
    max_len_price = 0
    max_len_qty = 0
    padding_value = 2

    for item in bill["items"]:
        qty = item.get("quantity", 1)
        max_len_name = max(len(item["name"]), max_len_name)
        max_len_price = max(len(str(int(item["price"] * qty))), max_len_price)
        max_len_qty = max(len(str(qty)), max_len_qty)

    line_format = f"<p>{{quantity:0{max_len_qty}}}x {{product_name}}{{spaces}}${{price:2.2f}}</p>"

    full_line_length = max_len_name + max_len_price + max_len_qty + padding_value + 6
    lis = []

    rendered_item = {
        "restaurant": bill["restaurant"],
        "date": bill["date"].strftime("%d/%m/%Y"),
        "delivery": bill.get("delivery"),
        "separator": "".join([SPACE_CHAR for _ in range(full_line_length)]),
        "items": [],
    }
    for item in bill["items"]:
        qty = item.get("quantity", 1)
        price = item["price"] * qty
        spaces = (max_len_name + padding_value) - len(item["name"])
        spaces = "".join([SPACE_CHAR for _ in range(spaces)])
        rendered_item["items"].append(
            line_format.format(quantity=qty, product_name=item["name"], spaces=spaces, price=price)
        )

    if bill.get("tip"):
        word = "Tip"
        content = f" {word}: ${bill['tip']:0.2f}"
        spaces = (full_line_length) - len(content)
        rendered_item["tip"] = "".join([NBSP_CHAR for _ in range(spaces)]) + content

    if bill.get("delivery"):
        word = "Delivery"
        content = f" {word}: ${bill['delivery']:0.2f}"
        spaces = (full_line_length) - len(content)
        rendered_item["delivery"] = "".join([NBSP_CHAR for _ in range(spaces)]) + content

    word = "Total"
    content = f" {word}: ${bill['total']:0.2f}"
    spaces = (full_line_length) - len(content)
    rendered_item["total"] = "".join([NBSP_CHAR for _ in range(spaces)]) + content

    iframe = folium.IFrame(template.render(**rendered_item))

    return iframe


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


region_mean_prices, region_mean_tip, region_total_price = calculate_values(filtered_range_df)
col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Total price",
        f"£{region_total_price:.2f}",
        delta=None,
        delta_color="normal",
        help=None,
        label_visibility="visible",
    )

with col2:
    mean_price_kwargs = {}
    delta = region_mean_prices - mean_prices
    mean_price_kwargs["delta"] = f"{delta:.2f}"
    mean_price_kwargs["delta_color"] = "inverse"
    if delta == 0 or region_mean_prices == 0:
        delta_color = "off"
        mean_price_kwargs["delta"] = None
    st.metric("Mean price", f"£{region_mean_prices:.2f}", help=None, label_visibility="visible", **mean_price_kwargs)

with col3:
    mean_tip_kwargs = {}
    delta = region_mean_tip - mean_tip
    mean_tip_kwargs["delta"] = f"{delta:.2f}"
    mean_tip_kwargs["delta_color"] = "inverse"
    if delta == 0 or region_mean_tip == 0:
        delta_color = "off"
        mean_tip_kwargs["delta"] = None
    st.metric("Mean tip", f"£{region_mean_tip:.2f}", help=None, label_visibility="visible", **mean_tip_kwargs)
