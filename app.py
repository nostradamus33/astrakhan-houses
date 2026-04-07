import os
import csv
import re
from flask import Flask, render_template, jsonify, request

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "data", "houses_geocoded.csv")


def load_houses():
    houses = []
    if not os.path.exists(DATA_FILE):
        return houses
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            wear_num = None
            wear_str = row.get("wear_percent", "")
            if wear_str:
                nums = re.findall(r'[\d.,]+', wear_str)
                if nums:
                    try:
                        wear_num = float(nums[0].replace(",", "."))
                    except ValueError:
                        pass
            year_num = None
            year_str = row.get("year_built", "")
            if year_str:
                nums = re.findall(r'\d{4}', year_str)
                if nums:
                    try:
                        year_num = int(nums[0])
                    except ValueError:
                        pass
            lat, lon = None, None
            try:
                lat = float(row.get("lat", ""))
                lon = float(row.get("lon", ""))
            except (ValueError, TypeError):
                pass
            houses.append({
                "url": row.get("url", ""),
                "address": row.get("address", ""),
                "year_built": year_str,
                "year_num": year_num,
                "condition": row.get("condition", ""),
                "wear_percent": wear_str,
                "wear_num": wear_num,
                "lat": lat,
                "lon": lon,
            })
    return houses


ALL_HOUSES = load_houses()


@app.route("/")
def index():
    conditions = sorted(set(h["condition"] for h in ALL_HOUSES if h["condition"]))
    years = sorted(set(h["year_num"] for h in ALL_HOUSES if h["year_num"]))
    min_year = min(years) if years else 1900
    max_year = max(years) if years else 2025
    stats = {
        "total": len(ALL_HOUSES),
        "with_coords": sum(1 for h in ALL_HOUSES if h["lat"]),
        "with_wear": sum(1 for h in ALL_HOUSES if h["wear_num"] is not None),
        "conditions": conditions,
        "min_year": min_year,
        "max_year": max_year,
    }
    return render_template("index.html", stats=stats)


@app.route("/api/houses")
def api_houses():
    condition = request.args.get("condition", "").strip()
    year_from = request.args.get("year_from", type=int)
    year_to = request.args.get("year_to", type=int)
    wear_from = request.args.get("wear_from", type=float)
    wear_to = request.args.get("wear_to", type=float)
    search = request.args.get("search", "").strip().lower()
    filtered = []
    for h in ALL_HOUSES:
        if not h["lat"] or not h["lon"]:
            continue
        if condition and h["condition"] != condition:
            continue
        if year_from and (not h["year_num"] or h["year_num"] < year_from):
            continue
        if year_to and (not h["year_num"] or h["year_num"] > year_to):
            continue
        if wear_from is not None and (h["wear_num"] is None or h["wear_num"] < wear_from):
            continue
        if wear_to is not None and (h["wear_num"] is None or h["wear_num"] > wear_to):
            continue
        if search and search not in h["address"].lower():
            continue
        filtered.append({
            "url": h["url"],
            "address": h["address"],
            "year_built": h["year_built"],
            "condition": h["condition"],
            "wear_percent": h["wear_percent"],
            "wear_num": h["wear_num"],
            "lat": h["lat"],
            "lon": h["lon"],
        })
    return jsonify({"count": len(filtered), "houses": filtered})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
