import joblib
import pandas as pd
import numpy as np
import geopandas as gpd

model = joblib.load("risk_model.pkl")


water = gpd.read_file("water.geojson")
hospital = gpd.read_file("hospital.geojson")
buildings = gpd.read_file("building.geojson")
road = gpd.read_file("road.geojson")

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
road_points = get_points(road)

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

lat = float(input("Enter latitude: "))
lng = float(input("Enter longitude: "))
type_val = 2

dist_water = distance([lat,lng], water_points)

dist_hospital = distance([lat,lng], hospital_points)

building_density = density([lat,lng], building_points)

road_type = 1   

cluster = 0     

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

pred = model.predict(data)

print("Location:", lat, lng)
print("Water dist:", dist_water)
print("Hospital dist:", dist_hospital)
print("Building density:", building_density)
print("Cluster:", cluster)
print("Risk:", pred)
