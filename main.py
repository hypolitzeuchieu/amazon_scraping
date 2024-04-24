from amazon_bot import AmazonBot
from pymongo import MongoClient
from dotenv import load_dotenv
import os
from pymongo.server_api import ServerApi

load_dotenv()

try:
    uri = "mongodb+srv://"+os.getenv("MONGODB_USERNAME") + \
          ":"+os.getenv("MONGODB_PASSWORD") + \
           "@"+os.getenv("MONGODB_DOMAIN") + \
          "/?retryWrites=true&w=majority&appName=Cluster0"
    client = MongoClient(uri, server_api=ServerApi('1'))
    client.server_info()

except Exception as e:
    print(f"something went wrong to mongodb:{e}")
    raise e

bot = AmazonBot(mongodb_client=client)

bot.scrape_urls()
bot.close()
