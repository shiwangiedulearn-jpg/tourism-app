import geopandas as gpd
import pandas as pd
import numpy as np

road_type_map = {
    "primary": 3,
    "secondary": 2,
    "residential": 1,
    "service": 1,
    "path": 2,
    "footway": 2,
}

files = [
    ("hospital.geojson", "hospital"),
    ("tourism.geojson", "tourism"),
    ("road.geojson", "road"),
    ("water.geojson", "water"),
    ("place.geojson", "place"),
]

type_map = {
    "hospital": 0,
    "tourism": 1,
    "road": 2,
    "water": 3,
    "place": 4,
}

all_data = []
building_points = []
water_points = []
hospital_points = []


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

    if label == "road":

        if "highway" in gdf.columns:
            gdf["road_type"] = gdf["highway"].map(road_type_map).fillna(1)
        else:
            gdf["road_type"] = 1

    else:
        gdf["road_type"] = 0    
    if label == "water":
        water_points = gdf[["lat", "lng"]].values

    if label == "hospital":
        hospital_points = gdf[["lat", "lng"]].values

    all_data.append(gdf)
buildings = gpd.read_file("building.geojson")

build_proj = buildings.to_crs(epsg=3857)

centroids = build_proj.geometry.centroid

centroids = gpd.GeoSeries(
    centroids,
    crs=3857
).to_crs(4326)

buildings["lat"] = centroids.y
buildings["lng"] = centroids.x

building_points = buildings[["lat","lng"]].values


gdf = pd.concat(all_data)


def distance(p, points):
    if len(points) == 0:
        return 0
    d = np.sqrt((points[:,0] - p[0])**2 + (points[:,1] - p[1])**2)
    return np.min(d)
def density(p, points):

    if len(points) == 0:
        return 0

    d = np.sqrt(
        (points[:,0] - p[0])**2 +
        (points[:,1] - p[1])**2
    )

    return np.sum(d < 0.01)

dist_water = []
dist_hospital = []
building_density = []

for i, row in gdf.iterrows():

    p = [row["lat"], row["lng"]]

    dist_water.append(distance(p, water_points))
    dist_hospital.append(distance(p, hospital_points))

    building_density.append(
        density(p, building_points)
    )


gdf["dist_water"] = dist_water
gdf["dist_hospital"] = dist_hospital
gdf["building_density"] = building_density

import random

time_of_day = []

for i in range(len(gdf)):
    time_of_day.append(random.randint(0, 1))  
    # 0 = day
    # 1 = night

gdf["time"] = time_of_day
gdf["risk"] = 1  

gdf.loc[gdf["dist_water"] < 0.01, "risk"] = 2

gdf.loc[gdf["dist_hospital"] > 0.03, "risk"] = 2

gdf.loc[gdf["building_density"] < 3, "risk"] = 2

gdf.loc[gdf["time"] == 1, "risk"] += 1

gdf["risk"] = gdf["risk"].clip(0, 2)



safe = gdf[gdf["risk"] == 0]
medium = gdf[gdf["risk"] == 1]
danger = gdf[gdf["risk"] == 2]

n = min(len(safe), len(medium), len(danger))

if n > 0:
    safe = safe.sample(n)
    medium = medium.sample(n)
    danger = danger.sample(n)
    gdf = pd.concat([safe, medium, danger])



df = gdf[
    [
        "lat",
        "lng",
        "type",
        "road_type",
        "dist_water",
        "dist_hospital",
        "building_density",
        "time",
        "risk"
    ]
]



df.to_csv("final_dataset.csv", index=False)

print("Dataset with distance created")