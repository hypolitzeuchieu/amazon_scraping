import datetime

from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By


class AmazonBot:
    def __init__(self, mongodb_client, server_smtp):
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36"
        chrome_options = Options()
        chrome_options.add_argument(f"user-agent={user_agent}")
        chrome_options.add_experimental_option("detach", True)
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 10)
        self.mongodb_client = mongodb_client
        self.server_smtp = server_smtp

    def get_product_title(self, product_url) -> str:
        try:
            title = self.wait.until(EC.presence_of_element_located((By.ID, "productTitle"))).text.strip()
            return title
        except Exception as e:
            print(f"Error to fetch title from {product_url}: {e}")

    def get_product_rating(self, product_url):
        try:
            xpath = '//*[@id="acrPopover"]/span[1]/a/span'
            rating = self.wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
            return rating.text
        except Exception as e:
            print(f"error to fetch the rate from {product_url}:{e}")
            return 0.0

    def get_product_nb_reviewers(self, product_url):
        try:
            xpath = '//*[@id="acrCustomerReviewText"]'
            nb_reviews1 = self.wait.until(EC.presence_of_element_located((By.XPATH, xpath))).text.strip()
            nb_reviews1 = nb_reviews1.replace(',', '')
            nb_reviews1 = int(nb_reviews1.split()[0])
            return nb_reviews1
        except Exception as e:
            print(f"error to fetch number of reviews from {product_url}: {e}")
            return None

    def get_product_price(self, product_url: str) -> float:
        try:
            self.driver.get(product_url)

            xpath = '//*[@id="corePrice_desktop"]/div/table/tbody/tr[2]/td[2]/span[1]/span[2]'
            prices = self.wait.until(EC.presence_of_element_located((By.XPATH, xpath))).text[1:]
            return float(prices)
        except Exception:
            path = '//*[@id="usedBuySection"]/div[1]/div/span[2]'
            prices = self.wait.until(EC.presence_of_element_located((By.XPATH, path))).text[1:]
            prices = prices.replace(',', '')
            return float(prices)

        except NoSuchElementException as e:
            print(f"error to fetch price from {product_url}: {e}")
        return 0.0

    def get_product_data(self, product_url):
        try:
            self.driver.get(product_url)
            return {
                'url': product_url,
                'product_title': self.get_product_title(product_url),
                'rating': self.get_product_rating(product_url),
                'number_of_reviews': self.get_product_nb_reviewers(product_url),
                'product_price': self.get_product_price(product_url),
                'update_at': datetime.datetime.now()
            }
        except Exception as e:
            print(f"Error to fetch content from {product_url}: {e}")

    def scrape_urls(self):
        while True:
            product_urls = self.mongodb_client['amazon_db']['products_urls'].find(
                {"$or": [
                    {"updated_at": None},
                    {"updated_at": {"$lte": datetime.datetime.now() - datetime.timedelta(minutes=5)}}
                ]
                })

            for product_url in product_urls:
                data = self.get_product_data(product_url['url'])
                self.mongodb_client['amazon_db']['products_data'].update_many({'url': product_url['url']},
                                                                              {'$set': data},
                                                                              upsert=True)
                self.mongodb_client["amazon_db"]['products_urls'].update_many({'url': product_url['url']}, {"$set": {
                    "updated_at": datetime.datetime.now()
                }})
                try:
                    last_product_price = self.mongodb_client['amazon_db']['products_prices'].find(
                        {'url': data['url']}).sort([('created_at', -1)]).limit(1).next()
                except StopIteration:
                    last_product_price = None

                if last_product_price is None:
                    self.mongodb_client['amazon_db']['products_prices'].insert_one({
                        'url': product_url['url'],
                        'product_price': data['product_price'],
                        'created_at': datetime.datetime.now()
                    })
                elif last_product_price is not None and last_product_price['product_price'] != data['product_price']:
                    self.mongodb_client['amazon_db']['products_prices'].insert_one({
                        'url': product_url['url'],
                        'product_price': data['product_price'],
                        'created_at': datetime.datetime.now()
                    })

                    if (type(data['product_price']) is int or type(data['product_price']) is float) and \
                            (type(last_product_price['product_price']) is int or type(
                                last_product_price['product_price']) is float):

                        dif_price_percentage = (1 - data['product_price'] / last_product_price['product_price']) * 100
                        if dif_price_percentage > 0:
                            message = f"""
                                The price of {self.get_product_title(product_url)} decrease by {dif_price_percentage} %, 
                                from {product_url['url']} .
                                Previous price: {last_product_price['product_price']} .
                                New price : {data['product_price']} .                           
                            """
                            message = message.encode('utf-8')
                            self.server_smtp.sendmail('hypolithypolit@gmail.com', 'hypolithypolit@gmail.com', message)

    def close(self):
        self.driver.close()
