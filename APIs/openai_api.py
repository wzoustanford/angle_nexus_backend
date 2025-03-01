from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()


class OpenAIChatClient:
    def __init__(self, response_format,model="deepseek-reasoner"):
        
        if model=="deepseek-reasoner":
            self.client = OpenAI(api_key=os.environ.get("DEEPSEEK_KEY"),base_url=os.environ.get("DEEPSEEK_BASE_URL"))
        else:
            self.client = OpenAI(api_key=os.environ.get("OPENAI_KEY"))
        self.model = model
        self.response_format=response_format

    def create_chat_completion(self, messages):
        try:
            if self.model=="deepseek-reasoner":
                completion = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,

                )
                return completion.choices[0].message.content

            else:
                completion = self.client.beta.chat.completions.parse(
                    model=self.model,
                    messages=messages,
                    response_format=self.response_format
                )
                return completion.choices[0].message.parsed
        except Exception as e:
            return f"An error occurred: {e}"
