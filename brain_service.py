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
IPC_FOLDER = "ipc_data"
TRIGGER_FILE = os.path.join(IPC_FOLDER, "trigger.txt")
IMAGE_FILE = os.path.join(IPC_FOLDER, "current_screen.png")
ACTION_FILE = os.path.join(IPC_FOLDER, "action.json")

# 4. The Master Prompt (Forces strict JSON output)
SYSTEM_PROMPT = """
You are OmniAccess, an autonomous accessibility agent. 
You will be provided with a screenshot of a user's computer screen and a user goal.
Your task is to locate the UI element required to achieve the goal and output its EXACT pixel coordinates.

CRITICAL INSTRUCTIONS:
1. You must output ONLY valid JSON.
2. No markdown formatting, no backticks, no conversational text.
3. If the target element is NOT visible on the screen, set the action to "error".
4. Use the following schema:
{
  "action": "click" | "type" | "error",
  "x": int (0 if error),
  "y": int (0 if error),
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
    reasoning = getattr(completion.choices[0].message, "reasoning_content", None)
    if reasoning:
        print(f"\n🤔 Internal Logic:\n{reasoning}\n")
        
    return completion.choices[0].message.content

def start_brain_service():
    """The infinite loop that watches the folder for new screenshots."""
    print("🧠 Brain Service Started. Watching for triggers in the ipc_data/ folder...")
    
    while True:
        # Check if Member 2 has dropped the trigger file AND the screenshot
        if os.path.exists(TRIGGER_FILE) and os.path.exists(IMAGE_FILE):
            try:
                base64_img = encode_image(IMAGE_FILE)
                ai_response = ask_nemotron(base64_img)
                
                # NEW SAFETY CHECK: If the AI returns None, skip processing
                if not ai_response:
                    print("❌ Error: Nemotron returned an empty response.")
                    continue 

                print(f"✅ Final Decision: {ai_response}")
                
                # Strip any accidental markdown the AI might add
                clean_json_string = ai_response.replace("```json", "").replace("```", "").strip()
                
                # Parse it into a real Python dictionary
                json_data = json.loads(clean_json_string)
                
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