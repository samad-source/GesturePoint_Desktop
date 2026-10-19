
import csv

# Open the training dataset
with open(
    "gesturepoint_training_data.csv",
    mode="r",
    newline="",
    encoding="utf-8"
) as file:

    reader = csv.DictReader(file)

    # Display the column names
    print("DATASET COLUMNS:")
    print(reader.fieldnames)

    # Read all rows
    rows = list(reader)

    # Display the total number of examples
    print("\nTOTAL EXAMPLES:")
    print(len(rows))

    # Display the first five examples
    print("\nFIRST FIVE EXAMPLES:")

    for row in rows[:5]:
        print(row)

    # Count the examples belonging to each gesture
    gesture_counts = {}

    for row in rows:
        gesture = row["gesture_label"]

        if gesture not in gesture_counts:
            gesture_counts[gesture] = 0

        gesture_counts[gesture] += 1

    print("\nEXAMPLES PER GESTURE:")

    for gesture, count in gesture_counts.items():
        print(f"{gesture}: {count}")
