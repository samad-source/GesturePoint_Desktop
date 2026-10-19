from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay
import matplotlib.pyplot as plt
import csv
import numpy as np

# Store the names of the numerical features
feature_columns = [
    "thumb_index_distance",
    "wrist_index_distance",
    "wrist_middle_distance"
]

# Empty lists to store the features and correct labels
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

    # Read each row in the dataset
    for row in reader:

        # Extract the three numerical measurements
        measurements = [
            float(row[column])
            for column in feature_columns
        ]

        # Save the measurements and their correct gesture
        features.append(measurements)
        labels.append(row["gesture_label"])

print("Total examples:", len(features))
print("Total labels:", len(labels))
print("First example:", features[0])
print("First label:", labels[0])

# Split the dataset into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(
    features,
    labels,
    test_size=0.2,
    random_state=42,
    stratify=labels
)

print("\nTraining examples:", len(X_train))
print("Testing examples:", len(X_test))

print("\nTraining labels:", len(y_train))
print("Testing labels:", len(y_test))

# Create a KNN model with feature scaling
model = make_pipeline(
    StandardScaler(),
    KNeighborsClassifier(n_neighbors=5)
)

# Train the model using the training data
model.fit(X_train, y_train)

print("\nKNN model trained successfully!")
print("Number of training examples:", len(X_train))
print("Number of neighbors (k):", 5)

# Use the trained model to predict the testing examples
y_pred = model.predict(X_test)

# Display the actual and predicted labels
print("\nACTUAL LABELS:")
print(y_test)

print("\nPREDICTED LABELS:")
print(y_pred)

# Calculate the model's accuracy
accuracy = accuracy_score(y_test, y_pred)

print("\nMODEL ACCURACY:")
print(f"{accuracy:.2%}")

# Create a confusion matrix
gesture_names = ["fist", "open_palm", "pinch"]

matrix = confusion_matrix(
    y_test,
    y_pred,
    labels=gesture_names
)

print("\nCONFUSION MATRIX:")
print(matrix)

# Display the confusion matrix as a chart
display = ConfusionMatrixDisplay(
    confusion_matrix=matrix,
    display_labels=gesture_names
)

display.plot()
plt.title("GesturePoint KNN - Confusion Matrix")
plt.tight_layout()
plt.show()

# Find the examples the model classified incorrectly
print("\nMISCLASSIFIED EXAMPLES:")

for index in range(len(y_test)):
    actual = y_test[index]
    predicted = y_pred[index]

    if actual != predicted:
        print(
            f"Test example {index + 1}: "
            f"Actual = {actual}, "
            f"Predicted = {predicted}, "
            f"Features = {X_test[index]}"
        )
        

print("\nNEAREST-NEIGHBOR INVESTIGATION:")

# Get the fitted scaler and KNN classifier from the pipeline
scaler = model.named_steps["standardscaler"]
knn = model.named_steps["kneighborsclassifier"]

# Transform the testing features using the fitted scaler
X_test_scaled = scaler.transform(X_test)

for index in range(len(y_test)):
    if y_test[index] != y_pred[index]:
        distances, neighbor_indices = knn.kneighbors(
            X_test_scaled[index].reshape(1, -1)
        )

        print(
            f"\nTest example {index + 1}: "
            f"Actual = {y_test[index]}, "
            f"Predicted = {y_pred[index]}"
        )

        print("Nearest training neighbors:")

        for rank, (distance, neighbor_index) in enumerate(
            zip(distances[0], neighbor_indices[0]),
            start=1
        ):
            print(
                f"{rank}. Gesture = {y_train[neighbor_index]}, "
                f"Distance = {distance:.4f}"
            )