import pyautogui
import os

# Define the folder and file name
folder_path = "ipc_data_one"
file_name = "current_screen.jpg"
full_path = os.path.join(folder_path, file_name)

# Take and save the screenshot
def take_screenshot():
    pyautogui.screenshot(full_path)