from openai import OpenAI
from dotenv import load_dotenv
import os

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
                    messages=messages
                )
                return completion.choices[0].message.content
        except Exception as e:
            return f"An error occurred: {e}"
