import os
from dotenv import load_dotenv

# If you're using .env file, load it
load_dotenv()
class Config:
   TWITTER_USERNAME=  os.getenv('NAME_NEW')
   TWITTER_PASS = os.getenv('PASSWORD')
   MONGO_URL = os.getenv('MONGODB_URL')