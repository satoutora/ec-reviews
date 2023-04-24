import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

import mysql.connector as mysql
from constant import database_constant

# Open database connection
db = mysql.connect(host=database_constant.LOCALHOST,
                   port=database_constant.PORT,
                   user=database_constant.USER,
                   password=database_constant.PASSWORD)
# prepare a cursor object using cursor() method
cursor = db.cursor()

try:
    cursor.execute("USE {}".format(database_constant.DATABASE))
except mysql.Error as e:
    cursor.execute("CREATE DATABASE {}".format(database_constant.DATABASE))
    db.database = database_constant.DATABASE

def createTableProduct():
    create_table_product = """CREATE TABLE IF NOT EXISTS `product` (
                            `id_product` int auto_increment primary key,
                            `product_name` varchar(1000), 
                            `product_url` varchar(1000) not null,
                            `product_img` varchar(255) not null,
                            `shop_id` varchar(45),
                            `total_rating` varchar(45),
                            `source_id` varchar(255),
                            `source` varchar(45) not null,
                            `modified` datetime
                            )"""
    cursor.execute(create_table_product)
    db.commit()
    print('created table product')

def createTableReview():
    create_table_review = """CREATE TABLE IF NOT EXISTS `review` (
                        `id_review` int auto_increment primary key,
                        `id_product` varchar(45) not null,
                        `product_info` varchar(255),
                        `rating_star` varchar(10),
                        `review_title` varchar(1000),
                        `review_content` varchar(5000),
                        `buyer_id` varchar(255) not null,
                        `buyer_name` varchar(255),
                        `review_create_date` datetime,
                        `agree_count` int,
                        `source_id` varchar(45) not null
                        )"""
    cursor.execute(create_table_review)
    db.commit()
    print('created table review')

def createTableMedia():
    create_table_media = """CREATE TABLE IF NOT EXISTS `media` (
                        `id_media` int auto_increment primary key,
                        `type` varchar(45) not null, 
                        `url_media` varchar(255) not null,
                        `id_review` int not null
                        )"""
    cursor.execute(create_table_media)
    db.commit()
    print('created table media')

def createTableGroup():
    create_table_group = """ CREATE TABLE IF NOT EXISTS `group` (
                        `id_group` int auto_increment primary key,
                        `group_name` varchar(5000),
                        `create` datetime,
                        `modified` datetime
                        ) """
    cursor.execute(create_table_group)
    db.commit()
    print('created table group')

def createTableGroupMapProduct():
    create_table_group_map_product = """ CREATE TABLE IF NOT EXISTS `group_map_product` (
                                    `id_group_map_product` int auto_increment primary key,
                                    `id_group` int not null,
                                    `id_product` int not null
                                    ) """
    cursor.execute(create_table_group_map_product)
    db.commit()
    print('created table group_map_product')


def reloadDb():
    global db
    global cursor
    cursor.close()
    db.close()
    db = mysql.connect(host=database_constant.LOCALHOST,
                       port=database_constant.PORT,
                       user=database_constant.USER,
                       password=database_constant.PASSWORD,
                       database=database_constant.DATABASE)
    cursor = db.cursor()
    return db

try:
    createTableProduct()
    createTableReview()
    createTableMedia()
    createTableGroup()
    createTableGroupMapProduct()
except BaseException as e:
    print(e)
