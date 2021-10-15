import os
import smtplib
from email.mime.text import MIMEText
import logging
import itertools
from typing import List
from time import sleep

from bs4 import BeautifulSoup
import requests

PING_TARGET = [
    "http://preorders.kr/product/store-list?id=174",
    "http://preorders.kr/product/store-list?id=175",
    "http://preorders.kr/product/store-list?id=176",
    "http://preorders.kr/product/store-list?id=177",
    # "http://preorders.kr/product/store-list?id=72"
]


class PreOrdersCrawler:
    shop_details = []
    shop_details_has_product = []

    def __init__(self, refresh_time: int, alarm_email: str, urls: list):
        self.refresh_time = refresh_time
        self.alarm_email = alarm_email
        self.urls = urls
        logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)

    def request_to_html(self) -> List[str]:
        html_list = [requests.get(url).text for url in self.urls]
        return html_list

    @staticmethod
    def generate_bs_instances(htmls: List[str]) -> List[BeautifulSoup]:
        bs_instacnes = [BeautifulSoup(html, 'html.parser') for html in htmls]
        return bs_instacnes

    @classmethod
    def get_product_status(cls, bs_instances: List[BeautifulSoup]) -> List[dict]:
        shop_list = list(itertools.chain(*[bs_instance.find_all('div', attrs={'class': 'product-info'})
                                                  for bs_instance in bs_instances]))

        try:
            logging.info(f":::::{len(shop_list)} 개의 상점 검색 완료:::::")
            [cls.shop_details.append({
                "shop": shop.find_all('p', attrs={'class': 'shop-name'})[0].text,
                "product": shop.find_all('p', attrs={'class': 'product-title'})[0].text,
                "status": shop.find_all('span', attrs={'class': 'red-label'})[0].text,
            }) for shop in shop_list]
            logging.info(f":::::{len(shop_list)} 개의 상점 재고 없음:::::")
        except IndexError:
            [cls.shop_details_has_product.append({
                "shop": shop.find_all('p', attrs={'class': 'shop-name'})[0].text,
                "product": shop.find_all('p', attrs={'class': 'product-title'})[0].text
            })
                for shop in shop_list if len(shop.find_all('span', attrs={'class': 'red-label'})) == 0
                if len(shop.find_all('p', attrs={'class': 'product-title'})) != 0]

            logging.info(f"""
            다음 매장에서 재고 상품이 발견되었습니다.
            {[shop for shop in cls.shop_details_has_product]}
            """)

            print(cls.shop_details_has_product[0])
            print(cls.shop_details_has_product)
            email_sender(email="ddhyun93@gmail.com",
                         subject=f"[프리오더스 재고 상품 발견: ]{cls.shop_details_has_product[0].get('shop')} 등",
                         msg=f"{[detail for detail in cls.shop_details_has_product]}")

            cls.shop_details_has_product = []
            cls.shop_details = []

    def initialize(self, bs_instances):
        while True:
            self.get_product_status(bs_instances=bs_instances)
            sleep(self.refresh_time)


def email_sender(email: str, subject: str, msg: str):
    smtp = smtplib.SMTP_SSL("smtp.gmail.com", 465)
    smtp.set_debuglevel(1)
    smtp.ehlo()
    smtp.login(email, os.getenv("email_password"))

    msg = MIMEText(msg)
    msg['Subject'] = "[프리오더스 재고 상품 발견]"
    msg['To'] = email
    msg['FROM'] = email
    smtp.sendmail(email, email, msg.as_string())
    smtp.quit()
    return {"stauts": 200, "mail_subject": msg['Subject']}


if __name__ == "__main__":
    crawler = PreOrdersCrawler(refresh_time=5, alarm_email="ddhyun93@gmail.com", urls=PING_TARGET)
    html_list = crawler.request_to_html()
    bs_instance = crawler.generate_bs_instances(html_list)
    crawler.initialize(bs_instance)