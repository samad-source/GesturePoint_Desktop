import math

# Example wrist coordinates
wrist_x = 100
wrist_y = 200

# Example index fingertip coordinates
index_x = 160
index_y = 100

# Calculate the differences between the coordinates
difference_x = index_x - wrist_x
difference_y = index_y - wrist_y

# Calculate the straight-line distance
distance = math.sqrt(
    difference_x**2 + difference_y**2
)

print("Wrist:", (wrist_x, wrist_y))
print("Index fingertip:", (index_x, index_y))
print("Horizontal difference:", difference_x)
print("Vertical difference:", difference_y)
print("Wrist-to-index distance:", round(distance, 2))