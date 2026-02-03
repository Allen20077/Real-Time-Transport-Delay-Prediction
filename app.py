from flask import Flask, render_template, request, jsonify
import pandas as pd
import math
import time
import random

app = Flask(__name__)

# ================= LOAD GTFS (BMTC) =================
routes = pd.read_csv("gtfs/routes.txt", encoding="utf-8", on_bad_lines="skip")
stops = pd.read_csv("gtfs/stops.txt", encoding="utf-8", on_bad_lines="skip")

# Force numeric conversion (VERY IMPORTANT)
stops["stop_lat"] = pd.to_numeric(stops["stop_lat"], errors="coerce")
stops["stop_lon"] = pd.to_numeric(stops["stop_lon"], errors="coerce")

# Drop bad rows if any
stops = stops.dropna(subset=["stop_lat", "stop_lon"])

stop_times = pd.read_csv("gtfs/stop_times.txt", encoding="utf-8", on_bad_lines="skip")
trips = pd.read_csv("gtfs/trips.txt", encoding="utf-8", on_bad_lines="skip")
shapes = pd.read_csv("gtfs/shapes.txt", encoding="utf-8", on_bad_lines="skip")

# ================= HELPERS =================
def distance(lat1, lon1, lat2, lon2):
    return math.sqrt((lat1 - lat2)**2 + (lon1 - lon2)**2)

# ================= ROUTES =================
@app.route("/")
def index():
    return render_template("index.html")
@app.route("/bmtc/route")
def bmtc_route():
    route_short = request.args.get("route")

    # find route_id
    route_row = routes[routes.route_short_name == route_short]
    if route_row.empty:
        return jsonify({"points": []})

    route_id = route_row.iloc[0].route_id

    # find trips for route
    trip_ids = trips[trips.route_id == route_id].trip_id.unique()
    if len(trip_ids) == 0:
        return jsonify({"points": []})

    # find shape_id
    shape_id = trips[trips.trip_id == trip_ids[0]].shape_id.iloc[0]

    # get shape points
    shape_points = shapes[
        shapes.shape_id == shape_id
    ].sort_values("shape_pt_sequence")

    points = shape_points[["shape_pt_lat", "shape_pt_lon"]].values.tolist()
    return jsonify({"points": points})

@app.route("/live_delay")
def live_delay():
    return jsonify({
        "delay": random.randint(0, 15),
        "updated": time.strftime("%H:%M:%S")
    })

# 🔥 CORE FEATURE: REAL BMTC BUS NUMBERS
@app.route("/bmtc/buses")
def bmtc_buses():
    lat = float(request.args.get("lat"))
    lng = float(request.args.get("lng"))

    # Find nearby stops (~1 km)
    nearby_stops = stops[
        ((stops.stop_lat - lat).abs() +
         (stops.stop_lon - lng).abs()) < 0.02
    ]

    if nearby_stops.empty:
        return jsonify({"buses": []})

    stop_ids = nearby_stops.stop_id.tolist()

    trip_ids = stop_times[
        stop_times.stop_id.isin(stop_ids)
    ].trip_id.unique()

    route_ids = trips[
        trips.trip_id.isin(trip_ids)
    ].route_id.unique()

    bus_numbers = routes[
        routes.route_id.isin(route_ids)
    ]["route_short_name"].dropna().unique().tolist()

    return jsonify({
        "city": "Bengaluru",
        "authority": "BMTC",
        "buses": sorted(bus_numbers)
    })


if __name__ == "__main__":
    app.run(debug=True)
