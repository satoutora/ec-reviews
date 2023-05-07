import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))))

from database import repository
from constant import ecweb_constant
import requests
from bs4 import BeautifulSoup
import json
import datetime, time


class UpdateProductLazada():
    product = None
    dateNewest = None

    header = {
        'authority': 'my.lazada.vn',
        'accept': 'application/json, text/plain, */*',
        'accept-encoding': 'gzip, deflate, br',
        'accept-language':
        'vi-VN,vi;q=0.9,fr-FR;q=0.8,fr;q=0.7,en-US;q=0.6,en;q=0.5',
        'origin': 'https://www.lazada.vn',
        'referer': 'vi-VN,vi;q=0.9,fr-FR;q=0.8,fr;q=0.7,en-US;q=0.6,en;q=0.5',
        'user-agent':
        'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
        'x-csrf-token': 'be3686eeb0a7',
        'x-requested-with': 'XMLHttpRequest',
        'cookie': 'lzd_uid=200083818586;'
    }

    def __init__(self, product=None, *args, **kwargs):
        super(UpdateProductLazada, self).__init__(*args, **kwargs)
        try:
            self.product = product
            self.dateNewest = repository.getReviewDateNewest(product)
        except Exception as e:
            print(e)

    def convertDatetime(self, date):
        try:
            if date.find("tuần trước"):
                week = date[0]
                today = datetime.datetime.now()
                tmp = datetime.timedelta(days=int(week) * 7)
                create_date = (today - tmp).date()
                return datetime.datetime(create_date.year, create_date.month, create_date.day)
            else:
                format_date = "{}/{}/{}".format(
                    date.split(" ")[0],
                    date.split(" ")[2],
                    date.split(" ")[3])
                create_date = datetime.strptime(format_date, '%d/%m/%Y %H:%M:%S')
                return create_date
        except Exception as e:
            print(e)

    def start_requests(self):
        #lazada get review newest

        page = 1
        startDate = self.dateNewest + datetime.timedelta(days=1)

        while startDate > self.dateNewest:
            try:
                pageAPI = ecweb_constant.API_LAZADA.format(self.product['source_id'], page)

                session = requests.Session()
                response = session.get(url=pageAPI, headers=self.header)
                data = response.json()

                reviews = data['model']['items']

                for data_review in reviews:
                    review = {}
                    review['id_product'] = self.product['id_product']
                    review['product_info'] = data_review['skuInfo'] if data_review['skuInfo'] != None else ""
                    review['rating_star'] = data_review['rating']
                    review['review_title'] = data_review['reviewTitle'] if data_review['reviewTitle'] != None else ""
                    review['review_content'] = data_review['reviewContent'] if data_review['reviewContent'] != None else ""
                    review['buyer_id'] = data_review['buyerId']
                    review['buyer_name'] = data_review['buyerName']
                    review['review_create_date'] = self.convertDatetime(date=data_review['reviewTime'])
                    review['agree_count'] = data_review['likeCount'] if data_review['likeCount'] != None else 0
                    review['source_id'] = data_review['reviewRateId']

                    startDate = review['review_create_date']
                    if startDate <= self.dateNewest:
                        print(f"done lazada {self.product['id_product']}")
                        break

                    list_media = []
                    images = data_review['images']
                    if images != None:
                        for image in images:
                            media = {}
                            media['type'] = 'image'
                            media['url_media'] = image['url']
                            list_media.append(media)

                    repository.saveReview(review, list_media)
                    repository.updateModifyProduct(self.product['id_product'])
                page = page + 1
                time.sleep(5)
                if page > 10: exit()
            except BaseException as e:
                print(e)
                exit()
