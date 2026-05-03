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
IPC_FOLDER = "ipc_data_one"
IPC_FOLDER_TWO = "ipc_data_two"
TRIGGER_FILE_ONE = os.path.join(IPC_FOLDER, "trigger1.txt")
TRIGGER_FILE_TWO = os.path.join(IPC_FOLDER, "trigger2.txt")
TRANSCRIPT_FILE = os.path.join(IPC_FOLDER, "transcript.txt")
KEYWORD_FILE = os.path.join(IPC_FOLDER, "keyword.txt")
USER_GOAL_FILE = os.path.join(IPC_FOLDER_TWO, "user_goal.txt")
USER_DATA = ""

# 4. The Master Prompt (Forces strict JSON output)
SYSTEM_PROMPT = """
You are the Interpreter (Agent 1) for an AI agent system called HandsOff, an autonomous accessibility agent. Your job is to translate raw, messy user inputs (audio transcripts or physical gesture descriptions) into a single, clear computer command.
Physical gesture descriptions will come with one word. Audio transcripts will come into the form of a long text.
RULES:

You must condense the input into exactly one short sentence.

You must NOT include any conversational filler (e.g., do not say 'Here is the goal' or 'The user wants to').

You must format your output strictly starting with this exact phrase: 'Action requested: [insert specific action here]
"""


def read_file(path):
    with open(path, 'r') as f:
        for line in f:
            return line.strip()


def ask_nemotron(text_input):
    print("Nemotron One Thinking...")
    
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
                  {"type": "text", "text": f"User Goal: {USER_DATA}"},
                  {"type": "text", "text": f"Data: {text_input}"}
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
        print(f"\nInternal Logic:\n{reasoning}\n")

    if not completion.choices or len(completion.choices) == 0:
        return None

    return completion.choices[0].message.content


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


def start_brain_service():
    print("Brain Service Started. Watching for triggers in the ipc_data_one/ folder...")
    
    while True:
        # Check if Member 2 has dropped the trigger file AND the screenshot
        if (os.path.exists(TRIGGER_FILE_ONE) and os.path.exists(TRANSCRIPT_FILE)) or \
           (os.path.exists(TRIGGER_FILE_TWO) and os.path.exists(KEYWORD_FILE)):
            try:
                input = ''
                if os.path.exists(TRANSCRIPT_FILE):
                    USER_DATA = "Here is a transcript of the user requests for action"
                    input = read_file(TRANSCRIPT_FILE)
                elif os.path.exists(KEYWORD_FILE):
                    USER_DATA = "Here is the keyword that was obtained from the physical gesture"
                    input = read_file(KEYWORD_FILE)
                else:
                    raise Exception
                ai_response = ask_nemotron(input)
                
                output = normalize_ai_response(ai_response)
                if not output or not isinstance(output, str):
                    error_payload = "error"
                    with open(USER_GOAL_FILE, "w") as f:
                        f.write(error_payload)
                    print("Error: Invalid or missing AI response; saved fallback error action.")
                    continue

                print(f"Final Decision: {output}")
                
                # Save it for Member 4
                with open(USER_GOAL_FILE, "w") as f:
                    f.write(output)
                print(f"Saved user_goal.txt")
                    
            except Exception as e:
                print(f"Error processing frame: {e}")
            finally:
                # Delete the trigger file so we don't process it twice
                if os.path.exists(TRIGGER_FILE_ONE):
                    os.remove(TRIGGER_FILE_ONE)
                if os.path.exists(TRIGGER_FILE_TWO):
                    os.remove(TRIGGER_FILE_TWO)
                
        # Pause briefly to prevent maxing out the CPU
        time.sleep(0.2)

if __name__ == "__main__":
    # If the ipc_data folder doesn't exist yet, create it safely
    if not os.path.exists(IPC_FOLDER):
        os.makedirs(IPC_FOLDER)
        
    start_brain_service()