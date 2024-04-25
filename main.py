from amazon_bot import AmazonBot
from pymongo import MongoClient
from dotenv import load_dotenv
import os
from pymongo.server_api import ServerApi
import ssl
import smtplib

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


try:
    context = ssl.create_default_context()
    server = smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context)
    server.login(os.getenv("SENDER_EMAIL"), os.getenv("EMAIL_PASSWORD"))
except Exception as e:
    raise e


bot = AmazonBot(mongodb_client=client, server_smtp=server)

bot.scrape_urls()
bot.close()
