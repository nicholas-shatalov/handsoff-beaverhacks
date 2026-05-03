from openai import OpenAI

def cache_model(client, cached_message):
    completion = client.chat.completions.create(
        model="nvidia/nemotron-3-nano-omni-30b-a3b-reasoning",
        messages=[*cached_message],  # prefix + small dynamic tail
        temperature=0,
        top_p=1,
        max_tokens=4096,
        extra_body={
            "chat_template_kwargs": {"enable_thinking": True},
            "reasoning_budget": 8192
        },
        stream=False
    )

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
      extra_body={"chat_template_kwargs":{"enable_thinking":True},"reasoning_budget":8192},
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