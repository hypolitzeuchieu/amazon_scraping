import datetime

from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By


class AmazonBot:
    def __init__(self, mongodb_client):
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36"
        chrome_options = Options()
        chrome_options.add_argument(f"user-agent={user_agent}")
        chrome_options.add_experimental_option("detach", True)
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 10)
        self.mongodb_client = mongodb_client

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

    def get_product_price(self, product_url: str):
        try:
            self.driver.get(product_url)

            xpath = '//*[@id="corePrice_desktop"]/div/table/tbody/tr[2]/td[2]/span[1]/span[2]'
            prices = self.wait.until(EC.presence_of_element_located((By.XPATH, xpath))).text[1:]
            return prices
        except Exception:
            path = '//*[@id="usedBuySection"]/div[1]/div/span[2]'
            prices = self.wait.until(EC.presence_of_element_located((By.XPATH, path))).text[1:]
            return prices

        except NoSuchElementException as e:
            print(f"error to fetch price from {product_url}: {e}")
        return None

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
        product_urls = self.mongodb_client['amazon_db']['products_urls'].find()
        for product_url in product_urls:
            print(product_url)
            print()
            data = self.get_product_data(product_url['url'])
            self.mongodb_client['amazon_db']['products_data'].update_many({'url': data['url']}, {'$set': data}, upsert=True)

    def close(self):
        self.driver.close()
