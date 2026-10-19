
import csv

from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import KNeighborsClassifier


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
        features.append([
            float(row[column])
            for column in feature_columns
        ])
        labels.append(row["gesture_label"])


# 2. Recreate the same split
X_train, X_test, y_train, y_test = train_test_split(
    features,
    labels,
    test_size=0.2,
    random_state=42,
    stratify=labels
)


# 3. Train KNN with k=5
model = make_pipeline(
    StandardScaler(),
    KNeighborsClassifier(
        n_neighbors=5,
        weights="uniform"
    )
)

model.fit(X_train, y_train)
predictions = model.predict(X_test)


# 4. Print only the incorrect predictions
print("MISCLASSIFIED TEST EXAMPLES")
print("-" * 40)

for index, (actual, predicted) in enumerate(
    zip(y_test, predictions)
):
    if actual != predicted:
        print(f"\nTest example: {index}")
        print(f"Actual gesture: {actual}")
        print(f"Predicted gesture: {predicted}")
        print("Feature measurements:")

        for name, value in zip(
            feature_columns,
            X_test[index]
        ):
            print(f"  {name}: {value:.6f}")
