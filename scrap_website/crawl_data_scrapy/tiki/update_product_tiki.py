import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))))

from database import repository
from constant import ecweb_constant
import requests
from bs4 import BeautifulSoup
import json
import datetime, time


class UpdateProductTiki():
    product = None
    dateNewest = None

    header = {
        'authority': 'tiki.vn',
        'accept': 'application/json, text/plain, */*',
        'accept-encoding': 'gzip, deflate, br',
        'accept-language':
        'vi-VN,vi;q=0.9,fr-FR;q=0.8,fr;q=0.7,en-US;q=0.6,en;q=0.5',
        'sec-ch-ua':
        '"Not?A_Brand";v="8", "Chromium";v="108", "Google Chrome";v="108"',
        'referer': 'https://tiki.vn/',
        'user-agent':
        'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
        'x-requested-with': 'XMLHttpRequest',
    }

    def __init__(self, product=None, *args, **kwargs):
        super(UpdateProductTiki, self).__init__(*args, **kwargs)
        try:
            self.product = product
            self.dateNewest = repository.getReviewDateNewest(product)
        except Exception as e:
            print(e)

    def convertDatetime(self, date):
        return datetime.datetime.fromtimestamp(date)

    def start_requests(self):
        #tiki get review newest
        itemId = self.product['source_id']
        shopId = self.product['shop_id']

        page = 1
        startDate = self.dateNewest + datetime.timedelta(days=1)

        while startDate > self.dateNewest:
            try:
                pageApi = ecweb_constant.API_TIKI.format(page, shopId, itemId)
                session = requests.Session()
                response = session.get(url=pageApi, headers=self.header)
                data = response.json()

                reviews = data['data']
                for data_review in reviews:
                    review = {}

                    review['id_product'] = self.product['id_product']
                    review['product_info'] = data_review['product_attributes'][0] if len(data_review['product_attributes'])>0 else ""
                    review['rating_star'] = data_review['rating']
                    review['review_title'] = data_review['title'] if data_review['title'] != None else ""
                    review['review_content'] = data_review['content'] if data_review['content'] != None else ""
                    review['buyer_id'] = data_review['created_by']['id']
                    review['buyer_name'] = data_review['created_by']['full_name']
                    review['review_create_date'] = self.convertDatetime(date=data_review['created_at'])
                    review['agree_count'] = data_review['thank_count'] if data_review['thank_count'] != None else 0
                    review['source_id'] = data_review['id']

                    startDate = review['review_create_date']
                    if startDate <= self.dateNewest:
                        print(f"done tiki {self.product['id_product']}")
                        break

                    list_media = []
                    images = data_review['images']
                    if images != None:
                        for image in images:
                            media = {}
                            media['type'] = 'image'
                            media['url_media'] = image['full_path']
                            list_media.append(media)

                    repository.saveReview(review, list_media)
                    repository.updateModifyProduct(self.product['id_product'])
                page = page + 1
                time.sleep(1)
            except BaseException as e:
                print(e)
                exit()
