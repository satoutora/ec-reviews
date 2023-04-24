import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))))

from database import repository
from constant import ecweb_constant
import requests
from bs4 import BeautifulSoup
import json
import datetime, time
from constant import ecweb_constant
import scrapy


class UpdateProductShopee(scrapy.Spider):
    name = 'update-product-shopee'
    product = None
    listReviewId = []

    header = {
        'authority': 'shopee.vn',
        'accept': 'application/json, text/plain, */*',
        'accept-encoding': 'gzip, deflate, br',
        'accept-language':
        'vi-VN,vi;q=0.9,fr-FR;q=0.8,fr;q=0.7,en-US;q=0.6,en;q=0.5',
        'sec-ch-ua':
        '"Not?A_Brand";v="8", "Chromium";v="108", "Google Chrome";v="108"',
        'referer': 'https://shopee.vn',
        'user-agent':
        'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
        'x-requested-with': 'XMLHttpRequest',
    }

    def __init__(self, product=None, *args, **kwargs):
        super(UpdateProductShopee, self).__init__(*args, **kwargs)
        try:
            self.product = product
            listReview = repository.getAllReviewByProduct(self.product['id_product'])
            for rv in listReview:
                self.listReviewId.append(str(rv['source_id']))
            self.listReviewId = set(self.listReviewId)
            print(f"aaaaaaa {self.listReviewId}")
            self.start_urls = self.get_API_by_itemId_shopId_and_totalReview()
        except Exception as e:
            print(e)

    def convertDatetime(self, date):
        return datetime.datetime.fromtimestamp(date)

    def get_API_by_itemId_shopId_and_totalReview(self):
        listPageAPI = []
        try:
            shopId = self.product['shop_id']
            itemId = self.product['source_id']

            api = ecweb_constant.API_SHOPEE.format(itemId, 0, shopId)

            session = requests.Session()
            response = session.get(api, headers=self.header)
            response_data = response.json()
            totalRating = response_data['data']['item_rating_summary'][
                'rating_total']

            if(len(self.listReviewId) < int(totalRating)):
                offset = 0
                while offset < totalRating:
                    offsetApi = ecweb_constant.API_SHOPEE.format(itemId, offset, shopId)
                    listPageAPI.append(offsetApi)
                    offset = offset + 50
            else:
                print('shopee: nothing to update')

        except Exception as e:
            print(e)
        return listPageAPI

    def start_requests(self):
        for api in self.start_urls:
            yield scrapy.Request(api, headers=self.header)

    def parse(self, response):
        try:
            data = json.loads(response.body)
            reviews = data['data']['ratings']
            for data_review in reviews:
                review = {}
                review['id_product'] = self.product['id_product']
                review['product_info'] = data_review['product_items'][0]['model_name'] if data_review['product_items'] != [] else ""
                review['rating_star'] = data_review['rating_star']
                review['review_title'] = ""
                review['review_content'] = data_review['comment'] if data_review['comment'] != None else ""
                review['buyer_id'] = data_review['userid']
                review['buyer_name'] = data_review['author_username']
                review['review_create_date'] = self.convertDatetime(date=data_review['ctime'])
                review['agree_count'] = data_review['like_count'] if data_review['like_count'] != None else 0
                review['source_id'] = str(data_review['cmtid'])

                if review['source_id'] in self.listReviewId:
                    print('review exists')
                    continue
                else:
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
                    repository.updateModifyProduct(self.product['id_product'])
                print('done shopee')
        except BaseException as e:
            print(e)
            exit()


from scrapyscript import Job, Processor
# if __name__ == '__main__':
def startProcess(product):
    processor = Processor(settings=None)
    job = Job(UpdateProductShopee, product=product)
    processor.run(job)