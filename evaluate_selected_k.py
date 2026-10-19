
import csv

from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report


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


# 2. Recreate the same training and test split
X_train, X_test, y_train, y_test = train_test_split(
    features,
    labels,
    test_size=0.2,
    random_state=42,
    stratify=labels
)


# 3. Train the selected KNN model
model = make_pipeline(
    StandardScaler(),
    KNeighborsClassifier(
        n_neighbors=5,
        weights="uniform"
    )
)

model.fit(X_train, y_train)


# 4. Make predictions on the held-out test data
y_pred = model.predict(X_test)


# 5. Evaluate the model
print("FINAL HELD-OUT TEST EVALUATION")
print("-" * 40)

print(
    f"Test accuracy: "
    f"{accuracy_score(y_test, y_pred):.2%}"
)

print("\nConfusion matrix:")
print(confusion_matrix(
    y_test,
    y_pred,
    labels=["fist", "open_palm", "pinch"]
))

print("\nClassification report:")
print(classification_report(
    y_test,
    y_pred,
    labels=["fist", "open_palm", "pinch"],
    zero_division=0
))
