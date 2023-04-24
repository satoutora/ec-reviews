import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

from flask import Flask, redirect, url_for, render_template, request, flash
from flask_paginate import Pagination, get_page_args

from crawl_data_scrapy.lazada import single_product_lazada, simple_request_lazada, update_product_lazada
from crawl_data_scrapy.shopee import single_product_shopee, update_product_shopee
from crawl_data_scrapy.tiki import single_product_tiki, update_product_tiki
from scrapyscript import Job, Processor
from threading import Thread
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from database import repository
import time, json
from scrapy.crawler import CrawlerProcess

app = Flask(__name__)




def getPageReview(list_review, offset=0, per_page=10):
    return list_review[offset:offset + per_page]


@app.route("/")
def home():
    list_group = repository.getAllGroup()
    return render_template("index.html",
                            list_group=list_group)


@app.route("/add-new-group", methods=['POST', 'GET'])
def addNewGroup():
    if request.method == 'POST':
        group_name = str(request.form['group']).strip()
        if len(group_name) == 0:
            flash('Group name can not empty', category='error')
        else:
            repository.saveGroup(group_name)
    return redirect(url_for('home'))


@app.route("/group/<int:id_group>")
def group(id_group):
    group = repository.getGroupById(id_group)

    list_product_in_group = repository.getAllProductByGroup(id_group)
    list_shopee = list_product_in_group['list_shopee']
    list_lazada = list_product_in_group['list_lazada']
    list_tiki = list_product_in_group['list_tiki']

    return render_template("group.html",
                           group=group,
                           list_shopee=list_shopee,
                           list_lazada=list_lazada,
                           list_tiki=list_tiki)


@app.route("/group/edit-group/<int:id_group>", methods=['POST', 'GET'])
def editGroup(id_group):
    group = repository.getGroupById(id_group)

    if request.method == 'POST':
        group_name = str(request.form.get('group_name')).strip()
        list_remove_id = json.loads(request.form.get('list_remove'))
        # print(list_remove_id)
        if list_remove_id != None:
            for remove_id in list_remove_id:
                repository.deleteGroupMapProduct(id_group, remove_id)
        if group['group_name'] != group_name:
            repository.updateGroup(id_group, group_name)

        return url_for('group', id_group=id_group)

    list_product_in_group = repository.getAllProductByGroup(id_group)
    list_shopee = list_product_in_group['list_shopee']
    list_lazada = list_product_in_group['list_lazada']
    list_tiki = list_product_in_group['list_tiki']

    return render_template("edit_group.html",
                           group=group,
                           list_shopee=list_shopee,
                           list_lazada=list_lazada,
                           list_tiki=list_tiki)


@app.route("/group/delete/<int:id_group>")
def deleteGroup(id_group):
    repository.deleteGroup(id_group)
    return redirect(url_for('home'))


@app.route("/group/<int:id_group>/view-all-reviews", methods=['POST', 'GET'])
def getAllReview(id_group):
    group = repository.getGroupById(id_group)

    list_product = []
    list_product_in_group = repository.getAllProductByGroup(id_group)

    list_product += list_product_in_group['list_shopee']
    list_product += list_product_in_group['list_lazada']
    list_product += list_product_in_group['list_tiki']

    for product in list_product:
        list_review = repository.getAllReviewAndMediaByProduct(product['id_product'])
        product['list_review'] = list_review

        product['checked'] = 'checked'
    source_list_product = list_product
    check_have_content = check_not_have_content = check_have_media = check_not_have_media = 'checked'
    check_1s = check_2s = check_3s = check_4s = check_5s = 'checked'

    if request.method == 'POST':
        try:
            list_id_product = request.form.getlist('product')
            have_content = "''" if request.form.get('have_content') == '1' else "null"
            not_have_content = "''" if request.form.get('not_have_content') == '1' else "null"
            have_media = 1 if request.form.get('have_media') == '1' else 0
            not_have_media = 1 if request.form.get('not_have_media') == '1' else 0
            most_liked = "order by agree_count desc"
            rating = request.form.getlist('rating_star')
            list_star = '('
            for st in rating:
                list_star =  list_star + str(st) + ','
            list_star = list_star[:len(list_star)-1] + ')'

            new_list_product = []
            for product in source_list_product:
                if str(product['id_product']) in list_id_product:
                    n_list_review = repository.getAllReviewByFilter(product['id_product'], have_content, not_have_content, have_media, not_have_media, most_liked, list_star)
                    product['list_review'] = n_list_review
                    new_list_product.append(product)
                else:
                    product['checked'] = ''

            if have_content == "null": check_have_content = ''
            if not_have_content == "null": check_not_have_content = ''
            if have_media == 0: check_have_media = ''
            if not_have_media == 0: check_not_have_media = ''
            if '1' not in rating: check_1s = ''
            if '2' not in rating: check_2s = ''
            if '3' not in rating: check_3s = ''
            if '4' not in rating: check_4s = ''
            if '5' not in rating: check_5s = ''

            list_product = new_list_product

        except BaseException as e:
            print(e)


    return render_template('all_review_list.html',
                           group=group,
                           list_product=list_product,
                           source_list_product=source_list_product,
                           check_have_content=check_have_content,
                           check_not_have_content=check_not_have_content,
                           check_have_media=check_have_media,
                           check_not_have_media=check_not_have_media,
                           check_1s=check_1s,
                           check_2s=check_2s,
                           check_3s=check_3s,
                           check_4s=check_4s,
                           check_5s=check_5s)


@app.route("/crawl/<int:id_group>", methods=['POST', 'GET'])
def crawl(id_group):
    if request.method == 'POST':
        try:
            url_product = str(request.form['link']).strip()
            print(url_product)

            list_id_product = set(repository.getAllIdProductInGroup(id_group))

            processor = Processor(settings=None)

            if len(url_product) > 0 and url_product.find('shopee') != -1:
                try:
                    tmp = url_product[url_product.rfind('-i.')+3 : url_product.find('?sp_atk=')]
                    shop_id = tmp.split('.')[0]
                    source_id = tmp.split('.')[1]

                    product = repository.getProductBySourceIdAndShopId(source_id, shop_id)
                    if product != None:
                        if product['id_product'] not in list_id_product:
                            print('add product to group')
                            job = Job(update_product_shopee.UpdateProductShopee, product=product)
                            processor.run(job)
                            repository.saveGroupMapProduct(id_group, product['id_product'])
                            repository.updateGroup(id_group, "")
                        else:
                            print('product exists in group')
                            flash('product exists in group', category='error')
                    else:
                        job = Job(single_product_shopee.SingleProductShopeeSpider, urlProduct=url_product)
                        processor.run(job)
                        repository.reloadRepository()

                        new_product = repository.getProductBySourceIdAndShopId(source_id, shop_id)
                        repository.saveGroupMapProduct(id_group, new_product['id_product'])
                        repository.updateGroup(id_group, "")
                except Exception as e:
                    print(e)
                    flash('Link is error', category='error')

            elif len(url_product) > 0 and url_product.find('tiki') != -1:
                try:
                    tmp = url_product[None:url_product.find('.html?')]
                    source_id = tmp[tmp.rfind('-p') + 2:None]
                    shop_id = url_product[url_product.find('spid=')+5 : url_product.find('&')]

                    product = repository.getProductBySourceIdAndShopId(source_id, shop_id)
                    if product != None:
                        if product['id_product'] not in list_id_product:
                            print('add product to group')
                            th = Thread(
                                target=update_product_tiki.UpdateProductTiki(
                                    product=product).start_requests)
                            th.start()
                            repository.saveGroupMapProduct(id_group, product['id_product'])
                            repository.updateGroup(id_group, "")
                        else:
                            print('product exists in group')
                            flash('product exists in group', category='error')
                    else:
                        job = Job(single_product_tiki.SingleProductTikiSpider, urlProduct=url_product)
                        processor.run(job)
                        repository.reloadRepository()

                        new_product = repository.getProductBySourceIdAndShopId(source_id, shop_id)
                        repository.saveGroupMapProduct(id_group, new_product['id_product'])
                        repository.updateGroup(id_group, "")
                except Exception as e:
                    print(e)
                    flash('Link is error. Please try again', category='error')

            elif len(url_product) > 0 and url_product.find('lazada') != -1:
                try:
                    tmp = url_product[url_product.rfind('-i'):url_product.find('.html?')]
                    source_id = tmp[tmp.find('-i') + 2:tmp.find('-s')]
                    shop_id = ''

                    product = repository.getProductBySourceIdAndShopId(source_id, shop_id)
                    print(product)
                    if product != None:
                        if product['id_product'] not in list_id_product:
                            print('add product to group')
                            update_product_lazada.UpdateProductLazada(product=product).start_requests()
                            repository.saveGroupMapProduct(id_group, product['id_product'])
                            repository.updateGroup(id_group, "")
                        else:
                            print('product exists in group')
                            flash('product exists in group', category='error')
                    else:
                        simple_request_lazada.SimpleRequestLazada(urlProduct=url_product).start_requests()
                        new_product = repository.getProductBySourceIdAndShopId(source_id, shop_id)
                        repository.saveGroupMapProduct(id_group, new_product['id_product'])
                        repository.updateGroup(id_group, "")
                except Exception as e:
                    print(e)
                    flash('Link is error. Please try again', category='error')

            else:
                flash('Link is error. Please try again', category='error')

        except Exception as e:
            print(e)
    return redirect(url_for('group', id_group=id_group))


@app.route("/group/<int:id_group>/detail/<int:id_product>",
           methods=['POST', 'GET'])
def detailProduct(id_group, id_product):
    product = repository.getProductById(id_product)
    list_review = repository.getAllReviewAndMediaByProduct(id_product)

    check_have_content = check_not_have_content = check_have_media = check_not_have_media = 'checked'
    check_1s = check_2s = check_3s = check_4s = check_5s = 'checked'

    if request.method == 'POST':
        try:
            have_content = "''" if request.form.get('have_content') == '1' else "null"
            not_have_content = "''" if request.form.get('not_have_content') == '1' else "null"
            have_media = 1 if request.form.get('have_media') == '1' else 0
            not_have_media = 1 if request.form.get('not_have_media') == '1' else 0
            most_liked = "order by agree_count desc"
            rating = request.form.getlist('rating_star')
            list_star = '('
            for st in rating:
                list_star = list_star + str(st) + ','
            list_star = list_star[:len(list_star) - 1] + ')'
            print(have_content, not_have_content, have_media, not_have_media)
            return redirect(
                url_for('detailProductByFilter', id_group=id_group,
                                                id_product=id_product,
                                                have_content=have_content,
                                                not_have_content=not_have_content,
                                                have_media=have_media,
                                                not_have_media=not_have_media,
                                                list_star=list_star))

        except BaseException as e:
            print(e)

    total_review = len(list_review)
    page, per_page, offset = get_page_args(page_parameter='page', per_page_parameter='per_page')
    page_review = getPageReview(list_review=list_review, offset=offset, per_page=per_page)
    pagination = Pagination(page=page, per_page=per_page, total=total_review, css_framework='bootstrap4')

    return render_template("detail_product.html",
                           id_group=id_group,
                           product=product,
                           list_review=list_review,
                           total_review=total_review,
                           page_review=page_review,
                           page=page,
                           per_page=per_page,
                           pagination=pagination,
                           check_have_content=check_have_content,
                           check_not_have_content=check_not_have_content,
                           check_have_media=check_have_media,
                           check_not_have_media=check_not_have_media,
                           check_1s=check_1s,
                           check_2s=check_2s,
                           check_3s=check_3s,
                           check_4s=check_4s,
                           check_5s=check_5s)


@app.route("/group/<int:id_group>/detail/<int:id_product>/filter/<have_content>/<not_have_content>/<int:have_media>/<int:not_have_media>/<list_star>",
    methods=['POST', 'GET'])
def detailProductByFilter(id_group, id_product, have_content, not_have_content, have_media, not_have_media, list_star):
    product = repository.getProductById(id_product)

    most_liked = "order by agree_count desc"

    list_review = repository.getAllReviewByFilter(
                        id_product, have_content, not_have_content,
                        have_media, not_have_media, most_liked, list_star)

    if request.method == 'POST':
        have_content = "''" if request.form.get('have_content') == '1' else "null"
        not_have_content = "''" if request.form.get('not_have_content') == '1' else "null"
        have_media = 1 if request.form.get('have_media') == '1' else 0
        not_have_media = 1 if request.form.get('not_have_media') == '1' else 0
        rating = request.form.getlist('rating_star')
        list_star = '('
        for st in rating:
            list_star = list_star + str(st) + ','
        list_star = list_star[:len(list_star) - 1] + ')'
        print(have_content, not_have_content, have_media, not_have_media)
        return redirect(
            url_for('detailProductByFilter', id_product=id_product,
                                            have_content=have_content,
                                            not_have_content=not_have_content,
                                            have_media=have_media,
                                            not_have_media=not_have_media,
                                            list_star=list_star))

    check_have_content = check_not_have_content = check_have_media = check_not_have_media = 'checked'
    check_1s = check_2s = check_3s = check_4s = check_5s = 'checked'
    if have_content == "null": check_have_content = ''
    if not_have_content == "null": check_not_have_content = ''
    if have_media == 0: check_have_media = ''
    if not_have_media == 0: check_not_have_media = ''
    if '1' not in list_star: check_1s = ''
    if '2' not in list_star: check_2s = ''
    if '3' not in list_star: check_3s = ''
    if '4' not in list_star: check_4s = ''
    if '5' not in list_star: check_5s = ''

    total_review = len(list_review)
    page, per_page, offset = get_page_args(page_parameter='page', per_page_parameter='per_page')
    page_review = getPageReview(list_review=list_review, offset=offset, per_page=per_page)
    pagination = Pagination(page=page, per_page=per_page, total=total_review, css_framework='bootstrap4')

    return render_template("detail_product.html",
                           id_group=id_group,
                           product=product,
                           list_review=list_review,
                           total_review=total_review,
                           page_review=page_review,
                           page=page,
                           per_page=per_page,
                           pagination=pagination,
                           check_have_content=check_have_content,
                           check_not_have_content=check_not_have_content,
                           check_have_media=check_have_media,
                           check_not_have_media=check_not_have_media,
                           check_1s=check_1s,
                           check_2s=check_2s,
                           check_3s=check_3s,
                           check_4s=check_4s,
                           check_5s=check_5s)


def updateAll():
    list_shopee = repository.getAllProductBySource("shopee")
    list_lazada = repository.getAllProductBySource("lazada")
    list_tiki = repository.getAllProductBySource("tiki")
    print(f"schedule is running lazada")
    for lazada_product in list_lazada:
        update_product_lazada.UpdateProductLazada(product=lazada_product).start_requests()
    repository.reloadRepository()
    print(f"schedule is running tiki")
    for tiki_product in list_tiki:
        update_product_tiki.UpdateProductTiki(product=tiki_product).start_requests()
    repository.reloadRepository()
    print(f"schedule is running shopee")
    for shopee_product in list_shopee:
        update_product_shopee.startProcess(shopee_product)
    repository.reloadRepository()


scheduler = BackgroundScheduler()
trigger = CronTrigger(year="*", month="*", day="*", hour="3", minute="0", second="0")
scheduler.add_job(func=updateAll, trigger=trigger)
scheduler.start()


if __name__ == '__main__':
    app.config['SECRET_KEY'] = 'crawler'
    app.run(debug=True, port=8000)
