from openai import OpenAI

def build_contents(user_goal, text_input, image_input):
    contents_list = []
    
    if user_goal is not None:
        contents_list.append({"type": "text", "text": f"User Goal: {user_goal}"})

    if text_input is not None:
        contents_list.append({"type": "text", "text": f"Data: {text_input}"})

    if image_input is not None:
        contents_list.append({"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_input}"}})

    return contents_list

def run_nemotron(client, cached_message, user_goal, text_input, image_input, json_format):
    
    contents = build_contents(user_goal, text_input, image_input)
    if json_format:
        contents.append({"type": "text", "text": "Remember: respond ONLY in the exact JSON format specified. No extra text, no markdown."})

    dynamic_message = {
        "role": "user",
        "content": contents
    }
    
    completion = client.chat.completions.create(
      model="nvidia/nemotron-3-nano-omni-30b-a3b-reasoning",
      messages=[*cached_message, dynamic_message],
      temperature=0, 
      top_p=1,
      max_tokens=4096, 
      extra_body={"chat_template_kwargs":{"enable_thinking":True},"reasoning_budget":16384},
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

def run_nemotron_gui(client, cached_message, location, image_b64):
    dynamic_message = {
        "role": "user",
        "content": [
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{image_b64}"}
            },
            {
                "type": "text",
                "text": 
                    f"Screenshot resolution: 1920x1200.\n"
                    f"Find this element: {location}\n"
                    f"Look at the screenshot, identify the element, and output its center coordinates.\n"
                    f"Do NOT second-guess yourself. Make one decision and output it.\n" 
                     "Respond ONLY with valid JSON: {'name': 'click', 'arguments': {'x': <int>, 'y': <int>}}}}"
            }
        ]
    }

    completion = client.chat.completions.create(
      model="nvidia/nemotron-3-nano-omni-30b-a3b-reasoning",
      messages=[*cached_message, dynamic_message],
      temperature=0, 
      top_p=1,
      max_tokens=512, 
      extra_body={"chat_template_kwargs":{"enable_thinking":True},"reasoning_budget":2048},
      stream=False
    )

    # Print the model's internal reasoning to the terminal (Great for demo!)
    '''reasoning = None
    if completion.choices and len(completion.choices) > 0:
        reasoning = getattr(completion.choices[0].message, "reasoning_content", None)
    if reasoning:
        print(f"\nInternal Logic:\n{reasoning}\n")'''

    if not completion.choices or len(completion.choices) == 0:
        return None

    return completion.choices[0].message.content

def run_nemotron_writing(client, cached_message, json_packet, timeout=45):

    # Extract the text prompt from the action packet
    text_prompt = json_packet.get("arguments", {}).get("text_prompt", "")

    if not text_prompt:
        print("No text_prompt found in writing json_packet")
        return None

    dynamic_message = {
        "role": "user",
        "content": [
            {
                "type": "text",
                "text": (
                    f"Write the following content: {text_prompt}\n\n"
                    f"REQUIREMENTS:\n"
                    f"- Write the full content immediately, do not summarize or outline it\n"
                    f"- Do not include any preamble like 'Here is your email:' or 'Sure!'\n"
                    f"- Do not include any commentary after the content\n"
                    f"- Match the tone and format to the content type\n"
                    f"- If it is an email, start with the greeting and end with a sign-off\n"
                    f"- If it is a message or post, write it ready to send as-is\n"
                    f"- If it is a document or report, include appropriate structure and sections\n"
                    f"- Output ONLY the final written content, nothing else"
                )
            }
        ]
    }

    try:
        completion = client.chat.completions.create(
            model="nvidia/nemotron-3-nano-omni-30b-a3b-reasoning",
            messages=[*cached_message, dynamic_message],
            temperature=0.7,   # higher = more natural and creative writing
            top_p=1,
            max_tokens=4096,
            extra_body={
                "chat_template_kwargs": {"enable_thinking": True},
                "reasoning_budget": 2048  # writing doesn't need much reasoning
            },
            timeout=timeout,
            stream=False
        )
    except Exception as e:
        print(f"Writing API call failed: {e}")
        return None

    reasoning = getattr(completion.choices[0].message, "reasoning_content", None)
    if reasoning:
        print(f"\nInternal Logic:\n{reasoning}\n")

    if not completion.choices:
        return None

    content = completion.choices[0].message.content
    if not content or content.strip() == "":
        print("Writing model returned empty response")
        return None

    return content.strip()