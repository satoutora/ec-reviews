import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))))

from database import repository
from constant import ecweb_constant
import scrapy
from scrapy.crawler import CrawlerProcess
import requests
from bs4 import BeautifulSoup
import json
import datetime


class SingleProductShopeeSpider(scrapy.Spider):
    name = 'single-product-shopee'
    bfUrl = ""
    id_product = None

    header = {
        'authority': 'shopee.vn',
        'accept': 'application/json, text/plain, */*',
        'accept-encoding': 'gzip, deflate, br',
        'accept-language':
        'vi-VN,vi;q=0.9,fr-FR;q=0.8,fr;q=0.7,en-US;q=0.6,en;q=0.5',
        'sec-ch-ua': '"Not?A_Brand";v="8", "Chromium";v="108", "Google Chrome";v="108"',
        'referer': 'https://shopee.vn',
        'user-agent':
        'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
        'x-requested-with': 'XMLHttpRequest',
    }

    def get_API_by_itemId_shopId_and_totalReview(self, urlProduct):
        listPageAPI = []

        try:
            tmp = urlProduct[urlProduct.rfind('-i.') + 3 : urlProduct.find('?sp_atk=')]
            shopId = tmp.split('.')[0]
            itemId = tmp.split('.')[1]

            api = ecweb_constant.API_SHOPEE.format(itemId, 0, shopId)

            session = requests.Session()
            response = session.get(api, headers=self.header)
            response_data = response.json()
            totalRating = response_data['data']['item_rating_summary']['rating_total']

            ratingCount = response_data['data']['item_rating_summary']['rating_count']

            data_product = response_data['data']['ratings']
            product = {}
            for d_p in data_product:
                product['name'] = d_p['product_items'][0]['name']
                product['product_url'] = self.bfUrl
                product['product_img'] = ecweb_constant.SHOPEE_HOST_MEDIA + d_p['product_items'][0]['image']
                product['shop_id'] = d_p['shopid']
                product['total_rating'] = str(round(float(float(ratingCount[0])*1+
                                                    float(ratingCount[1])*2+
                                                    float(ratingCount[2])*3+
                                                    float(ratingCount[3])*4+
                                                    float(ratingCount[4])*5)/int(totalRating), 1))
                product['source_id'] = d_p['itemid']
                product['source'] = 'shopee'

                self.id_product = repository.saveProduct(product)
                break

            offset = 0
            while offset < totalRating:
                offsetApi = ecweb_constant.API_SHOPEE.format(itemId, offset, shopId)
                listPageAPI.append(offsetApi)
                offset = offset + 50

        except Exception as e:
            print(e)

        return listPageAPI

    def convertDatetime(self, date):
        return datetime.datetime.fromtimestamp(date)

    def __init__(self, urlProduct=None, *args, **kwargs):
        super(SingleProductShopeeSpider, self).__init__(*args, **kwargs)
        self.bfUrl = urlProduct
        self.start_urls = self.get_API_by_itemId_shopId_and_totalReview(urlProduct)

    def start_requests(self):
        #shopee
        for api in self.start_urls:
            yield scrapy.Request(api, headers=self.header)

    def parse(self, response):
        # shopee
        try:
            data = json.loads(response.body)
            reviews = data['data']['ratings']
            for data_review in reviews:
                review = {}
                review['id_product'] = self.id_product
                review['product_info'] = data_review['product_items'][0]['model_name'] if data_review['product_items'] != [] else ""
                review['rating_star'] = data_review['rating_star']
                review['review_title'] = ""
                review['review_content'] = data_review['comment'] if data_review['comment'] != None else ""
                review['buyer_id'] = data_review['userid']
                review['buyer_name'] = data_review['author_username']
                review['review_create_date'] = self.convertDatetime(date=data_review['ctime'])
                review['agree_count'] = data_review['like_count'] if data_review['like_count'] != None else 0
                review['source_id'] = data_review['cmtid']

                # print(review['review_create_date'])
                list_media = []
                images = data_review['images']
                if images != None:
                    for image in images:
                        media = {}
                        media['type'] = 'image'
                        media[
                            'url_media'] = ecweb_constant.SHOPEE_HOST_MEDIA + image
                        list_media.append(media)

                repository.saveReview(review, list_media)
        except BaseException as e:
            print(e)
            exit()




from scrapyscript import Job, Processor
# if __name__ == '__main__':
def startProcess(urlProduct):
    processor = Processor(settings=None)
    job = Job(SingleProductShopeeSpider, urlProduct=urlProduct)
    processor.run(job)
