import cv2
import numpy as np
import time
import os

# ─────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────
NVIDIA_BROADCAST_CAMERA_INDEX = 0
FALLBACK_CAMERA_INDEX         = 0

BOX_SIZE = 200  
RIGHT_MARGIN = 30
TOP_MARGIN = 80  

HOLD_DELAY = 0.5
IPC_FILE = 'ipc_data_one/keyword.txt'

HSV_LOWER   = np.array([0, 20, 70], dtype=np.uint8)
HSV_UPPER   = np.array([25, 255, 255], dtype=np.uint8)
YCRCB_LOWER = np.array([0, 133, 77], dtype=np.uint8)
YCRCB_UPPER = np.array([255, 173, 127], dtype=np.uint8)

# ─────────────────────────────────────────────────────────────
# GESTURE ENGINE
# ─────────────────────────────────────────────────────────────

def classify_gesture(contour):
    area = cv2.contourArea(contour)
    hull = cv2.convexHull(contour)
    hull_area = cv2.contourArea(hull)
    solidity = area / hull_area if hull_area > 0 else 0

    # Get Bounding Box to check width vs height
    x, y, w, h = cv2.boundingRect(contour)
    aspect_ratio = float(w) / h

    # Calculate defects for Zoom gestures
    n_defects = 0
    hull_idx = cv2.convexHull(contour, returnPoints=False)
    if hull_idx is not None and len(hull_idx) > 3:
        try:
            defects = cv2.convexityDefects(contour, hull_idx)
            if defects is not None:
                for i in range(defects.shape[0]):
                    s, e, f, d = defects[i, 0]
                    start, end, far = contour[s][0], contour[e][0], contour[f][0]
                    a = np.linalg.norm(start - end)
                    b = np.linalg.norm(far - start)
                    c = np.linalg.norm(far - end)
                    angle = np.degrees(np.arccos(np.clip((b**2 + c**2 - a**2) / (2*b*c), -1, 1)))
                    if angle < 80 and (d/256.0) > 20:
                        n_defects += 1
        except: pass

    # 1. ZOOM GESTURES
    if n_defects >= 3: return "ZOOM_OUT"
    if solidity > 0.92: return "ZOOM_IN" # Very compact (Fist/Pinch)

    # 2. SCROLL GESTURES (Thumb Out vs Thumb In)
    # When thumb is out, the shape is wider (higher aspect ratio)
    # and has more "empty space" in the hull (lower solidity).
   
    if aspect_ratio > 0.65 or solidity < 0.78:
        return "SCROLL_UP"   # Thumb Out
    else:
        return "SCROLL_DOWN" # Thumb In

# ─────────────────────────────────────────────────────────────
# MAIN EXECUTION
# ─────────────────────────────────────────────────────────────

def main():
    if not os.path.exists('ipc_data_one'): os.makedirs('ipc_data_one')

    cap = cv2.VideoCapture(NVIDIA_BROADCAST_CAMERA_INDEX)
    if not cap.isOpened(): cap = cv2.VideoCapture(FALLBACK_CAMERA_INDEX)

    current_held_gesture = None
    gesture_start_time = 0
    cooldown_until = 0
    kernel = np.ones((5,5), np.uint8)

    while True:
        ret, frame = cap.read()
        if not ret: continue
        frame = cv2.flip(frame, 1)
        h, w = frame.shape[:2]

        x1 = w - BOX_SIZE - RIGHT_MARGIN
        y1 = TOP_MARGIN
        x2, y2 = x1 + BOX_SIZE, y1 + BOX_SIZE

        # UI Overlay
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
       
        roi = frame[y1:y2, x1:x2]
        blurred = cv2.GaussianBlur(roi, (7, 7), 0)
        mask = cv2.bitwise_or(
            cv2.inRange(cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV), HSV_LOWER, HSV_UPPER),
            cv2.inRange(cv2.cvtColor(blurred, cv2.COLOR_BGR2YCrCb), YCRCB_LOWER, YCRCB_UPPER)
        )
       
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        detected_gesture = "UNKNOWN"

        if contours:
            largest = max(contours, key=cv2.contourArea)
            if cv2.contourArea(largest) > 5000:
                epsilon = 0.01 * cv2.arcLength(largest, True)
                approx = cv2.approxPolyDP(largest, epsilon, True)
                detected_gesture = classify_gesture(approx)
               
                # Feedback
                cv2.drawContours(roi, [approx], -1, (255, 0, 0), 1)

        # ── HOLD & TRIGGER ──
        now = time.time()
        if detected_gesture != "UNKNOWN":
            if detected_gesture == current_held_gesture:
                time_held = now - gesture_start_time
                bw = int((time_held / HOLD_DELAY) * BOX_SIZE)
                cv2.rectangle(frame, (x1, y2 + 5), (x1 + min(bw, BOX_SIZE), y2 + 15), (0, 255, 0), -1)

                if time_held >= HOLD_DELAY and now > cooldown_until:
                    with open(IPC_FILE, 'w') as f:
                        f.write(detected_gesture)
                    cooldown_until = now + 1.0
                    gesture_start_time = now
            else:
                current_held_gesture = detected_gesture
                gesture_start_time = now
        else:
            current_held_gesture = None
            gesture_start_time = 0

        cv2.putText(frame, f"MODE: {current_held_gesture}", (x1, y1 - 15),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
       
        cv2.imshow("OmniAccess Perception", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'): break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
