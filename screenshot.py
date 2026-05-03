import pyautogui
import os
import base64
from PIL import Image
import io

# Define the folder and file name
folder_path = "ipc_data_one"
file_name = "current_screen.jpg"
full_path = os.path.join(folder_path, file_name)

scale_x = 0
scale_y = 0

# Take and save the screenshot
def take_screenshot(resize_width=800):
    screenshot = pyautogui.screenshot(full_path)
    screen_w, screen_h = screenshot.size

    aspect = screen_h / screen_w
    resize_height = int(resize_width * aspect)
    resized = screenshot.resize((resize_width, resize_height), Image.LANCZOS)

    scale_x = screen_w / resize_width
    scale_y = screen_h / resize_height

    buffer = io.BytesIO()
    resized.save(buffer, format="JPEG", quality=85)
    b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return b64

def get_scale_x(resize_width=800):
    screenshot = pyautogui.screenshot(full_path)
    screen_w, screen_h = screenshot.size

    return screen_w / resize_width
    

def get_scale_y(resize_width=800):
    screenshot = pyautogui.screenshot(full_path)
    screen_w, screen_h = screenshot.size

    aspect = screen_h / screen_w
    resize_height = int(resize_width * aspect)

    return screen_h / resize_height

    
