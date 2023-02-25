import folium

from jinja2 import Environment, FileSystemLoader

env = Environment(loader=FileSystemLoader("."))


template = env.get_template("bill.html.jinja")


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
