import cv2
import mediapipe as mp
import time
import os
import math
import mss  # Fast screen capture

# --- INITIALIZATION ---
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=2, min_detection_confidence=0.7)
sct = mss.mss()  # Initialize screen capture

if not os.path.exists('ipc_data_one'):
    os.makedirs('ipc_data_one')

# --- CONFIGURATION ---
HOLD_TIME = 0.5        # How many seconds to hold the pose
COOLDOWN = 1.0         # Time to wait after a trigger
last_action_time = 0

# Pose tracking timers
pose_start_time = 0
current_pose = None

cap = cv2.VideoCapture(0)

print("OmniAccess 'Eyes' Active.")
print("Pointing Up = Swipe Up | Pointing Down = Swipe Down")
print("Pinch = Zoom In | Wide Open = Zoom Out")

while cap.isOpened():
    success, frame = cap.read()
    if not success: break

    frame = cv2.flip(frame, 1)
    h, w, c = frame.shape
    img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(img_rgb)

    now = time.time()
    detected_pose = None

    if results.multi_hand_landmarks:
        hand_lms = results.multi_hand_landmarks[0]
        
        # Landmarks
        thumb_tip = hand_lms.landmark[4]
        index_tip = hand_lms.landmark[8]
        index_mcp = hand_lms.landmark[5] 
        middle_tip = hand_lms.landmark[12]

        # 1. Logic for "Pointing Up"
        if index_tip.y < index_mcp.y - 0.1 and middle_tip.y > index_mcp.y:
            detected_pose = "SWIPE_UP"
            
        # 2. Logic for "Pointing Down"
        elif index_tip.y > index_mcp.y + 0.1:
            detected_pose = "SWIPE_DOWN"
            
        # 3. Logic for "Pinch"
        else:
            dist = math.sqrt((thumb_tip.x - index_tip.x)**2 + (thumb_tip.y - index_tip.y)**2)
            if dist < 0.05:
                detected_pose = "ZOOM_IN"
            
            # 4. Logic for "Wide Open"
            elif dist > 0.2:
                detected_pose = "ZOOM_OUT"

    # --- THE TIMER & SENDING LOGIC ---
    if detected_pose and detected_pose == current_pose:
        time_held = now - pose_start_time
        
        cv2.putText(frame, f"HOLDING: {detected_pose} ({time_held:.1f}s)", (50, 50), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        if time_held >= HOLD_TIME and (now - last_action_time > COOLDOWN):
            print(f"TRAPPED: {detected_pose}. Capturing screen...")

            # STEP 1: Capture the screen FIRST
            # Using .png to match your brain.py expectations
            #screenshot_path = 'ipc_data/current_screen.png'
            # sct.shot(output=screenshot_path)

            # STEP 2: Create the trigger file AFTER the image is saved
            # This ensures the Brain doesn't wake up to an empty image
            with open('ipc_data_one/trigger.txt', 'w') as f:
                f.write(detected_pose)
            
            print(f"Sent {detected_pose} to Brain.")
            
            last_action_time = now
            pose_start_time = now 
    else:
        current_pose = detected_pose
        pose_start_time = now

    cv2.imshow("OmniAccess Perception", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'): break

cap.release()
cv2.destroyAllWindows()