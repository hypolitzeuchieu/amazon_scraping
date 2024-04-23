import requests


def main(url: str):
    response = requests.get(url)
    print(response.status_code)


if __name__ == '__main__':
    link = "https://www.amazon.com/Apple-iPhone-256GB-Midnight-Green/dp/B08BHXC5ZS/ref=sr_1_3?sr=8-3"

    print(main(link))
