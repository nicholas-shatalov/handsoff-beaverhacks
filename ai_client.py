from openai import OpenAI
from dotenv import load_dotenv
import processor
import config
import os

# Load API keys
load_dotenv()

# Initialize Models
nemo1 = OpenAI(
  base_url="https://integrate.api.nvidia.com/v1",
  api_key=os.getenv("NVIDIA_API_KEY") 
)

nemo2 = OpenAI(
  base_url="https://integrate.api.nvidia.com/v1",
  api_key=os.getenv("NVIDIA_API_KEY") 
)

nemo_gui = OpenAI(
  base_url="https://integrate.api.nvidia.com/v1",
  api_key=os.getenv("NVIDIA_API_KEY") 
)

nemo_writing = OpenAI(
  base_url="https://integrate.api.nvidia.com/v1",
  api_key=os.getenv("NVIDIA_API_KEY") 
)

def ask_nemotron_one(user_goal, text_input, image_input):
    return processor.run_nemotron(nemo1, config.CACHED_MESSAGE_1, user_goal, text_input, image_input, json_format=False)

def ask_nemotron_two(user_goal, text_input, image_input):
    return processor.run_nemotron(nemo2, config.CACHED_MESSAGE_2, user_goal, text_input, image_input, json_format=True)

def ask_nemo_gui(location, image_b64):
    return processor.run_nemotron_gui(nemo_gui, config.CACHED_MESSAGE_3, location, image_b64)

def ask_nemo_writing(json_packet):
    return processor.run_nemotron_gui(nemo_writing, config.CACHED_MESSAGE_4, json_packet)