import pandas as pd
from sklearn.cluster import DBSCAN
import matplotlib.pyplot as plt

df = pd.read_csv("final_dataset.csv")

X = df[["lat", "lng"]]

model = DBSCAN(
    eps=0.01,
    min_samples=5
)

labels = model.fit_predict(X)

df["cluster"] = labels

print(df.head())

df.to_csv("clustered_dataset.csv", index=False)

print("Clusters created")


# plot

plt.scatter(
    df["lng"],
    df["lat"],
    c=df["cluster"],
    cmap="rainbow"
)

plt.show()