import json
from datetime import datetime
from pathlib import Path

import polars as pl

bills_path = Path("bills")

def read_bills():
    _bills = []
    for bill_file in bills_path.glob("*.json"):
        with open(bill_file) as f:
            bills = json.load(f)["bills"]
            for bill in bills:
                bill['region'] = bill_file.stem
                _bills.append(bill)
    return _bills


def bills_to_df(bills):
    aggregated_bills = []
    for bill in bills:
        total = bill.get("tip", 0) + bill.get("delivery_charge", 0)
        bill["date"] = datetime.fromisoformat(bill["date"])
        for item in bill.pop("items"):
            total += item["price"] * item["quantity"]
        bill["total"] = total
        aggregated_bills.append(bill)

    return pl.from_records(aggregated_bills)
