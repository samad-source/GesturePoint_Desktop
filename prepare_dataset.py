
import csv

# The three measurements KNN will use
feature_columns = [
    "thumb_index_distance",
    "wrist_index_distance",
    "wrist_middle_distance"
]

features = []
labels = []

# Open the dataset
with open(
    "gesturepoint_training_data.csv",
    mode="r",
    newline="",
    encoding="utf-8"
) as file:

    reader = csv.DictReader(file)

    for row in reader:

        # Convert measurements from text to numbers
        measurements = [
            float(row[column])
            for column in feature_columns
        ]

        # Store the measurements and their correct label
        features.append(measurements)
        labels.append(row["gesture_label"])

# Display the prepared dataset
print("Total examples:", len(features))
print("Number of features:", len(features[0]))

print("\nFirst feature example:")
print(features[0])

print("\nFirst example's correct label:")
print(labels[0])

print("\nFeature data type:")
print(type(features[0][0]))

print("\nFirst five labels:")
print(labels[:5])
