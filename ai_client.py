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

def initialize():
    print("Caching nemo1")
    processor.cache_model(nemo1, config.CACHED_MESSAGE_1)
    print("Caching nemo2")
    processor.cache_model(nemo2, config.CACHED_MESSAGE_2)

def ask_nemotron_one(user_goal, text_input, image_input):
    return processor.run_nemotron(nemo1, config.CACHED_MESSAGE_1, user_goal, text_input, image_input)

def ask_nemotron_two(user_goal, text_input, image_input):
    return processor.run_nemotron(nemo2, config.CACHED_MESSAGE_2, user_goal, text_input, image_input)