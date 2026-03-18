import geopandas as gpd
import pandas as pd
import numpy as np

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
water_points = []
hospital_points = []

# load all files first
for file, label in files:

    gdf = gpd.read_file(file)

    gdf["lat"] = gdf.geometry.centroid.y
    gdf["lng"] = gdf.geometry.centroid.x

    gdf["type"] = type_map[label]

    if label == "water":
        water_points = gdf[["lat", "lng"]].values

    if label == "hospital":
        hospital_points = gdf[["lat", "lng"]].values

    all_data.append(gdf)


# combine all
gdf = pd.concat(all_data)


def distance(p, points):
    if len(points) == 0:
        return 0
    d = np.sqrt((points[:,0] - p[0])**2 + (points[:,1] - p[1])**2)
    return np.min(d)


dist_water = []
dist_hospital = []

for i, row in gdf.iterrows():

    p = [row["lat"], row["lng"]]

    dist_water.append(distance(p, water_points))
    dist_hospital.append(distance(p, hospital_points))


gdf["dist_water"] = dist_water
gdf["dist_hospital"] = dist_hospital


# risk logic
gdf["risk"] = 0

gdf.loc[gdf["dist_water"] < 0.01, "risk"] = 2
gdf.loc[gdf["dist_hospital"] < 0.01, "risk"] = 0


df = gdf[[
    "lat",
    "lng",
    "type",
    "dist_water",
    "dist_hospital",
    "risk"
]]

df.to_csv("final_dataset.csv", index=False)

print("Dataset with distance created")