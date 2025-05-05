import os
import time
from dotenv import load_dotenv
import requests
import threading
from datetime import datetime, timedelta
from collections import deque
load_dotenv()
FINANCIAL_KEY = os.environ.get("FINANCIAL_KEY")

class RateLimiter:
    """ Rate limiter to ensure we don't exceed 300 API calls per minute to FMP """
    
    def __init__(self, calls_per_minute=300):
        self.calls_per_minute = calls_per_minute
        self.call_timestamps = deque()
        self.lock = threading.Lock()
        
    def wait_if_needed(self):
        """ Wait if we're approaching the rate limit """
        with self.lock:
            now = datetime.now()
            
            # Remove timestamps older than 1 minute
            while self.call_timestamps and self.call_timestamps[0] < now - timedelta(minutes=1):
                self.call_timestamps.popleft()
            
            # If we are at the limit, wait until the oldest call is more than 1 minute ago
            if len(self.call_timestamps) >= self.calls_per_minute:
                sleep_time = (self.call_timestamps[0] + timedelta(minutes=1) - now).total_seconds()
                if sleep_time > 0:
                    print(f"Rate limit approaching! Waiting for {sleep_time:.2f} seconds...")
                    # Release the lock while sleeping
                    self.lock.release()
                    time.sleep(sleep_time)
                    self.lock.acquire()
            
            # Record this call
            self.call_timestamps.append(now)


def get_finance_api_data(url, rate_limiter, max_retries=3, wait_time=5):
    retries = 0

    while retries < max_retries:
        try:
            # Wait if needed before making the API call
            rate_limiter.wait_if_needed()
            
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(f"{url}&apikey={FINANCIAL_KEY}", headers=headers)
            
            response.raise_for_status()
            return response.json()

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                print(f"Rate limit hit anyway! Retrying in {wait_time} seconds...")
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