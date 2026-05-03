import os
import base64
import json
import ai_client
import screenshot

def normalize_ai_response(ai_response):
    if ai_response is None:
        return None

    if not isinstance(ai_response, str):
        ai_response = str(ai_response)

    ai_response = ai_response.strip()

    if ai_response.lower() == "none":
        return None

    try:
        parsed = json.loads(ai_response)
    except json.JSONDecodeError:
        try:
            import ast
            parsed = ast.literal_eval(ai_response)
        except (ValueError, SyntaxError):
            print(f"Failed to parse GUI response: {ai_response}")
            return None

    # Handle if model wraps in a list e.g. [{"name": "click", "arguments": {...}}]
    if isinstance(parsed, list):
        if len(parsed) == 0:
            return None
        parsed = parsed[0]

    if not isinstance(parsed, dict):
        print(f"Unexpected response type: {type(parsed)}")
        return None

    # Validate name exists and is a string
    if "name" not in parsed or not isinstance(parsed["name"], str):
        print(f"Missing or invalid 'name' in response: {parsed}")
        return None

    # Validate arguments exists and is a dict
    if "arguments" not in parsed or not isinstance(parsed["arguments"], dict):
        print(f"Missing or invalid 'arguments' in response: {parsed}")
        return None

    return parsed

def start_brain_service(json_packet):
    print("GUi brain service starting...")

    location = json_packet['arguments']['location']

    image = screenshot.take_screenshot()
    ai_response = ai_client.ask_nemo_gui(location, image)
    print(f"AI Response: {ai_response}")

    if ai_response is None:
        print("GUI model returned None — no response generated")
        return None

    json_data = normalize_ai_response(ai_response.strip())
    print(f"Final Output nemo_gui: {json_data}")
    return json_data


