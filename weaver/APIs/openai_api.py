from openai import OpenAI
from dotenv import load_dotenv
import os
import time

load_dotenv()

##ai models
class OpenAIChatClient:
    def __init__(self,model="deepseek-reasoner"):
        
        if model=="deepseek-reasoner":
            self.client = OpenAI(api_key=os.environ.get("DEEPSEEK_KEY"),base_url=os.environ.get("DEEPSEEK_BASE_URL"))
        else:
            self.client = OpenAI(api_key=os.environ.get("OPENAI_KEY"))
        self.model = model

    def create_chat_completion(self, messages):
        try:
            if self.model=="deepseek-reasoner":
                completion = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,

                )
                return completion.choices[0].message.content

            else:
                completion = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    reasoning_effort="low"
                )
                return completion.choices[0].message.content
        except Exception as e:
            return f"An error occurred: {e}"
    
    def create_chat_stream(self, messages):
        try:
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=True,
                reasoning_effort="low"
            )
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            return f"An error occurred: {e}"
