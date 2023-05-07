import sys, os

sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

from database.mysql_connector import cursor, db, reloadDb
from datetime import datetime


def saveProduct(product):
    insert_product = """INSERT INTO `product` (
                        product_name, product_url, product_img, 
                        shop_id, total_rating, source_id, source, modified)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
    cursor.execute(
        insert_product,
        (product['name'], product['product_url'], product['product_img'],
         product['shop_id'], product['total_rating'], product['source_id'],
         product['source'], datetime.now() ))
    db.commit()

    print("product saved " + str(cursor.lastrowid))
    return cursor.lastrowid

def updateModifyProduct(id_product):
    update_product = f"UPDATE `product` SET `modified` = '{datetime.now()}' WHERE id_product = {id_product} ;"
    cursor.execute(update_product)
    db.commit()

def saveMedia(media, id_review):
    insert_media = """ INSERT INTO `media` (type, url_media, id_review) 
                        VALUES (%s, %s, %s)"""
    cursor.execute(insert_media,
                   (media['type'], media['url_media'], id_review))
    db.commit()

    print("media saved " + media['type'] + ": " + str(cursor.lastrowid))

def saveReview(review, list_media):
    insert_review = """ INSERT INTO `review` (
        id_product, product_info, rating_star, review_title, review_content, 
        buyer_id, buyer_name, review_create_date, agree_count, source_id
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""

    cursor.execute(
        insert_review,
        (review['id_product'], review['product_info'], review['rating_star'],
         review['review_title'], review['review_content'], review['buyer_id'],
         review['buyer_name'], review['review_create_date'],
         review['agree_count'], review['source_id']))
    db.commit()
    id_review = cursor.lastrowid

    print("review saved " + str(id_review))
    for media in list_media:
        saveMedia(media, id_review)

def getAllProductBySource(ec):
    s = "SELECT * FROM `product` WHERE `source` = '" + ec + "' order by `id_product` desc;"
    cursor.execute(s)
    data = cursor.fetchall()
    list_product = []
    for row in data:
        product = {}
        product['id_product'] = row[0]
        product['name'] = row[1]
        product['product_url'] = row[2]
        product['product_img'] = row[3]
        product['shop_id'] = row[4]
        product['total_rating'] = row[5]
        product['source_id'] = row[6]
        product['source'] = row[7]
        list_product.append(product)
    return list_product

def getLimitProductBySource(ec, limit):
    s = f"SELECT * FROM `product` WHERE `source` = '{ec}' order by `id_product` desc limit {limit};"
    cursor.execute(s)
    data = cursor.fetchall()
    list_product = []
    for row in data:
        product = {}
        product['id_product'] = row[0]
        product['name'] = row[1]
        product['product_url'] = row[2]
        product['product_img'] = row[3]
        product['shop_id'] = row[4]
        product['total_rating'] = row[5]
        product['source_id'] = row[6]
        product['source'] = row[7]
        list_product.append(product)
    return list_product

def getAllReviewByProduct(id_product):
    s = "SELECT * FROM `review` WHERE `id_product` = " + str(
        id_product) + " order by `rating_star` desc, `agree_count` desc;"

    cursor.execute(s)
    data = cursor.fetchall()
    list_review = []
    for row in data:
        review = {}
        review['product_info'] = row[2]
        review['rating_star'] = row[3]
        review['review_title'] = row[4]
        review['review_content'] = row[5]
        review['buyer_id'] = row[6]
        review['buyer_name'] = row[7]
        review['review_create_date'] = row[8]
        review['agree_count'] = row[9]
        review['source_id'] = row[10]
        list_review.append(review)
    return list_review

def getAllReviewAndMediaByProduct(id_product):
    select_review = "SELECT * FROM `review` WHERE `id_product` = " + str(
        id_product) + " order by `rating_star` desc, `agree_count` desc;"

    cursor.execute(select_review)
    data = cursor.fetchall()
    list_review = []
    for row in data:
        review = {}
        review['id_review'] = row[0]
        review['product_info'] = row[2]
        review['rating_star'] = row[3]
        review['review_title'] = row[4]
        review['review_content'] = row[5]
        review['buyer_id'] = row[6]
        review['buyer_name'] = row[7]
        review['review_create_date'] = row[8]
        review['agree_count'] = row[9]
        review['source_id'] = row[10]

        select_media = f"SELECT * FROM `media` WHERE `id_review` = {review['id_review']};"
        cursor.execute(select_media)
        media_data = cursor.fetchall()
        list_media = []
        for m in media_data:
            media = {}
            media['id_media'] = m[0]
            media['type'] = m[1]
            media['url_media'] = m[2]
            list_media.append(media)

        list_review.append((review, list_media))
    return list_review

def getProductById(id_product):
    s = "SELECT * FROM `product` WHERE `id_product` = " + str(
        id_product) + " limit 1;"
    cursor.execute(s)
    data = cursor.fetchall()
    if data != []:
        product = {}
        product['id_product'] = data[0][0]
        product['name'] = data[0][1]
        product['product_url'] = data[0][2]
        product['product_img'] = data[0][3]
        product['shop_id'] = data[0][4]
        product['total_rating'] = data[0][5]
        product['source_id'] = data[0][6]
        product['source'] = data[0][7]
        product['modified'] = data[0][8]
        return product
    else:
        return None

def getReviewDateNewest(product):
    s = "SELECT * FROM `review` WHERE `id_product` = " + str(
        product['id_product']) + " order by review_create_date desc limit 1;"
    cursor.execute(s)
    data = cursor.fetchall()
    if data != None:
        return data[0][8]
    else:
        return None

def getProductBySourceIdAndShopId(sourceId, shopId):
    s = "SELECT * FROM `product` WHERE `source_id` = '" + str(
        sourceId) + "' and `shop_id` like '%" + str(shopId) + "%' limit 1;"

    cursor.execute(s)
    data = cursor.fetchall()
    print(data)
    if data != []:
        product = {}
        product['id_product'] = data[0][0]
        product['name'] = data[0][1]
        product['product_url'] = data[0][2]
        product['product_img'] = data[0][3]
        product['shop_id'] = data[0][4]
        product['total_rating'] = data[0][5]
        product['source_id'] = data[0][6]
        product['source'] = data[0][7]
        return product
    else:
        return None

def saveGroup(group_name):
    print(group_name)
    insert_group = """INSERT INTO `group` (
                        `group_name`, `create`, `modified`)
                        VALUES (%s, %s, %s)"""
    cursor.execute(insert_group,
                   (group_name, datetime.now(), datetime.now()))
    db.commit()
    print("group saved " + str(group_name) + " " + str(cursor.lastrowid))

def getAllGroup():
    s = "SELECT * FROM `group` order by `id_group` desc;"
    cursor.execute(s)
    data = cursor.fetchall()
    list_group = []
    for row in data:
        group = {}
        group['id_group'] = row[0]
        group['group_name'] = row[1]
        group['create'] = row[2]
        group['modified'] = row[3]
        list_group.append(group)
    return list_group

def getGroupById(id_group):
    s = "SELECT * FROM `group` WHERE `id_group` = " + str(id_group) + " limit 1;"
    cursor.execute(s)
    data = cursor.fetchall()
    if data != []:
        group = {}
        group['id_group'] = data[0][0]
        group['group_name'] = data[0][1]
        group['create'] = data[0][2]
        group['modified'] = data[0][3]
        return group
    else:
        return None

def deleteGroup(id_group):
    delete_group_map_product = f"DELETE FROM `group_map_product` WHERE id_group = {id_group} ;"
    cursor.execute(delete_group_map_product)
    db.commit()
    delete_group = f"DELETE FROM `group` WHERE id_group = {id_group} ;"
    cursor.execute(delete_group)
    db.commit()

def updateGroup(id_group, group_name):
    if group_name != "":
        update_group = f"UPDATE `group` SET group_name = '{group_name}', modified = '{datetime.now()}' WHERE id_group = {id_group} ;"
        cursor.execute(update_group)
        db.commit()
    else:
        update_group = f"UPDATE `group` SET modified = '{datetime.now()}' WHERE id_group = {id_group} ;"
        cursor.execute(update_group)
        db.commit()

def saveGroupMapProduct(id_group, id_product):
    insert_group_map_product = """INSERT INTO `group_map_product` (`id_group`, `id_product`)
                        VALUES (%s, %s)"""
    cursor.execute(insert_group_map_product,
                   (id_group, id_product))
    db.commit()
    print("group map product saved " + str(id_group) + " " + str(id_product))

def getAllIdProductInGroup(id_group):
    s = f"SELECT * FROM `group_map_product` WHERE `id_group` = {id_group} ;"
    cursor.execute(s)
    data = cursor.fetchall()
    list_id_product = []
    for row in data:
        list_id_product.append(row[2])
    return list_id_product

def deleteGroupMapProduct(id_group, id_product):
    delete_group_map_product = f"DELETE FROM `group_map_product` WHERE id_group = {id_group} AND id_product = {id_product} ;"
    cursor.execute(delete_group_map_product)
    db.commit()

def getAllProductByGroup(id_group):
    list_id_product = getAllIdProductInGroup(id_group)
    list_shopee = []
    list_lazada = []
    list_tiki = []
    for id_product in list_id_product:
        product = getProductById(id_product)
        if product['source'] == 'shopee':
            list_shopee.append(product)
        elif product['source'] == 'lazada':
            list_lazada.append(product)
        elif product['source'] == 'tiki':
            list_tiki.append(product)
    list_product = {
        'list_shopee' : list_shopee,
        'list_lazada' : list_lazada,
        'list_tiki' : list_tiki
    }
    return list_product

def getAllReviewByFilter(id_product, have_content, not_have_content, have_media, not_have_media, option_sort, list_star):
    s = f"select * from `review` where ( `id_product` = {id_product} ) and (`review_content` != {have_content} or `review_content` = {not_have_content}) and (`rating_star` in {list_star}) {option_sort} ;"
    print(s)
    cursor.execute(s)
    data = cursor.fetchall()

    list_review = []
    for row in data:
        review = {}
        review['id_review'] = row[0]
        review['product_info'] = row[2]
        review['rating_star'] = row[3]
        review['review_title'] = row[4]
        review['review_content'] = row[5]
        review['buyer_id'] = row[6]
        review['buyer_name'] = row[7]
        review['review_create_date'] = row[8]
        review['agree_count'] = row[9]
        review['source_id'] = row[10]

        list_media = []
        select_media = f"SELECT * FROM `media` WHERE `id_review` = {review['id_review']};"
        cursor.execute(select_media)
        media_data = cursor.fetchall()
        for m in media_data:
            media = {}
            media['id_media'] = m[0]
            media['type'] = m[1]
            media['url_media'] = m[2]
            list_media.append(media)

        if have_media == 1:
            if list_media != []:
                list_review.append((review, list_media))

        if not_have_media == 1:
            if list_media == []:
                list_review.append((review, list_media))

    return list_review

def reloadRepository():
    global db, cursor
    db = reloadDb()
    cursor = db.cursor()
