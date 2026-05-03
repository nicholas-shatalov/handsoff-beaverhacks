import os
import time
from pathlib import Path
import webview
import threading
import liveJarvis
import brain_service_one
import brain_service_two
import actions
import ai_client



class Api:
    def __init__(self):
        self.active = False

    def set_voice_mode(self):
        self.active = True
        print("Python: Voice Control Activated")

    def stop_voice_mode(self):
        self.active = False
        print("Python: Voice Control Deactivated")


def jarvis_loop(api):
    """The background logic loop"""
    while True:
        if api.active:
            liveJarvis.main()
            brain_service_one.start_brain_service()
            brain_service_two.start_brain_service()
            actions.execute_tasks()
        else:
            time.sleep(0.1)


if __name__ == "__main__":
    api = Api()

    # Start the Jarvis logic in a background thread
    threading.Thread(target=jarvis_loop, args=(api,), daemon=True).start()

    # Load your HTML file
    index_path = Path(__file__).resolve().parent / 'my_app' / 'index.html'
    window = webview.create_window('Ok Jarvis', index_path.as_uri(), js_api=api)
    webview.start()