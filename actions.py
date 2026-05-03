import json
import subprocess
import webbrowser
import pyautogui
import pygetwindow as gw
import time
import os

IPC_FOLDER = "ipc_data_two"
TOOLS_JSON_FILE = os.path.join(IPC_FOLDER, "tools.json")
TRIGGER_FILE = os.path.join(IPC_FOLDER, "actiontrigger.txt")
ACTION_FILE = os.path.join(IPC_FOLDER, "action.json")

def open_application(app_name: str):
    try:
        subprocess.Popen(app_name)
        time.sleep(1)
        return True
    except Exception as e:
        print(f"Failed to open {app_name}: {e}")
        return False

def open_url(url: str):
    try:
        webbrowser.open(url)
        time.sleep(1)
        return True
    except Exception as e:
        print(f"Failed to open browser and go to {url}: {e}")
        return False

def open_youtube():
    open_url("https://www.youtube.com")

def click(x: int, y: int):
    pyautogui.click(x, y)

def scroll(direction: str, amount: int = 3):
    try:
        if direction == "up":
            pyautogui.scroll(amount)    # positive = up
        elif direction == "down":
            pyautogui.scroll(-amount)   # negative = down
        return True
    except Exception as e:
        print(f"Failed to scroll: {e}")
        return False
    
def zoom(direction: str, amount: int = 3):
    try:
        pyautogui.keyDown("ctrl")
        if direction == "in":
            pyautogui.scroll(amount)
        elif direction == "out":
            pyautogui.scroll(-amount)
        pyautogui.keyUp("ctrl")
        return True
    except Exception as e:
        print(f"Failed to zoom: {e}")
        return False

def type_text(text: str):
    pyautogui.typewrite(text, interval=0.05)

def press_key(key: str):
    pyautogui.press(key)

def take_screenshot(path: str = "screenshot.png"):
    pyautogui.screenshot(path)
    return path

def focus_window(title_substring: str):
    # Bring a window with the given title to focus
    windows = gw.getWindowsWithTitle(title_substring)
    if windows:
        windows[0].activate()
        return True
    return False

def search_on_youtube(query: str):
    url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
    open_url(url)

with open("tools.json") as file:
    # make a nested list dict based off json
    tools = json.load(file)

# maps names of functions to the action function
actions = {
    "open_application": open_application,
    "open_url": open_url,
    "open_youtube": open_youtube,
    "click": click,
    "scroll": scroll,
    "zoom": zoom,
    "type_test": type_text,
    "press_key": press_key,
    "take_screenshot": take_screenshot,
    "focus_window": focus_window,
    "search_on_youtube": search_on_youtube
}

def execute_action(tool_name, tool_input):
    function = actions.get(tool_name)
    # Check if function exists
    if function:
        # Unpack dictionary kwargs
        return function(**tool_input)
    
def execute_tasks():
    print("Executing tasks started... checking for trigger")
    if os.path.exists(TRIGGER_FILE) and os.path.exists(ACTION_FILE):
        try:
            with open(ACTION_FILE) as f:
                actions = json.load(f)
            for action in actions:
                execute_action(action["name"], action["argument"])
                print(f"Action: {action["name"]} completed")
        except Exception as e:
            print("Actions failed")
        finally:
            os.remove(TRIGGER_FILE)
                
