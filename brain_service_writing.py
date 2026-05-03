import os
import base64
import json
import ai_client
import screenshot


def normalize_ai_response(response):
    if not isinstance(response, str):
        return None 
    return response

def start_brain_service(json_packet):
    print("Writing brain service starting...")

    ai_response = ai_client.ask_nemo_writing(json_packet)
    print(f"AI Response: {ai_response}")

    string_response = normalize_ai_response(ai_response)
    print(f"Final Output nemo_gui: {string_response}")
    if string_response is None:
        print("Error on nemo_writing output")

    text_json = {"name": "type_text", "arguments": {"text": string_response}}

    return text_json