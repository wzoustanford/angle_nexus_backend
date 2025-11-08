import os
import json
import time
from dotenv import load_dotenv
import requests

load_dotenv()
FINANCIAL_KEY = os.environ.get("FINANCIAL_KEY")

def get_finance_api_data(url, max_retries=3, wait_time=5):
    retries = 0

    while retries < max_retries:
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(f"{url}&apikey={FINANCIAL_KEY}",headers=headers)

            response.raise_for_status()
            return response.json()

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                print(f"Rate limit hit! Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
                wait_time *= 2
                retries += 1
            else:
                print(f"HTTP Error {e.response.status_code}: {e.response.reason}")
                break

        except requests.exceptions.RequestException as e:
            print(f"Request Error: {e}")
            break

    return None
