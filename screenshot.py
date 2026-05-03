import pyautogui
import os
import base64
from PIL import Image
import io

# Define the folder and file name
folder_path = "ipc_data_one"
file_name = "current_screen.png"
full_path = os.path.join(folder_path, file_name)

scale_x = 0
scale_y = 0

# Take and save the screenshot
def take_screenshot():
    screenshot = pyautogui.screenshot(full_path)

    buffer = io.BytesIO()
    screenshot.save(buffer, format="PNG", quality=85)
    b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return b64

    
