
import csv

from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
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


# 3. Set up five-fold cross-validation
cv = StratifiedKFold(
    n_splits=5,
    shuffle=True,
    random_state=42
)


# 4. Compare k values using training data only
print("FIVE-FOLD CROSS-VALIDATION")
print("-" * 40)

for k in [1, 3, 5, 7, 9]:
    model = make_pipeline(
        StandardScaler(),
        KNeighborsClassifier(
            n_neighbors=k,
            weights="uniform"
        )
    )

    scores = cross_val_score(
        model,
        X_train,
        y_train,
        cv=cv,
        scoring="accuracy"
    )

    print(f"\nk = {k}")
    print("Fold scores:", [round(score, 3) for score in scores])
    print(f"Mean accuracy: {scores.mean():.2%}")
