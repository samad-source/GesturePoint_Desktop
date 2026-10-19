
import time
import pyautogui

# Display screen dimensions
screen_width, screen_height = pyautogui.size()

print(f"Screen width: {screen_width}")
print(f"Screen height: {screen_height}")

print("\nMouse test starts in 3 seconds.")
print("Move your hand away from the mouse.")
print("Press Ctrl+C in the terminal to stop if needed.")

time.sleep(3)

# Move the real Windows cursor to the screen centre
centre_x = screen_width // 2
centre_y = screen_height // 2

pyautogui.moveTo(centre_x, centre_y, duration=1)

print("Mouse moved successfully!")
print("The test will finish in 2 seconds.")

time.sleep(2)
