import os
import time
import base64
import json
import ai_client

# 3. Define the IPC Inter-Process Communication paths
IPC_FOLDER = "ipc_data_one"
IPC_FOLDER_TWO = "ipc_data_two"
TRIGGER_FILE_ONE = os.path.join(IPC_FOLDER, "trigger1.txt")
TRIGGER_FILE_TWO = os.path.join(IPC_FOLDER, "trigger2.txt")
TRANSCRIPT_FILE = os.path.join(IPC_FOLDER, "transcript.txt")
KEYWORD_FILE = os.path.join(IPC_FOLDER, "keyword.txt")
USER_GOAL_FILE = os.path.join(IPC_FOLDER_TWO, "user_goal.txt")
OUTPUT_TRIGGER = os.path.join(IPC_FOLDER_TWO, "trigger.txt")


def read_file(path):
    with open(path, 'r') as f:
        for line in f:
            return line.strip()


def normalize_ai_response(ai_response):
    """Safely convert the model response into a cleaned string."""
    if ai_response is None:
        return None

    if isinstance(ai_response, (list, dict)):
        return json.dumps(ai_response)

    response_text = str(ai_response).strip()
    if response_text.lower() == "none":
        return None

    cleaned = response_text.replace("```json", "").replace("```", "").strip()
    if not cleaned:
        return None

    return cleaned


def create_trigger_for_two():
    """Create a trigger file in ipc_data_two to signal brain_service_two that processing is complete."""
    trigger_path = os.path.join("ipc_data_two", "trigger.txt")
    with open(trigger_path, "w") as f:
        f.write("done")
    print("Created trigger for brain_service_two")


def start_brain_service():
    print("Brain Service 1 Starting... watching for triggers")
    
    if (os.path.exists(TRIGGER_FILE_ONE) and os.path.exists(TRANSCRIPT_FILE)) or \
        (os.path.exists(TRIGGER_FILE_TWO) and os.path.exists(KEYWORD_FILE)):
        try:
            input = ''
            if os.path.exists(TRANSCRIPT_FILE):
                input = read_file(TRANSCRIPT_FILE)
            elif os.path.exists(KEYWORD_FILE):
                input = read_file(KEYWORD_FILE)
            else:
                raise Exception
            
            ai_response = ai_client.ask_nemotron_one(user_goal=None, text_input=input, image_input=None)
            print(f"AI Response: {ai_response}")
            output = normalize_ai_response(ai_response)
            if not output or not isinstance(output, str):
                error_payload = "error"
                with open(USER_GOAL_FILE, "w") as f:
                    f.write(error_payload)
                print("Error: On response from nemo1")
                return

            print(f"Final Output Nemo1: {output}")
            

            with open(USER_GOAL_FILE, "w") as f:
                f.write(output)
            print(f"Saved user_goal.txt")

            create_trigger_for_two()
                
        except Exception as e:
            print(f"Error processing data in nemo1: {e}")
        finally:
            # Delete the trigger file so we don't process it twice
            if os.path.exists(TRIGGER_FILE_ONE):
                os.remove(TRIGGER_FILE_ONE)
            if os.path.exists(TRIGGER_FILE_TWO):
                os.remove(TRIGGER_FILE_TWO)
                


if __name__ == "__main__":
    # If the ipc_data folder doesn't exist yet, create it safely
    if not os.path.exists(IPC_FOLDER):
        os.makedirs(IPC_FOLDER)
        
    start_brain_service()