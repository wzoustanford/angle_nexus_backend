from APIs.openai_api import OpenAIChatClient
from flask import Flask, request, Response
from Prompts.prompt import *
from APIs.fmp_api import *
from Models.model import *
from datetime import date
from Utils.util import *
import json



app = Flask(__name__)

ALLOWED_MODELS = ["o3-mini", "GPT-4o","deepseek-reasoner"]# allowed models


@app.route("/")
def test():
    return "<p>Test, Api is working.</p>"

@app.route('/weaver', methods=['POST'])
def chat():
    try:
        chat_request = ChatRequest(**request.get_json())
    except ValidationError as e:
        return Response(f"Invalid input: {e}", status=400)
    
    if chat_request.model_name not in ALLOWED_MODELS:
        return Response(f"Model '{chat_request.model_name}' is not allowed.", status=400)

    chat_client = OpenAIChatClient(model=chat_request.model_name)
    sys_prompt = q_analysis_sys_prompt()
    fin_apis_details = FinApis_details()
    today_date = date.today()

    user_query=f"Here is Financial apis details:\n {fin_apis_details}, and here is ther user input: {chat_request.user_input}.\n Today Date is: {today_date}"

    messages = format_conversation(chat_request.history, user_query, sys_prompt, window_size=6)

    #generate json response k topis with right finance APIs 
    k_topics_str = chat_client.create_chat_completion(messages)
    k_topics_json=json.loads(k_topics_str)
    # print("k_topics_json: ",k_topics_json)

    finance_api_responses={}
    if k_topics_json:
        for key,api_json in k_topics_json.items():
            response=get_finance_api_data(api_json['api'])
            if response:
                finance_api_responses[key]=response
        if finance_api_responses:
            user_input=f"Here is Financial apis reponses:\n {json.dumps(finance_api_responses)}, and here is ther user input: {chat_request.user_input}.\n Today Date is: {today_date}"
            messages2=format_conversation(chat_request.history, user_input, combine_results_sys_promt(), window_size=6)
    else:
        messages2=format_conversation(chat_request.history, f"here is ther user input: {chat_request.user_input}.\n", combine_results_sys_promt(), window_size=6)
    return Response(chat_client.create_chat_stream(messages2),mimetype='text/plain')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)