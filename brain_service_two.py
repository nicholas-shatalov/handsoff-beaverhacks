import os
import time
import base64
import json
from openai import OpenAI
from dotenv import load_dotenv

# 1. Load the hidden .env file securely
load_dotenv()

# 2. Initialize the NVIDIA NIM client
client = OpenAI(
  base_url="https://integrate.api.nvidia.com/v1",
  api_key=os.getenv("NVIDIA_API_KEY") 
)

# 3. Define the IPC Inter-Process Communication paths
IPC_FOLDER = "ipc_data_2"
TRIGGER_FILE = os.path.join(IPC_FOLDER, "trigger.txt")
IMAGE_FILE = os.path.join(IPC_FOLDER, "current_screen.png")
ACTION_FILE = os.path.join(IPC_FOLDER, "action.json")

# 4. The Master Prompt (Forces strict JSON output)
SYSTEM_PROMPT = """
You are OmniAccess, an autonomous accessibility agent. 
You will be provided with a screenshot of a user's computer screen and a user goal.
Before calculating coordinates, identify key UI landmarks such as headers, navbars, dialogs, forms, or buttons that help locate the target element.
Then locate the UI element required to achieve the goal and output its coordinates as percentages relative to the screen size.

CRITICAL INSTRUCTIONS:
1. You must output ONLY valid JSON.
2. No markdown formatting, no backticks, no conversational text.
3. If the target element is NOT visible on the screen, set the action to "error".
4. Use the following schema:
{
  "action": "click" | "type" | "error",
  "x": float (0.0-100.0, 0 if error),
  "y": float (0.0-100.0, 0 if error),
  "text": "string (Type text here, OR put the error reason here)"
}
"""

# Let's test it on a button actually on your screen!
USER_GOAL = "Find the 'Google Search' box in the middle of the screen and click it."

def encode_image(image_path):
    """Converts the screenshot into a format the AI can read."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def ask_nemotron(base64_image):
    """Sends the image and prompt to the Nemotron Omni model."""
    print("🧠 Thinking...")
    
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

    # Print the model's internal reasoning to the terminal (Great for demo!)
    reasoning = None
    if completion.choices and len(completion.choices) > 0:
        reasoning = getattr(completion.choices[0].message, "reasoning_content", None)
    if reasoning:
        print(f"\n🤔 Internal Logic:\n{reasoning}\n")

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
    """The infinite loop that watches the folder for new screenshots."""
    print("🧠 Brain Service Started. Watching for triggers in the ipc_data/ folder...")
    
    while True:
        # Check if Member 2 has dropped the trigger file AND the screenshot
        if os.path.exists(TRIGGER_FILE) and os.path.exists(IMAGE_FILE):
            try:
                base64_img = encode_image(IMAGE_FILE)
                ai_response = ask_nemotron(base64_img)
                
                json_data = normalize_ai_response(ai_response)
                if not json_data or not isinstance(json_data, dict):
                    error_payload = {
                        "action": "error",
                        "x": 0,
                        "y": 0,
                        "text": "AI returned no valid response or could not find the target element."
                    }
                    with open(ACTION_FILE, "w") as f:
                        json.dump(error_payload, f)
                    print("❌ Error: Invalid or missing AI response; saved fallback error action.")
                    continue

                print(f"✅ Final Decision: {json.dumps(json_data)}")
                
                # Save it for Member 4
                with open(ACTION_FILE, "w") as f:
                    json.dump(json_data, f)
                print(f"💾 Saved action.json for execution.")
                    
            except Exception as e:
                print(f"❌ Error processing frame: {e}")
            finally:
                # Delete the trigger file so we don't process it twice
                os.remove(TRIGGER_FILE)
                
        # Pause briefly to prevent maxing out the CPU
        time.sleep(0.2)

if __name__ == "__main__":
    # If the ipc_data folder doesn't exist yet, create it safely
    if not os.path.exists(IPC_FOLDER):
        os.makedirs(IPC_FOLDER)
        
    start_brain_service()