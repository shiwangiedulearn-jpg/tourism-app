import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
import joblib

df = pd.read_csv("clustered_dataset.csv")

print(df.head())

# features
X = df[
    [
        "lat",
        "lng",
        "type",
        "dist_water",
        "dist_hospital",
        "cluster",
    ]
]

# label
y = df["risk"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2
)

model = RandomForestClassifier()

model.fit(X_train, y_train)

print("Accuracy:", model.score(X_test, y_test))

joblib.dump(model, "risk_model.pkl")

print("Model saved")