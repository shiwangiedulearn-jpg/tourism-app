import pandas as pd
from sklearn.cluster import DBSCAN
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler


df = pd.read_csv("final_dataset.csv")

X = df[
    [
        "lat",
        "lng",
        "elevation",
        "slope",
        "forest_density",
        "dist_road"
    ]
]

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

model = DBSCAN(
    eps=0.8,
    min_samples=5
)

labels = model.fit_predict(X_scaled)

df["cluster"] = labels

print(df.head())

df.to_csv("clustered_dataset.csv", index=False)

print("Clusters created")




plt.scatter(
    df["lng"],
    df["lat"],
    c=df["cluster"],
    cmap="rainbow"
)

plt.show()