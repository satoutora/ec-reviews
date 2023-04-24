import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))))

from database import repository
from constant import ecweb_constant
import requests
from bs4 import BeautifulSoup
import json
import datetime, time

class SimpleRequestLazada():
    id_product = None
    urlProduct = None

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

    def __init__(self, urlProduct=None, *args, **kwargs):
        super(SimpleRequestLazada, self).__init__(*args, **kwargs)
        self.urlProduct = urlProduct


    def get_API_by_itemId_and_totalReview(self, urlProduct):
        listPageAPI = []
        product = {}

        try:
            tmp = urlProduct[urlProduct.rfind('-i'):urlProduct.find('.html?')]
            itemId = tmp[tmp.find('-i') + 2:tmp.find('-s')]

            api = ecweb_constant.API_LAZADA.format(itemId, 1)
            session = requests.Session()
            response = session.get(api, headers=self.header)
            response_data = response.json()
            totalPages = response_data['model']['paging']['totalPages']

            product['name'] = response_data['model']['item']['itemTitle']
            product['product_url'] = response_data['model']['item']['itemUrl']
            product['product_img'] = response_data['model']['item']['itemPic']
            product['shop_id'] = response_data['model']['item']['sellerId']
            product['total_rating'] = response_data['model']['ratings'][
                'average']
            product['source_id'] = response_data['model']['item']['itemId']
            product['source'] = 'lazada'

            # print(product)
            if totalPages > 20: totalPages = 20

            self.id_product = repository.saveProduct(product)

            for page in range(1, totalPages + 1):
                pageAPI = ecweb_constant.API_LAZADA.format(itemId, page)
                listPageAPI.append(pageAPI)

        except Exception as e:
            print(e)

        return listPageAPI

    def convertDatetime(self, date):
        try:
            if date.find("tuần trước"):
                week = date[0]
                today = datetime.datetime.now()
                tmp = datetime.timedelta(days=int(week) * 7)
                create_date = (today - tmp).date()
                return create_date
            else:
                format_date = "{}/{}/{}".format(
                    date.split(" ")[0],
                    date.split(" ")[2],
                    date.split(" ")[3])
                create_date = datetime.strptime(format_date, '%d/%m/%Y').date()
                return create_date
        except Exception as e:
            print(e)

    def start_requests(self):
        #lazada
        start_urls = self.get_API_by_itemId_and_totalReview(self.urlProduct)
        for api in start_urls:
            session = requests.Session()
            response = session.get(url=api, headers=self.header)
            self.parse(response)
            time.sleep(3)

    def parse(self, response):
        # lazada
        try:
            data = response.json()
            reviews = data['model']['items']

            for data_review in reviews:
                review = {}
                review['id_product'] = self.id_product
                review['product_info'] = data_review['skuInfo'] if data_review['skuInfo'] != None else ""
                review['rating_star'] = data_review['rating']
                review['review_title'] = data_review['reviewTitle'] if data_review['reviewTitle'] != None else ""
                review['review_content'] = data_review['reviewContent'] if data_review['reviewContent'] != None else ""
                review['buyer_id'] = data_review['buyerId']
                review['buyer_name'] = data_review['buyerName']
                review['review_create_date'] = self.convertDatetime(date=data_review['reviewTime'])
                review['agree_count'] = data_review['likeCount'] if data_review['likeCount'] != None else 0
                review['source_id'] = data_review['reviewRateId']

                # print(review['review_create_date'])
                list_media = []
                images = data_review['images']
                if images != None:
                    for image in images:
                        media = {}
                        media['type'] = 'image'
                        media['url_media'] = image['url']
                        list_media.append(media)

                repository.saveReview(review, list_media)
        except BaseException as e:
            print(e)
            exit()
