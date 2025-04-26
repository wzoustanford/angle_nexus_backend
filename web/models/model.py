from pydantic import BaseModel,ValidationError
from typing import List, Dict

class ChatRequest(BaseModel):
    user_input: str
    history: List[Dict[str, str]] = []
    model_name: str = "o3-mini"