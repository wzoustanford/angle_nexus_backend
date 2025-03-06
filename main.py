from APIs.openai_api import OpenAIChatClient
from Models.model import *
from Prompts.prompt import *
from APIs.fmp_api import *
from datetime import date
import datetime
import json
import os


####Switch model 
# model="deepseek-reasoner"
model="o3-mini"




chat_client = OpenAIChatClient(model=model)
sys_prompt=q_analysis_sys_prompt()
fin_apis=FinApis_details()
today_date=date.today()
user_statement="""I need cashflow statment of Miscrosoft last 2 year, and Apple and Tesla and please compare with each other and make final conclusion."""


messages = [
        {"role": "system", "content": sys_prompt},
        {"role": "user", "content": f"Here is Financial apis details:\n {fin_apis}, and here is ther user input: {user_statement}.\n Today Date is: {today_date}"},
    ]

print(f"API Json response making in progress using {model} model........")
output_message = chat_client.create_chat_completion(messages)
print(f"API Json response making End")
if model=="deepseek-reasoner":
    output_message = output_message.strip("```json").strip("```").strip()
    llm_json_response=json.loads(output_message)
    print("LLM API Response: ",json.dumps(llm_json_response,indent=4))

else: 
    llm_json_response=json.loads(output_message)
    print("LLM API Response: ",json.dumps(llm_json_response,indent=4))


print(f"Calling Finance APIs in progress.")
finance_api_responses={}
if llm_json_response:
    for key,api_json in llm_json_response.items():
        response=get_finance_api_data(api_json['api'])
        if response:
            finance_api_responses[key]=response
    print(f"Calling Finance APIs End.")
    if finance_api_responses:
        messages2 = [
                {"role": "system", "content": combine_results_sys_promt()},
                {"role": "user", "content": f"Here is Financial apis reponses:\n {json.dumps(finance_api_responses)}, and here is ther user input: {user_statement}.\n Today Date is: {today_date}"},
            ]
        print(f"Combining all results in progress using {model} model.")
        combine_response = chat_client.create_chat_completion(messages2)
        print(f"Combining all results End.")
        print("combine_response: ",combine_response)
    else:
        print("No finance API data found")

else:
    print("No finance API found.")

try:
    #### save into the .txt file each query
    output_dir="Output/"
    os.makedirs(output_dir, exist_ok=True)
    now = datetime.datetime.now()
    filename = now.strftime("%Y%m%d_%H%M%S") + "_query.txt"
    with open(output_dir+filename, "w") as file:
        file.write("User Query:\n")
        file.write(str(user_statement) + "\n\n")
        
        file.write("LLM JSON Response:\n")
        file.write(str(json.dumps(llm_json_response,indent=4)) + "\n\n")
        
        file.write("Combined Response:\n")
        file.write(str(combine_response) + "\n")

    print(f"Results saved in file: {filename}")
except Exception as e:
    print("Error: ",e)
finally:
     file.close()

