import joblib
import pandas as pd
import numpy as np

model = joblib.load("risk_model.pkl")
start = [31.32, 75.57]
end = [31.35, 75.60]
def generate_route(start, end, steps=20):

    lat1, lng1 = start
    lat2, lng2 = end

    route = []

    for i in range(steps):

        lat = lat1 + (lat2 - lat1) * i / steps
        lng = lng1 + (lng2 - lng1) * i / steps

        route.append([lat, lng])

    return route


route = generate_route(start, end)
def predict_risk(lat, lng):

    type_val = 2
    dist_water = np.random.rand() * 0.05
    dist_hospital = np.random.rand() * 0.05
    cluster = np.random.randint(-1, 3)

    data = pd.DataFrame(
        [[lat, lng, type_val, dist_water, dist_hospital, cluster]],
        columns=[
            "lat",
            "lng",
            "type",
            "dist_water",
            "dist_hospital",
            "cluster",
        ]
    )

    pred = model.predict(data)[0]

    return pred

total_risk = 0

for p in route:

    lat, lng = p

    r = predict_risk(lat, lng)

    total_risk += r

print("Total route risk:", total_risk)
end2 = [31.36, 75.65]

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

if r1 < r2:
    print("Route1 is safer")
elif r2 < r1:
    print("Route2 is safer")
else:
    print("Both routes have same risk")