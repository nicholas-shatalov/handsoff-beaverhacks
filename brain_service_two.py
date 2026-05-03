import os
import base64
import json
import ai_client

IPC_FOLDER = "ipc_data_two"
TRIGGER_FILE = os.path.join(IPC_FOLDER, "trigger.txt")
TOOLS_FILE = os.path.join(IPC_FOLDER, "tools.json")
SCREENSHOT_FILE = os.path.join(IPC_FOLDER, "current_screen.jpg")
USER_GOAL_FILE = os.path.join(IPC_FOLDER, "user_goal.txt")
ACTION_FILE = os.path.join(IPC_FOLDER, "action.json")
ACTION_TRIGGER = os.path.join(IPC_FOLDER, "actiontrigger.txt")

def read_user_goal():
    with open(USER_GOAL_FILE, 'r') as f:
        for line in f:
            goal = line.strip()
        return goal

def encode_image(image_path):
    """Converts the screenshot into a format the AI can read."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def normalize_ai_response(ai_response):
    """Safely convert the model response into a JSON-able Python object."""
    if ai_response is None:
        return None

    if isinstance(ai_response, dict):
        return [ai_response]  # wrap in list for consistency
    
    if isinstance(ai_response, list):
        return ai_response  # already a list, return as is

    response_text = str(ai_response).strip()
    if response_text.lower() == "none":
        return None

    cleaned = response_text.replace("```json", "").replace("```", "").strip()
    if not cleaned:
        return None

    try:
        parsed = json.loads(cleaned)
        # handle both single action {} and multiple actions [{}]
        if isinstance(parsed, dict):
            return [parsed]
        if isinstance(parsed, list):
            return parsed
        return None
    except json.JSONDecodeError:
        return None


def start_brain_service():
    print("Brain Service 2 Starting... watching for triggers")
    
    # Check if Member 2 has dropped the trigger file AND the screenshot
    if os.path.exists(TRIGGER_FILE) and os.path.exists(SCREENSHOT_FILE) and os.path.exists(USER_GOAL_FILE):
        try:
            goal = read_user_goal()
            base64_img = encode_image(SCREENSHOT_FILE)

            ai_response = ai_client.ask_nemotron_two(user_goal=goal, text_input=None, image_input=base64_img)
            print(f"AI Response: {ai_response}")

            json_data_list = normalize_ai_response(ai_response)
            print(f"Final Output nemo2: {json_data_list}")
            
            if not json_data_list or not isinstance(json_data_list, list):
                error_payload = {
                    "name": "error", 
                    "arguments": {"reason": "explanation of why goal is not achievable"}
                }
                with open(ACTION_FILE, "w") as f:
                    json.dump(error_payload, f)
                print("Error: On response from nemo2")
                return
            
            # Save action file
            with open(ACTION_FILE, "w") as f:
                for json_packet in json_data_list:
                    json.dump(json_packet, f)
            print("Saved action.json for execution")
            
            with open(ACTION_TRIGGER, "w") as f:
                f.write("")
            print("Wrote trigger for action tasks")
                
        except Exception as e:
            print(f"Error processing data in nemo2: {e}")
        finally:
            # Delete the trigger file so we don't process it twice
            os.remove(TRIGGER_FILE)
                
                

if __name__ == "__main__":
    # If the ipc_data folder doesn't exist yet, create it safely
    if not os.path.exists(IPC_FOLDER):
        os.makedirs(IPC_FOLDER)
        
    start_brain_service()