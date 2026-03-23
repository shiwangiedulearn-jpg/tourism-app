import joblib
import pandas as pd
import numpy as np
import geopandas as gpd
import osmnx as ox
import networkx as nx

model = joblib.load("risk_model.pkl")
water = gpd.read_file("water.geojson")
hospital = gpd.read_file("hospital.geojson")
buildings = gpd.read_file("building.geojson")

cluster_df = pd.read_csv("clustered_dataset.csv")

cluster_points = cluster_df[["lat", "lng"]].values
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

    return gdf[["lat","lng"]].values


water_points = get_points(water)
hospital_points = get_points(hospital)
building_points = get_points(buildings)

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


print("Enter start location")
lat1 = float(input("Start latitude: "))
lng1 = float(input("Start longitude: "))

print("Enter end location")
lat2 = float(input("End latitude: "))
lng2 = float(input("End longitude: "))

start = [lat1, lng1]
end = [lat2, lng2]

def generate_route(start, end):

    lat1, lng1 = start
    lat2, lng2 = end

    G = ox.graph_from_point(
        (lat1, lng1),
        dist=30000,
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

    return coords


route = generate_route(start, end)

def predict_risk(lat, lng):

    type_val = 2

    dist_water = distance([lat,lng], water_points)
    dist_hospital = distance([lat,lng], hospital_points)

    building_density = density([lat,lng], building_points)

    cluster = get_cluster(lat, lng)

    data = pd.DataFrame(
        [[
            lat,
            lng,
            type_val,
            dist_water,
            dist_hospital,
            building_density,
            cluster
        ]],
        columns=[
            "lat",
            "lng",
            "type",
            "dist_water",
            "dist_hospital",
            "building_density",
            "cluster",
        ]
    )

    pred = model.predict(data)[0]
    print("point:", lat, lng, "risk:", pred)

    return pred

total_risk = 0

for p in route:

    lat, lng = p

    r = predict_risk(lat, lng)

    total_risk += r

print("Total route risk:", total_risk)
print("Enter second end location")

lat3 = float(input("End2 latitude: "))
lng3 = float(input("End2 longitude: "))

end2 = [lat3, lng3]

route2 = generate_route(start, end2)

def route_risk(route):

    total = 0

    for p in route:

        total += predict_risk(p[0], p[1])

    return total


r1 = route_risk(route)
r2 = route_risk(route2)

print("Route1:", r1)
print("Route2:", r2)

print("Route1 length:", len(route))
print("Route2 length:", len(route2))

print(route[:5])
print(route2[:5])

if r1 < r2:
    print("Route1 is safer")
elif r2 < r1:
    print("Route2 is safer")
else:
    print("Both routes have same risk")

