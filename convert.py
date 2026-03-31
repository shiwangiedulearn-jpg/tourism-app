import geopandas as gpd
import pandas as pd
import numpy as np
from datetime import datetime


    
files = [
    ("road.geojson", "road"),
    ("hospital.geojson", "hospital"),
    ("water.geojson", "water"),
    ("tourism.geojson", "tourism"),
    ("forest.geojson", "forest"),
    ("building.geojson", "building"),
]

type_map = {
    "road": 0,
    "hospital": 1,
    "water": 2,
    "tourism": 3,
    "forest": 4,
    "building": 5,
}

all_data = []

road_points = []
hospital_points = []
water_points = []
forest_points = []
building_points = []



for file, label in files:

    gdf = gpd.read_file(file)

    gdf = gdf.to_crs(epsg=3857)

    centroids = gdf.geometry.centroid

    centroids = gpd.GeoSeries(
        centroids,
        crs=3857
    ).to_crs(4326)

    gdf["lat"] = centroids.y
    gdf["lng"] = centroids.x

    gdf["type"] = type_map[label]
    gdf["road_type"] = 1

    if label == "road":
        road_points = gdf[["lat","lng"]].values

    if label == "hospital":
        hospital_points = gdf[["lat","lng"]].values

    if label == "water":
        water_points = gdf[["lat","lng"]].values

    if label == "forest":
        forest_points = gdf[["lat","lng"]].values
    if label == "building":
        building_points = gdf[["lat","lng"]].values
    all_data.append(gdf)


gdf = pd.concat(all_data)


import numpy as np

def haversine(p, points):

    if len(points) == 0:
        return 0

    lat1 = np.radians(p[0])
    lon1 = np.radians(p[1])

    lat2 = np.radians(points[:,0])
    lon2 = np.radians(points[:,1])

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
    c = 2 * np.arcsin(np.sqrt(a))

    R = 6371  

    return np.min(R * c)


def density(p, points, radius=1):  # radius in km

    if len(points) == 0:
        return 0

    lat1 = np.radians(p[0])
    lon1 = np.radians(p[1])

    lat2 = np.radians(points[:,0])
    lon2 = np.radians(points[:,1])

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
    c = 2 * np.arcsin(np.sqrt(a))

    R = 6371

    dist = R * c

    return np.sum(dist < radius)



dist_hospital = []
dist_water = []
dist_road = []
forest_density = []
building_density = []

elevation = []
slope = []
landslide = []

weather = []
time_list = []
network = []


hour = datetime.now().hour


for i, row in gdf.iterrows():

    p = [row["lat"], row["lng"]]

    
    dist_hospital.append(haversine(p, hospital_points))
    dist_water.append(haversine(p, water_points))
    dist_road.append(haversine(p, road_points))

    
    forest_density.append(density(p, forest_points))
    
    building_density.append(density(p, building_points))

    
    elevation_val = 300 + (row["lat"] -31) * 1000
    elevation.append(elevation_val)

    
    slope_val = abs((row["lat"] * 100) % 60)
    slope.append(slope_val)

    
    if hour > 18 or hour < 6:
        time_list.append(1)
    else:
        time_list.append(0)

    
    weather.append(0)

    
    if slope_val > 50:
        landslide.append(1)
    else:
        landslide.append(0)

    if building_density[-1] < 3:
        network.append(1)
    else:
        network.append(0)




gdf["dist_hospital"] = dist_hospital
gdf["dist_water"] = dist_water
gdf["dist_road"] = dist_road
gdf["forest_density"] = forest_density
gdf["building_density"] = building_density

gdf["elevation"] = elevation
gdf["slope"] = slope
gdf["landslide"] = landslide

gdf["time"] = time_list
gdf["weather"] = weather
gdf["network"] = network


# =========================
# RISK CALCULATION
# =========================

gdf["risk"] = 0

gdf.loc[gdf["dist_hospital"] > 5, "risk"] += 1
gdf.loc[gdf["dist_road"] > 2, "risk"] += 1
gdf.loc[gdf["weather"] >= 1, "risk"] += 1
gdf.loc[gdf["slope"] > 40, "risk"] += 1
gdf.loc[gdf["landslide"] == 1, "risk"] += 2
gdf.loc[gdf["time"] == 1, "risk"] += 1
gdf.loc[gdf["network"] == 1, "risk"] += 1
gdf.loc[gdf["building_density"] < 3, "risk"] += 1

gdf["risk"] = gdf["risk"].clip(0,2)


# =========================
# FINAL DATASET
# =========================

df = gdf[
    [
        "lat",
        "lng",
        "type",
        "road_type",
        "dist_water",
        "dist_hospital",
        "dist_road",
        "forest_density",
        "building_density",
        "time",
        "weather",
        "elevation",
        "slope",
        "landslide",
        "network",
        "risk"
    ]
]


df.to_csv("final_dataset.csv", index=False)

print("Trekking dataset created")