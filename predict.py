import joblib
import pandas as pd
import numpy as np
import geopandas as gpd
from datetime import datetime
import requests
from sklearn.metrics.pairwise import haversine_distances
from dotenv import load_dotenv
load_dotenv()

model = joblib.load("risk_model.pkl")



water = gpd.read_file("water.geojson")
hospital = gpd.read_file("hospital.geojson")
buildings = gpd.read_file("building.geojson")
road = gpd.read_file("road.geojson")
forest = gpd.read_file("forest.geojson")


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
forest_points = get_points(forest)

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

def density(p, points, radius=5):

    if len(points) == 0:
        return 0

    p_rad = np.radians([p])
    pts_rad = np.radians(points)

    d = haversine_distances(p_rad, pts_rad)[0] * 6371

    return np.sum(d < radius)

def get_weather_details(lat, lng):

    import os
    api_key= os.getenv("WEATHER_API_KEY")

    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lng}&appid={api_key}&units=metric"



    try:
        data = requests.get(url).json()

        rain = data.get("rain", {}).get("1h", 0)
        wind = data["wind"]["speed"]
        temp = data["main"]["temp"]
        visibility = data.get("visibility", 10000) / 1000

        return {
            "rain": rain,
            "wind": wind,
            "temp": temp,
            "visibility": visibility
        }

    except:
        return {
            "rain": 0,
            "wind": 10,
            "temp": 25,
            "visibility": 10
        }


def get_elevation(lat, lng):
    try:
        url = f"https://api.open-meteo.com/v1/elevation?latitude={lat}&longitude={lng}"
        data = requests.get(url).json()
        return data["elevation"][0]
    except:
        return 200


def get_slope(lat, lng):
    e1 = get_elevation(lat, lng)
    e2 = get_elevation(lat + 0.001, lng)
    return abs(e2 - e1)

def get_imd_alert():

    try:
        url = "https://mausam.imd.gov.in/rss/all-india.xml"

        data = requests.get(url).text.lower()

        # simple keyword detection
        if "heavy rain" in data:
            return 1
        elif "storm" in data:
            return 1
        elif "cyclone" in data:
            return 1
        else:
            return 0

    except:
        return 0

lat = float(input("Enter latitude: "))
lng = float(input("Enter longitude: "))

weather_data = get_weather_details(lat, lng)
imd_alert = get_imd_alert()

rain = weather_data["rain"]
wind = weather_data["wind"]
temp = weather_data["temp"]
visibility = weather_data["visibility"]
if rain == 0:
    weather_val = 0
elif rain < 10:
    weather_val = 1
else:
    weather_val = 2

type_val = 2

dist_water = min(haversine([lat,lng], water_points),5)/5

dist_forest = haversine([lat, lng], forest_points)

dist_hospital = min(haversine([lat,lng], hospital_points),10)/10

dist_road = min(haversine([lat,lng], road_points),5)/5

forest_density = density([lat,lng], forest_points)

if dist_forest < 0:
    forest_level = "DENSE"
elif dist_forest < 3:
    forest_level = "MEDIUM"
elif dist_forest < 6:
    forest_level = "LIGHT"
else:
    forest_level = "OPEN"

building_density = density([lat,lng], building_points)

road_type = 1   
cluster = 1

hour = datetime.now().hour
time_val = 1 if (hour > 18 or hour < 6) else 0



elevation_val = get_elevation(lat, lng)

slope_val = get_slope(lat, lng)

landslide_val = 1 if (slope_val > 25 and (rain > 5 or forest_density < 2)) else 0

network_val = 1 if building_density < 3 else 0   

data = pd.DataFrame(
    [[
        lat,
        lng,
        type_val,
        road_type,
        dist_water,
        dist_hospital,
        dist_road,
        forest_density,
        building_density,
        time_val,
        weather_val,
        elevation_val,
        slope_val,
        landslide_val,
        network_val,
        cluster

    ]],
    columns=[
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
        "cluster"
    ]
)

pred = model.predict(data)[0]


flood = int(dist_water < 0.2 and rain > 20)
landslide_rule = int(rain > 15 and slope_val > 30)
storm = int(wind > 50)
low_visibility = int(visibility < 2)
heat = int(temp > 40)
cold = int(temp < 0)
forest_risk = 1 if forest_density > 4 else 0
remote_risk = 1 if (building_density < 10 and dist_road > 0.3) else 0
risk_score = (
    pred * 0.25 +
    flood * 0.15 +
    landslide_rule * 0.2 +
    storm * 0.1+
    cold * 0.1+
    forest_risk * 0.05 +
    remote_risk * 0.05 +
    imd_alert*0.1
)

if dist_road > 0.6:
    risk_score += 0.1

if risk_score < 0.4:
    final = 0
elif risk_score < 0.7:
    final = 1
else:
    final = 2
if slope_val < 5 and building_density > 10:
    final = 0
if elevation_val > 3500 and temp < 0:
    risk_score += 0.1

print("\n FINAL RESULT:")

if final == 0:
    print(" SAFE")
elif final == 1:
    print(" MODERATE RISK")
else:
    print(" DANGEROUS")

print("\nDEBUG:")
print("forest_density:", forest_density)
print("dist_forest:", dist_forest)
print("dist_road:", dist_road)
print("building_density:", building_density)
print("forest_density:", forest_density)

print("\nDETAILS:")
print("Elevation:", elevation_val)
print("Slope:", slope_val)
print("Distance to hospital:", dist_hospital)
print("Distance to water:", dist_water)
print("Building density:", building_density)
print("Cluster:", cluster)
print("Forest density:", forest_density, "(", forest_level, ")")
print("Distance to forest:", dist_forest)

print("\nWEATHER:")
print("Rain:", rain)
print("Wind:", wind)
print("Temperature:", temp)

print("\nDISASTER:")
print("\nIMD ALERT:", imd_alert)
print("Flood:", flood)
print("Landslide:", landslide_rule)
print("Storm:", storm)