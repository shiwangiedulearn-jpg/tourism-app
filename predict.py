import joblib
import pandas as pd

model = joblib.load("risk_model.pkl")

lat = 31.32
lng = 75.57
type_val = 2
dist_water = 0.02
dist_hospital = 0.05
cluster = 1

data = pd.DataFrame(
    [[
        lat,
        lng,
        type_val,
        dist_water,
        dist_hospital,
        cluster
    ]],
    columns=[
        "lat",
        "lng",
        "type",
        "dist_water",
        "dist_hospital",
        "cluster",
    ]
)

pred = model.predict(data)

print("Location:", lat, lng)
print("Type:", type_val)
print("Distance from water:", dist_water)
print("Distance from hospital:", dist_hospital)
print("Cluster:", cluster)
print("Final Risk:", pred)