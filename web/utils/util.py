from typing import List, Dict

def format_conversation(history: List[Dict[str, str]], user_input: str, sys_prompt: str=None ,window_size: int = 5):
    messages = []
    if sys_prompt:
        messages.append({"role": "system", "content": sys_prompt})

    for entry in history[-window_size:]:
        messages.append({"role": "user", "content": entry.get("user", "")})
        messages.append({"role": "assistant", "content": entry.get("assistant", "")})
    messages.append({"role": "user", "content": user_input})

    return messages