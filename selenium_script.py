from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pymongo import MongoClient
import requests
import time
import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from templates.config import Config

# MongoDB setup
client = MongoClient(Config.MONGO_URL)
db = client['twitter_trends']
collection = db['trends']

# Selenium setup
def get_driver():
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

def safe_quit(driver):
    """Safely quit the WebDriver."""
    try:
        if driver:
            driver.quit()
            print("Driver successfully quit.")
    except Exception as e:
        print("Error while quitting driver:", e)

# Fetch the current IP address using requests
def get_ip_address():
    try:
        response = requests.get("http://httpbin.org/ip", timeout=10)  # Fetch IP using requests
        response.raise_for_status()  # Raise error for bad responses
        ip_data = response.json()
        return ip_data.get('origin')
    except requests.RequestException as e:
        print(f"Error fetching IP address: {e}")
        return "Unknown"

def fetch_trends():
    driver = None
    try:
        print("Step 1: Fetching Current IP Address")
        ip_address = get_ip_address()
        print(f"Current IP Address: {ip_address}")

        print("Step 2: Setting up WebDriver")
        driver = get_driver()

        print("Step 3: Navigating to Twitter login page")
        driver.get('https://x.com/login')
        time.sleep(5)  # Allow time for the page to load

        print("Step 4: Logging in to Twitter")
        username = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.NAME, 'text'))
        )
        username.send_keys(Config.TWITTER_USERNAME)  # Replace with actual username
        username.send_keys(Keys.RETURN)

        time.sleep(3)  # Wait for password field to appear
        password = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.NAME, 'password'))
        )
        password.send_keys(Config.TWITTER_PASS)  # Replace with actual password
        password.send_keys(Keys.RETURN)

        print("Step 5: Navigating to Twitter Trending Page")
        WebDriverWait(driver, 30).until(
            EC.url_contains("https://x.com/home")
        )  # Ensure login is complete before navigating
        driver.get('https://x.com/explore/tabs/trending')
        time.sleep(5)  # Allow time for the page to load

        print("Step 6: Extracting trends from the trending page")
        trends_section = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.XPATH, '//div[contains(@data-testid, "trend")]'))
        )
        trends = trends_section.find_elements(By.XPATH, '//span/span[contains(., "#")]')

        top_trends = [trend.text for trend in trends if trend.text]

        if not top_trends:
            print("No trends found. Adjust the XPath or wait longer for content to load.")
        else:
            top_trends = list(set(top_trends))[:10]  # Ensure uniqueness and limit to top 10
            print("Fetched Trends:", top_trends)

            trend_data = {
                "unique_id": str(datetime.datetime.now().timestamp()),
                "trends": top_trends,
                "timestamp": datetime.datetime.now(),
                "ip_address": ip_address
            }

            print("Step 7: Storing trends in MongoDB")
            collection.insert_one(trend_data)
            print("Successfully fetched and stored trends:", top_trends)

    except Exception as e:
        print("An error occurred:", str(e))
    finally:
        safe_quit(driver)

if __name__ == "__main__":
    fetch_trends()
