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
