
import csv

from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import accuracy_score, confusion_matrix


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


# 2. Split the data
X_train, X_test, y_train, y_test = train_test_split(
    features,
    labels,
    test_size=0.2,
    random_state=42,
    stratify=labels
)


# 3. Compare uniform and distance-weighted voting
voting_methods = ["uniform", "distance"]

for method in voting_methods:
    model = make_pipeline(
        StandardScaler(),
        KNeighborsClassifier(
            n_neighbors=5,
            weights=method
        )
    )

    model.fit(X_train, y_train)

    predictions = model.predict(X_test)

    accuracy = accuracy_score(y_test, predictions)

    print(f"\nVoting method: {method}")
    print(f"Accuracy: {accuracy:.2%}")

    print("Confusion matrix:")
    print(
        confusion_matrix(
            y_test,
            predictions,
            labels=["fist", "open_palm", "pinch"]
        )
    )
