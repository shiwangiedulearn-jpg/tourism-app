import joblib
import pandas as pd
import numpy as np
import geopandas as gpd
import osmnx as ox
import networkx as nx
import requests
from datetime import datetime


model = joblib.load("risk_model.pkl")



water_gdf = gpd.read_file("water.geojson")
hospital_gdf = gpd.read_file("hospital.geojson")
building_gdf = gpd.read_file("building.geojson")

cluster_df = pd.read_csv("clustered_dataset.csv")

cluster_points = cluster_df[["lat","lng"]].values
cluster_values = cluster_df["cluster"].values

def get_cluster(lat, lng):

    if len(cluster_points) == 0:
        return 0

    p = np.array([lat, lng])

    d = np.sqrt(
        (cluster_points[:,0] - p[0])**2 +
        (cluster_points[:,1] - p[1])**2
    )

    idx = np.argmin(d)

    return int(cluster_values[idx])

def get_points(gdf):

    gdf = gdf.to_crs(epsg=3857)

    centroids = gdf.geometry.centroid

    centroids = gpd.GeoSeries(
        centroids,
        crs=3857
    ).to_crs(4326)

    gdf["lat"] = centroids.y
    gdf["lng"] = centroids.x

    return gdf[["lat", "lng"]].values


water_points = get_points(water_gdf)
hospital_points = get_points(hospital_gdf)
building_points = get_points(building_gdf)




def distance(p, points):

    if len(points) == 0:
        return 0

    d = np.sqrt(
        (points[:,0] - p[0])**2 +
        (points[:,1] - p[1])**2
    )

    return np.min(d)


def density(p, points):

    if len(points) == 0:
        return 0

    d = np.sqrt(
        (points[:,0] - p[0])**2 +
        (points[:,1] - p[1])**2
    )

    return np.sum(d < 0.01)

def near_points(route, points, radius=0.01):

    count = 0

    for r in route:

        for p in points:

            d = np.sqrt(
                (r[0]-p[0])**2 +
                (r[1]-p[1])**2
            )

            if d < radius:
                count += 1

    return count



def generate_route(start, end):

    lat1, lng1 = start
    lat2, lng2 = end

    G = ox.graph_from_point(
        (lat1, lng1),
        dist=20000,
        network_type="drive"
    )

    orig = ox.nearest_nodes(G, lng1, lat1)
    dest = ox.nearest_nodes(G, lng2, lat2)

    route = nx.shortest_path(G, orig, dest, weight="length")

    coords = []

    for node in route:

        y = G.nodes[node]["y"]
        x = G.nodes[node]["x"]

        coords.append([y, x])

    coords = coords[::5]

    return coords




def get_weather(lat, lng):

    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lng}&current_weather=true"

    try:

        data = requests.get(url).json()

        code = data["current_weather"]["weathercode"]

        if code == 0:
            return 0
        elif code < 60:
            return 1
        else:
            return 2

    except:
        return 1




def get_hill(lat, lng):

    url = f"https://api.open-meteo.com/v1/elevation?latitude={lat}&longitude={lng}"

    try:

        data = requests.get(url).json()

        elevation = data["elevation"][0]

        if elevation > 400:
            return 1
        else:
            return 0

    except:
        return 0




def predict_risk(lat, lng):

    type_val = 2
    road_type_val = 1

    dist_water = distance([lat,lng], water_points)
    dist_hospital = distance([lat,lng], hospital_points)

    building_density = density([lat,lng], building_points)
    cluster = get_cluster(lat, lng)

    weather_val = get_weather(lat, lng)
    hill_val = get_hill(lat, lng)

    
    hour = datetime.now().hour

    if hour > 18 or hour < 6:
        time_val = 1
    else:
        time_val = 0

    
    if building_density < 3 and time_val == 1:
        crime_val = 2
    elif building_density < 5:
        crime_val = 1
    else:
        crime_val = 0

    # network
    if building_density < 3:
        network_val = 1
    else:
        network_val = 0


    data = pd.DataFrame(
        [[
            lat,
            lng,
            type_val,
            road_type_val,
            dist_water,
            dist_hospital,
            building_density,
            cluster,
            time_val,
            weather_val,
            hill_val,
            crime_val,
            network_val
        ]],
        columns=[
            "lat",
            "lng",
            "type",
            "road_type",
            "dist_water",
            "dist_hospital",
            "building_density",
            "cluster",
            "time",
            "weather",
            "hill",
            "crime",
            "network"
        ]
    )


    pred = model.predict(data)[0]

    return pred

def get_safe_route(start, end):

    route1 = generate_route(start, end)

    route2 = generate_route(
        start,
        [end[0] + 0.01, end[1]]
    )

    route3 = generate_route(
        start,
        [end[0], end[1] + 0.01]
    )


    def route_risk(route):

        total = 0
        zones = []

        for p in route:

            r = predict_risk(p[0], p[1])

            total += r

            if r == 0:
                zones.append("green")
            elif r == 1:
                zones.append("yellow")
            else:
                zones.append("red")

        return total, zones


    r1, z1 = route_risk(route1)
    r2, z2 = route_risk(route2)
    r3, z3 = route_risk(route3)


    print("Route1 risk:", r1)
    print("Route2 risk:", r2)
    print("Route3 risk:", r3)


    if r1 <= r2 and r1 <= r3:

        best = route1
        zones = z1
        print("Route1 safer")

    elif r2 <= r3:

        best = route2
        zones = z2
        print("Route2 safer")

    else:

        best = route3
        zones = z3
        print("Route3 safer")


    print("Hospitals:", near_points(best, hospital_points))
    print("Water:", near_points(best, water_points))
    print("Buildings:", near_points(best, building_points))


    return best, zones

if __name__ == "__main__":

    print("Enter start location")
    lat1 = float(input("Start latitude: "))
    lng1 = float(input("Start longitude: "))

    print("Enter end location")
    lat2 = float(input("End latitude: "))
    lng2 = float(input("End longitude: "))

    start = [lat1, lng1]
    end = [lat2, lng2]

    route, zones = get_safe_route(start, end)

    print("Route length:", len(route))

    for i in range(len(route)):

        print(
            route[i],
            "zone:",
            zones[i]
        )   