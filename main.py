from APIs.openai_api import OpenAIChatClient
from Models.model import *
from Prompts.prompt import *
from datetime import date
import json


model="deepseek-reasoner"
# model="gpt-4o-2024-08-06"




chat_client = OpenAIChatClient(response_format=APIModel,model=model)
sys_prompt=q_analysis_sys_prompt()
fin_apis=FinApis_details()
today_date=date.today()
user_statement="""I need cashflow statment of Miscrosoft last 2 year also pelase provide me data about the stockprice of both Microsoft adn Apple for last 1 year. """

messages = [
        {"role": "system", "content": sys_prompt},
        {"role": "user", "content": f"Here is Financial apis details:\n {fin_apis}, and here is ther user input: {user_statement}.\n Today Date is: {today_date}"},
    ]

output_message = chat_client.create_chat_completion(messages)
# print("output: ",output_message)
if model=="deepseek-reasoner":
    output_message = output_message.strip("```json").strip("```").strip()
    print(json.dumps(json.loads(output_message),indent=4))
else: 
    print(output_message.model_dump_json(indent=4))



