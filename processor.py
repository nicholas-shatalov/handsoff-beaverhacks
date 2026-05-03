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

def run_nemotron_writing(client, cached_message, json_packet):
    
    completion = client.chat.completions.create(
      model="nvidia/nemotron-3-nano-omni-30b-a3b-reasoning",
      messages=[*cached_message, json_packet],
      temperature=0.3, 
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