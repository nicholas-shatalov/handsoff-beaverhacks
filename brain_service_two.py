import os
import time
import base64
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
  base_url="https://integrate.api.nvidia.com/v1",
  api_key=os.getenv("NVIDIA_API_KEY") 
)

IPC_FOLDER = "ipc_data_two"
TRIGGER_FILE = os.path.join(IPC_FOLDER, "trigger.txt")
TOOLS_FILE = os.path.join(IPC_FOLDER, "tools.json")
SCREENSHOT_FILE = os.path.join(IPC_FOLDER, "current_screen.jpg")
USER_GOAL_FILE = os.path.join(IPC_FOLDER, "user_goal.txt")
ACTION_FILE = os.path.join(IPC_FOLDER, "action.json")
ACTION_TRIGGER = os.path.join(IPC_FOLDER, "actiontrigger.txt")

def build_tools_prompt(tools_path: str) -> str:
    with open(tools_path) as f:
        tools = json.load(f)

    prompt = "You have access to the following actions you can perform on the computer:\n\n"

    for tool in tools:
        fn = tool["function"]
        name = fn["name"]
        description = fn["description"]
        parameters = fn["parameters"]["properties"]
        required = fn["parameters"].get("required", [])

        prompt += f"Action: {name}\n"
        prompt += f"Description: {description}\n"

        if parameters:
            prompt += "Arguments:\n"
            for param_name, param_info in parameters.items():
                req_label = "(required)" if param_name in required else "(optional)"
                prompt += f"  - {param_name} {req_label}: {param_info.get('description', '')} [type: {param_info.get('type', 'string')}]\n"
        else:
            prompt += "Arguments: none\n"

        prompt += "\n"

    return prompt

JSON_PROMPT = build_tools_prompt(TOOLS_FILE)
USER_GOAL = ""

SYSTEM_PROMPT = """
You are HandsOff, an autonomous accessibility agent that is supposed to enact computer actions on behalf of the user. 
You will be provided with a user goal and a screenshot of the current screen.
Before doing any actions, read and understand the user goal. 
Then look at the user screenshot and identify key UI landmarks such as headers, navbars, dialogs, forms, or buttons that help locate target elements.
""" + JSON_PROMPT + """
Then think about the set of actions needed to achieve the user goal and and output them in the exact order they should be executed.
CRITICAL INSTRUCTIONS:
1. You must output ONLY valid JSON.
2. No markdown formatting, no backticks, no conversational text.
3. If the user goal is NOT achievable, set the action to "error".
4. Use the following schema:
[
    {"name": "open_url", "arguments": {"url": "https://youtube.com"}},
    {"name": "type_text", "arguments": {"text": "cat videos"}},
    {"name": "error", "arguments": {"reason": "explanation of why goal is not achievable"}}
]
"""

def read_user_goal():
    with open(USER_GOAL_FILE, 'r') as f:
        for line in f:
            goal = line.strip()
        return goal

def encode_image(image_path):
    """Converts the screenshot into a format the AI can read."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def ask_nemotron(base64_image):
    print("Nemotron Two Thinking")
    
    completion = client.chat.completions.create(
      model="nvidia/nemotron-3-nano-omni-30b-a3b-reasoning",
      messages=[
          {
              "role": "system", 
              "content": SYSTEM_PROMPT
          },
          {
              "role": "user",
              "content": [
                  {"type": "text", "text": f"User Goal: {USER_GOAL}"},
                  {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}}
              ]
          }
      ],
      temperature=0.1, 
      top_p=0.95,
      max_tokens=1024, 
      extra_body={"chat_template_kwargs":{"enable_thinking":True},"reasoning_budget":1024},
      stream=False
    )

    # Print the model's internal reasoning to the terminal 
    reasoning = None
    if completion.choices and len(completion.choices) > 0:
        reasoning = getattr(completion.choices[0].message, "reasoning_content", None)
    if reasoning:
        print(f"\nInternal Logic:\n{reasoning}\n")

    if not completion.choices or len(completion.choices) == 0:
        return None

    return completion.choices[0].message.content


def normalize_ai_response(ai_response):
    """Safely convert the model response into a JSON-able Python object."""
    if ai_response is None:
        return None

    if isinstance(ai_response, dict):
        return ai_response

    response_text = str(ai_response).strip()
    if response_text.lower() == "none":
        return None

    cleaned = response_text.replace("```json", "").replace("```", "").strip()
    if not cleaned:
        return None

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return None


def start_brain_service():
    print("Brain Service Two Started. Watching for triggers in the ipc_data_two/ folder...")
    
    # Check if Member 2 has dropped the trigger file AND the screenshot
    if os.path.exists(TRIGGER_FILE) and os.path.exists(SCREENSHOT_FILE) and os.path.exists(USER_GOAL_FILE):
        try:
            USER_GOAL = read_user_goal()
            base64_img = encode_image(SCREENSHOT_FILE)
            ai_response = ask_nemotron(base64_img)
            
            json_data = normalize_ai_response(ai_response)
            # If error occurs, save error data in action file
            if not json_data or not isinstance(json_data, dict):
                error_payload = {
                    "name": "error", 
                    "arguments": {"reason": "explanation of why goal is not achievable"}
                }
                with open(ACTION_FILE, "w") as f:
                    json.dump(error_payload, f)
                print("Error: Invalid or missing AI response; saved fallback error action")
                return

            print(f"Final Decision: {json.dumps(json_data)}")
            
            # Save action file
            with open(ACTION_FILE, "w") as f:
                json.dump(json_data, f)
            print("Saved action.json for execution")
            
            with open(ACTION_TRIGGER, 'w') as f:
                f.write("")
            print("Wrote trigger for action tasks")
                
        except Exception as e:
            print(f"Error processing data: {e}")
        finally:
            # Delete the trigger file so we don't process it twice
            os.remove(TRIGGER_FILE)
                
                

if __name__ == "__main__":
    # If the ipc_data folder doesn't exist yet, create it safely
    if not os.path.exists(IPC_FOLDER):
        os.makedirs(IPC_FOLDER)
        
    start_brain_service()