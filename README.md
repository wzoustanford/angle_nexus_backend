# angle
code base for angle

# Illumenti Backend

## Setup in local

1. create python environment
```bash
python -m venv env
# OR
python3 -m venv env
# THEN

source angle_env/bin/activate

```
python test_build_dataset.py -wi 2 -ns 4 

2. Install dependencies

```bash
pip install -r requirements.txt
# OR
pip3 install -r requirements.txt
```

3. Export development variables

```bash
export FLASK_ENV=development
export FLASK_APP=main
```

4. Start development server

```
flask run
```

## Directory Structure

```
src
|----main.py
|----modules
    |
    |_  pricing_data
    |   |_  main.py
    |   |_  __init__.py
    |   
    |_  recommendations
        |_  main.py
        |_  __init__.py
```
