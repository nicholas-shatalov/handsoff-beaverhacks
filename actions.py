import json
import subprocess
import webbrowser
import pyautogui
import pygetwindow as gw
import time
import os
import screenshot
import pyperclip

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

def search_browser(searchterm: str):
    open_url("https://www.google.com/search?q=" + searchterm)

def click(x: int, y: int):
    pyautogui.click(x+90, y+90)

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
    pyautogui.typewrite(text, interval=0.1)

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

with open(TOOLS_JSON_FILE) as file:
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
    "type_text": type_text,
    "press_key": press_key,
    "take_screenshot": take_screenshot,
    "focus_window": focus_window,
    "search_on_youtube": search_on_youtube
}

def execute_action(tool_name, tool_input):
    function = actions.get(tool_name)

    # Check if function exists
    if function:
        print(f"Action: {tool_name} completed")
        # Unpack dictionary kwargs
        args = {k: v for k, v in tool_input.items() if k != "agent"}
        return function(**args)

def get_tasks():
    print("Loading tasks from json... checking for trigger")
    tasks = []
    if os.path.exists(TRIGGER_FILE) and os.path.exists(ACTION_FILE):
        try:
            print("Succesfully found trigger and action file")
            with open(ACTION_FILE) as f:
                for line in f:
                    time.sleep(0.3)
                    line = line.strip()
                    if not line:
                        continue
                    task = json.loads(line)
                    tasks.append(task)
        except Exception as e:
            print("Getting tasks failed")
        finally:
            os.remove(TRIGGER_FILE)
    return tasks
                
if __name__ == "__main__":
   get_tasks()