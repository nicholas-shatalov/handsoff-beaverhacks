import os
import json

# Generate Prompts
SYSTEM_PROMPT_1 = """
You are the Interpreter (Agent 1) for an AI agent system called HandsOff, an autonomous accessibility agent. Your job is to translate raw, messy user inputs (audio transcripts or physical gesture descriptions) into a single, clear computer command.
Physical gesture descriptions will come with one word. Audio transcripts will come into the form of a long text.
RULES:

You must condense the input into exactly one short phrase.

You must NOT include any conversational filler.

You must format your output strictly starting with this exact phrase: 'Action requested: [insert specific action here]
"""


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

IPC_FOLDER = "ipc_data_two"
TOOLS_FILE = os.path.join(IPC_FOLDER, "tools.json")
JSON_PROMPT = build_tools_prompt(TOOLS_FILE)

SYSTEM_PROMPT_2 = """
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
4. You MUST use this following schema with NO additional fields:
[
    {"name": "open_url", "arguments": {"url": "https://youtube.com"}},
    {"name": "type_text", "arguments": {"text": "cat videos"}},
    {"name": "error", "arguments": {"reason": "explanation of why goal is not achievable"}}
]
"""

# Cached Prompts
CACHED_MESSAGE_1 = [
    {
        "role": "system",
        "content": SYSTEM_PROMPT_1
    },
    {
        "role": "assistant",
        "content": "Understood. I have internalized the context and am ready to process data inputs."
    }
]

CACHED_MESSAGE_2 = [
    {
        "role": "system",
        "content": SYSTEM_PROMPT_2
    },
    {
        "role": "assistant",
        "content": "Understood. I have internalized the context and am ready to process data inputs."
    }
]