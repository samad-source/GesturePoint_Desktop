
import cv2
import mediapipe as mp
import math

# Initialise MediaPipe hand tracking tools
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

# Open the webcam
camera = cv2.VideoCapture(0)

if not camera.isOpened():
    raise RuntimeError(
        "Could not open webcam. Check camera permissions."
    )

print("Webcam started.")
print("Show one hand to the camera.")
print("Press Q to quit.")

with mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.6,
    min_tracking_confidence=0.6
) as hands:

    while True:
        success, frame = camera.read()

        if not success:
            print("Could not read a webcam frame.")
            break

        # Mirror the image
        frame = cv2.flip(frame, 1)

        # Convert BGR to RGB for MediaPipe
        rgb_frame = cv2.cvtColor(
            frame, cv2.COLOR_BGR2RGB
        )

        # Detect the hand
        results = hands.process(rgb_frame)

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:

                # Draw the hand landmarks
                mp_drawing.draw_landmarks(
                    frame,
                    hand_landmarks,
                    mp_hands.HAND_CONNECTIONS
                )

                # Get wrist and index fingertip landmarks
                wrist = hand_landmarks.landmark[0]
                index_tip = hand_landmarks.landmark[8]

                # Calculate distance using normalized coordinates
                difference_x = index_tip.x - wrist.x
                difference_y = index_tip.y - wrist.y

                distance = math.sqrt(
                    difference_x ** 2 +
                    difference_y ** 2
                )

                # Display the distance
                cv2.putText(
                    frame,
                    f"Wrist-index distance: {distance:.4f}",
                    (10, 35),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.65,
                    (0, 255, 0),
                    2
                )

                # Highlight the index fingertip
                height, width, _ = frame.shape

                finger_x = int(index_tip.x * width)
                finger_y = int(index_tip.y * height)

                cv2.circle(
                    frame,
                    (finger_x, finger_y),
                    10,
                    (0, 255, 0),
                    cv2.FILLED
                )

        else:
            cv2.putText(
                frame,
                "No hand detected",
                (10, 35),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 0, 255),
                2
            )

        cv2.imshow(
            "GesturePoint - Hand Distance",
            frame
        )

        # Press Q to quit
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

camera.release()
cv2.destroyAllWindows()

print("Webcam closed.")
