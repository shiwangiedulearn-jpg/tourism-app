import joblib
import pandas as pd
import numpy as np
import geopandas as gpd
import osmnx as ox
import networkx as nx
import requests
from datetime import datetime



model = joblib.load("risk_model.pkl")



water = gpd.read_file("water.geojson")
hospital = gpd.read_file("hospital.geojson")
building = gpd.read_file("building.geojson")
road = gpd.read_file("road.geojson")
forest = gpd.read_file("forest.geojson")

cluster_df = pd.read_csv("clustered_dataset.csv")

cluster_points = cluster_df[["lat","lng"]].values
cluster_values = cluster_df["cluster"].values

def get_cluster(lat, lng):

    if len(cluster_points) == 0:
        return 0

    distances = []

    for pt in cluster_points:
        d = haversine([lat, lng], np.array([pt]))
        distances.append(d)

    idx = np.argmin(distances)

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


water_points = get_points(water)
hospital_points = get_points(hospital)
building_points = get_points(building)
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

    a = np.sin(dlat/2)**2 + np.cos(lat1)*np.cos(lat2)*np.sin(dlon/2)**2
    c = 2 * np.arcsin(np.sqrt(a))

    R = 6371
    return np.min(R * c)


def density(p, points):

    if len(points) == 0:
        return 0

    lat1 = np.radians(p[0])
    lon1 = np.radians(p[1])

    lat2 = np.radians(points[:,0])
    lon2 = np.radians(points[:,1])

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = np.sin(dlat/2)**2 + np.cos(lat1)*np.cos(lat2)*np.sin(dlon/2)**2
    c = 2 * np.arcsin(np.sqrt(a))

    R = 6371
    dist = R * c

    return np.sum(dist < 1)

def predict_risk(lat, lng):

    
    dist_hospital = min(haversine([lat, lng], hospital_points), 10) / 10
    dist_water = min(haversine([lat, lng], water_points), 5) / 5
    dist_road = min(haversine([lat, lng], road_points), 5) / 5

    
    building_density = density([lat, lng], building_points)
    forest_density = density([lat, lng], forest_points)
    network = 0 if building_density > 10 else 1

    
    elevation = get_elevation(lat, lng)

    
    slope = abs(get_elevation(lat + 0.001, lng) - elevation)

    
    risk = 0

    if slope > 25:
        risk += 1

    if dist_road > 0.6:
        risk += 1

    if building_density < 5:
        risk += 1

    if forest_density > 5:
        risk += 1

    if elevation > 3000:
        risk += 1

    return {
      "risk": min(risk, 2),
      "hospital": dist_hospital,
      "building": building_density,
      "forest": forest_density,
      "network": network
}

def near_points(route, points, radius=0.01):

    count = 0

    for r in route:

        for p in points:

            d = haversine(r, np.array([p]))

            if d < 1:
                count += 1

    return count



def generate_routes(start, end):

    lat1, lng1 = start
    lat2, lng2 = end

    G = ox.graph_from_point((lat1, lng1), dist=20000, network_type="drive")

    orig = ox.nearest_nodes(G, lng1, lat1)
    dest = ox.nearest_nodes(G, lng2, lat2)

    
    route1 = nx.shortest_path(G, orig, dest, weight="length")

    
    route2 = nx.shortest_path(G, orig, dest, weight="travel_time")

    def convert(route):
        coords = []
        for node in route:
            coords.append([G.nodes[node]["y"], G.nodes[node]["x"]])
        return coords[::5]

    return convert(route1), convert(route2)




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


def get_elevation(lat, lng):
    try:
        url = f"https://api.open-meteo.com/v1/elevation?latitude={lat}&longitude={lng}"
        data = requests.get(url).json()
        return data["elevation"][0]
    except:
        return 200




def route_risk(route):

    total_score = 0
    zones = []

    for p in route:

        result = predict_risk(p[0], p[1])
        level = result["risk"]

        zones.append(level)

        
        score = (
            level * 3 +                       
            (result["network"] * 1) +           
            (result["building"] < 5) * 2 +      
            (result["forest"] > 5) * 1          
        )

        total_score += score

    avg_score = total_score / len(route)

    return avg_score, zones

def summarize_route(route):

    total_hospital = 0
    total_building = 0
    total_forest = 0
    total_network = 0

    for p in route:

        result = predict_risk(p[0], p[1])
        near_hospital = find_nearby(p, hospital_points)

        total_hospital += len(near_hospital)
        total_building += result["building"]
        total_forest += result["forest"]
        total_network += result["network"]

    n = len(route)

    return {
        "hospitals": total_hospital // n,
        "buildings": total_building // n,
        "forest": total_forest // n,
        "network": total_network // n
    }

def group_zones(route, zones):

    grouped = []

    current_zone = zones[0]
    segment = [route[0]]

    route_data = []

    for i in range(1, len(route)):

        if zones[i] == current_zone:
            segment.append(route[i])
        else:
            grouped.append((current_zone, segment))
            current_zone = zones[i]
            segment = [route[i]]

    grouped.append((current_zone, segment))

    return grouped

def get_safe_route(start, end):

    route1, route2 = generate_routes(start, end)

    r1, z1 = route_risk(route1)
    r2, z2 = route_risk(route2)

    summary1 = summarize_route(route1)
    summary2 = summarize_route(route2)

    print("\n--- ROUTE COMPARISON ---")
    print("Route 1 Score:", r1)
    print("Route 2 Score:", r2)


    if r1 <= r2:
         print("\n✅ Route 1 is SAFER")

         print("\nFacilities in Route 1:")
         print("Hospitals:", summary1["hospitals"])
         print("Buildings:", summary1["buildings"])
         print("Forest:", summary1["forest"])
         print("Network:", "LOW" if summary1["network"] else "GOOD")

         return {
          "route": route1,
          "zones": z1,
          "score": r1
         }

    else:
       print("\n✅ Route 2 is SAFER")

       print("\nFacilities in Route 2:")
       print("Hospitals:", summary2["hospitals"])
       print("Buildings:", summary2["buildings"])
       print("Forest:", summary2["forest"])
       print("Network:", "LOW" if summary2["network"] else "GOOD")

       return {
          "route": route2,
          "zones": z2,
          "score": r2
         }

def get_zone_color(level):
    if level == 0:
        return "SAFE"
    elif level == 1:
        return "MODERATE"
    else:
        return "DANGEROUS"




def find_nearby(point, points, threshold=1):

    near = []

    for p in points:
        if haversine(point, np.array([p])) < threshold:
            near.append(p)

    return near

if __name__ == "__main__":

    lat1 = float(input("Start latitude: "))
    lng1 = float(input("Start longitude: "))

    lat2 = float(input("End latitude: "))
    lng2 = float(input("End longitude: "))

    result = get_safe_route([lat1, lng1], [lat2, lng2])

    route = result["route"]
    zones = result["zones"]
    score = result["score"]
    grouped_zones = group_zones(route, zones)

    print("\nSAFE ROUTE:\n")
    
    route_data = []
    for zone, segment in grouped_zones:

       print("\nZONE:", get_zone_color(zone))
       print("Points in this region:", len(segment))

       for point in segment:

          result = predict_risk(point[0], point[1])
          near_hospital = find_nearby(point, hospital_points)

          route_data.append({
              "lat": point[0],
              "lng": point[1],
              "zone": zone,
              "buildings": result["building"],
              "forest": result["forest"],
              "network": result["network"]
})

          print(
              point,
              "| Hospitals:", len(near_hospital),
              "| Buildings:", result["building"],
              "| Forest:", result["forest"],
              "| Network:", "LOW" if result["network"] else "GOOD"
        )


        
          if len(near_hospital) == 0:
            print(" ⚠ No hospitals nearby")
          if result["network"] == 1:
            print("⚠ Poor network coverage")
          if result["forest"] > 5:
            print("⚠ Dense forest area")

    print("\nDATA READY FOR FRONTEND")
    print("Total points:", len(route_data))
        

       


   


    