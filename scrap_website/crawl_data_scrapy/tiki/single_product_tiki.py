import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))))

from database import repository
from constant import ecweb_constant
import scrapy
from scrapy.crawler import CrawlerProcess
import requests
from bs4 import BeautifulSoup
import json
import datetime, time


class SingleProductTikiSpider(scrapy.Spider):
    name = 'single-product-tiki'
    bfUrl = ""
    id_product = None

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

    def get_API_by_itemId_shopId_and_totalReview(self, urlProduct):
        listPageAPI = []

        try:
            tmp = urlProduct[None:urlProduct.find('.html?')]
            itemId = tmp[tmp.rfind('-p') + 2 : None]
            shopId = urlProduct[urlProduct.find('spid=') + 5 : urlProduct.find('&')]

            api = ecweb_constant.API_TIKI.format(1, shopId, itemId)

            session = requests.Session()
            response = session.get(api, headers=self.header)
            response_data = response.json()
            totalPage = response_data['paging']['last_page']
            totalRating = response_data['rating_average']

            p_d_api = f'https://tiki.vn/api/v2/products/{itemId}?spid={shopId}'
            session = requests.Session()
            p_d_response = session.get(p_d_api, headers=self.header)
            p_d_data = p_d_response.json()

            product = {}
            product['name'] = p_d_data['name']
            product['product_url'] = self.bfUrl
            product['product_img'] = p_d_data['thumbnail_url']
            product['shop_id'] = shopId
            product['total_rating'] = str(round(float(totalRating), 1))
            product['source_id'] = itemId
            product['source'] = 'tiki'

            self.id_product = repository.saveProduct(product)
            

            for page in range(1, totalPage+1):
                pageApi = ecweb_constant.API_TIKI.format(page, shopId, itemId)
                listPageAPI.append(pageApi)

        except Exception as e:
            print(e)

        return listPageAPI

    def convertDatetime(self, date):
        return datetime.datetime.fromtimestamp(date)

    def __init__(self, urlProduct=None, *args, **kwargs):
        super(SingleProductTikiSpider, self).__init__(*args, **kwargs)
        self.bfUrl = urlProduct
        self.start_urls = self.get_API_by_itemId_shopId_and_totalReview(urlProduct)

    def start_requests(self):
        #tiki
        for api in self.start_urls:
            yield scrapy.Request(api, headers=self.header)
            # time.sleep(0.2)

    def parse(self, response):
        #tiki
        try:
            data = json.loads(response.body)
            reviews = data['data']
            for data_review in reviews:
                review = {}

                review['id_product'] = self.id_product
                review['product_info'] = data_review['product_attributes'][0] if len(data_review['product_attributes'])>0 else ""
                review['rating_star'] = data_review['rating']
                review['review_title'] = data_review['title'] if data_review['title'] != None else ""
                review['review_content'] = data_review['content'] if data_review['content'] != None else ""
                review['buyer_id'] = data_review['created_by']['id']
                review['buyer_name'] = data_review['created_by']['full_name']
                review['review_create_date'] = self.convertDatetime(date=data_review['created_at'])
                review['agree_count'] = data_review['thank_count'] if data_review['thank_count'] != None else 0
                review['source_id'] = data_review['id']

                # print(review['product_info'])

                list_media = []
                images = data_review['images']
                if images != None:
                    for image in images:
                        media = {}
                        media['type'] = 'image'
                        media['url_media'] = image['full_path']
                        list_media.append(media)

                repository.saveReview(review, list_media)

        except Exception as e:
            print(e)
            exit()



from scrapyscript import Job, Processor
# if __name__ == '__main__':
def startProcess(urlProduct):
    processor = Processor(settings=None)
    job = Job(SingleProductTikiSpider, urlProduct=urlProduct)
    processor.run(job)