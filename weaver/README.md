# Weaver

code base for weaver ai

# Weaver Ai Backend

## Setup in local

1. create python environment

```bash
python -m venv aivenv
# OR
python3 -m venv aivenv
# THEN

source aivenv/bin/activate

```

2. Install dependencies

```bash
pip install -r weaver/requirements.txt
# OR
pip3 install -r weaver/requirements.txt
```

3. Create .env file

```bash
OPENAI_KEY=
DEEPSEEK_KEY=
DEEPSEEK_BASE_URL=
FINANCIAL_KEY=

```

4. Start development server

```
flask run
```

4. Start production server  ##port is not fixed rin on any port.

```
cd weaver

gunicorn main:app -b 0.0.0.0:5001 -w 4 -t 300

#### or running in background
gunicorn main:app -b 0.0.0.0:5001 -w 4 -t 300 --daemon

```

How to run command using curl command.

```
1) for Local system command

curl -X POST http://localhost:5001/weaver -H "Content-Type: application/json" -d '{"user_input": "I want to see the combined cash flow number in USD of Microsoft for the past two years.", "history": [], "model_name": "o3-mini"}'

2) for Production server command
curl -X POST http://{production_server_public_IP}:5001/weaver -H "Content-Type: application/json" -d '{"user_input": "I want to see the combined cash flow number in USD of Microsoft for the past two years.", "history": [], "model_name": "o3-mini"}'

Explaination API parameters:

1) user_input => type => string => this is basically user input.
Example: I want to see the combined cash flow number in USD of Microsoft for the past two years.

2)history =>type => list => This parameter accept previous user chat history and maintain sliding window conversation.
Example: 
[
	{"role":"user", "content":"I want to see the combined cash flow number in USD of Tesla for the last year."},
	{"role":"user", "assistant":"For fiscal year 2024, Tesla’s cash flow statement shows a net change in cash of 2,788,000,000 USD, which represents the combined cash flow from its operating, investing, and financing activities for the last year."},
........
........
]

3) model_name => type => string => this parameter si for model name we set bydefault model name is o3-mini
   
```
