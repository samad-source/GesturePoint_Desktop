
import csv

from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import accuracy_score


# 1. Load the dataset
feature_columns = [
    "thumb_index_distance",
    "wrist_index_distance",
    "wrist_middle_distance"
]

features = []
labels = []

with open(
    "gesturepoint_training_data.csv",
    mode="r",
    newline="",
    encoding="utf-8"
) as file:
    reader = csv.DictReader(file)

    for row in reader:
        measurements = [
            float(row[column])
            for column in feature_columns
        ]

        features.append(measurements)
        labels.append(row["gesture_label"])


# 2. Create the same training/testing split
X_train, X_test, y_train, y_test = train_test_split(
    features,
    labels,
    test_size=0.2,
    random_state=42,
    stratify=labels
)


# 3. Compare different values of k
k_values = [1, 3, 5, 7, 9]

print("KNN: COMPARING VALUES OF K")
print("-" * 35)

for k in k_values:
    model = make_pipeline(
        StandardScaler(),
        KNeighborsClassifier(
            n_neighbors=k,
            weights="uniform"
        )
    )

    model.fit(X_train, y_train)

    predictions = model.predict(X_test)

    accuracy = accuracy_score(y_test, predictions)

    print(f"k = {k}: Accuracy = {accuracy:.2%}")
