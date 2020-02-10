#!/usr/bin/env python
# coding: utf-8

# In[16]:


import datetime
import sys
from peewee import *
 
db = SqliteDatabase('matherials.db')
class BaseModel(Model):
    class Meta:
        db = db
 
db.connect()
#db.create_tables([
#    Product, User, Store
#])

############ Описание модели

class User(Model):
    user_id = DecimalField(primary_key=True)
    name = CharField()
    login = CharField()
    
    class Meta:
        db = db

class Store(BaseModel):
    store_id = DecimalField(primary_key=True)
    name = CharField()
    address = TextField()
        
    class Meta:
        db = db
        
class Product(BaseModel):
    prod_id = DecimalField(primary_key=True) #артикул
    name = CharField()
    category = DecimalField()
    price = [DecimalField()]
    store = [ForeignKeyField(Store)]
    specifications = [[DecimalField()]]
    
    class Meta:
        db = db

class Product_list(BaseModel):
    product_list_id = DecimalField(primary_key=True)
    user = ForeignKeyField(User)
    product = [ForeignKeyField(Product)]
    store = ForeignKeyField(Store)
    total_sum = DecimalField
    create_date = DateTimeField(default=datetime.datetime.now)
    archive_date = DateTimeField()
    export = BooleanField()
    
    class Meta:
        db = db
# Удалить ?
#class Search_list(BaseModel):
#    search_list_id = DecimalField(primary_key=True)
#    category = TextField()
#    minprice = DecimalField()
#    specifications = [TextField()]
#    
#    class Meta:
#        db = db
    
class Notification(BaseModel):
    notification_id = DecimalField(primary_key=True)
    user = ForeignKeyField(User)
    notify_type = TextField()
    text = TextField()
    
    class Meta:
        db = db
        
class Compare_list(BaseModel):
    compare_list_id = DecimalField(primary_key=True)
    category = DecimalField()
    products = [ForeignKeyField(Product)]
    
    class Meta:
        db = db
    
############ Функции (операции)
    
def create_new_user(new_login, new_name):
    User.create(
        name = new_name,
        login = new_login        
    )
        
def change_login(user, new_login):
    user.login = new_login
    user.save()
    
def show_product(product):
    print(product.name)
    print(product.category)
    price = min(product.price)
    print(price)
    index = product.store.index(price)
    print(product.store[index])

def show_full_product(product):
    show_product(product)
    for spec in product.specifications:
        print(spec)

# spec_list - список списков, напр [[0], [6, 7]] каждый внутренний список - характеристика, число - значение
def find_product(searchfield, price, spec_list):
    search_result = Product.select().where(Product.name=searchfield, Product.price<=price, Product.specifications = spec_list).groupBy(Product.store)
    for product in search_result:
        show(product)

def add_product(user_id, product_id, store_id):
    list_exist = Product_list.select().where(Product.store=store_id)
    price = Product.select().where(Product.prod_id=product_id).price[index]
    if not list_exist or list_exist == 0:
        Product_list.create(
            user = user_id,
            product = [product_id],
            store = store_id,
            total_sum = price,
            create_date = DateTimeField(datetime.datetime.now),
            archive_date = None,
            export = False
        )
    else:
        index = product.store.index(store_id)
        new_total_sum = list_exist.total_sum + price
        Product_list.update(Product_list.product.append(product_id), Product_list.total_sum=new_total_sum).where(Product_list.store=store_id)

def compare_full(product_list):
    for item in product_list:
        print(item.name)
    print('###')
    for item in product_list:
        price = min(item.price)
        print(price)
    print('###')
    for x in range(len(product_list[0].specifications)):
        for item in product_list:
            print(item.specifications[x])
        print('###')
        
def compare(product_list):
    for item in product_list:
        print(item.name)
    print('###')
    for item in product_list:
        price = min(item.price)
        print(price)
    print('###')
    for x in range(len(product_list[0].specifications)):
        change = False
        spec = product_list[0].specifications[x]
        for item in product_list:
            if spec in item.specifications:
                pass
            else:
                change = True
                break
        if change:
            for item in product_list:
                print(item.specifications[x])
            print('###')

def add_to_compare(prod_id):
    product = Product.select().where(prod_id=prod_id)
    list_exist = Compare_list.select().where(Compare_list.category=product.category)
    if not list_exist or list_exist == 0:
        Compare_list.create(
            category=product.category,
            products=[prod_id]
        )
    else:
        Compare_list.update({Compare_list.products.append(prod_id)}.where(Compare_list.category=product.category))

############ Пример для тестирования
new_user = create_new_user('veram', 'Vera') # для работы указать дб
new_user.save()

############ Реализация шагов

### Сценарий 1.1
# Запросили плитку по цене меньше 1000 за кв.м, любого цвета, прочность выше 6 (из 10), легкость обращения выше 6 (из 10)
find_product("кафель", 1000, [not None, [7, 8, 9, 10], [7, 8, 9, 10]])

### Сценарий 2.1
# Добавляем в списки обои из Максидома и ламинат из Леруа, характеристики: любой цвет, любой материал, любая страна
find_product("обои", sys.maxsize, [not None, not None, not None])
add_product(1, 5, 1)
find_product("ламинат", sys.maxsize, [not None, not None, not None])
add_product(1, 4, 0)

### Сценарий 4.1
# Сравниваем 3 душевых кабины, их характеристики: тип стекла, ограждение, форма, высота поддона, конструкция дверей

### !!!!!!!!!!!! Пока проблема с обработкой = IS NOT NULL в запросе where
find_product("душевая кабина", sys.maxsize, [not None, not None, not None, not None, not None])
add_to_compare(7)
add_to_compare(8)
add_to_compare(9)
compare(Compare_list.select(Compare_list.products).where(Compare_list.category=3))

### Здесь использованы значения:
#Категории товаров: 0 - кафель, 1 - обои, 2 - ламинат, 3 - душевая кабина
#Магазины: 0 - Леруа мерлен, 1 - Максидом



