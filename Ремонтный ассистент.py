import datetime
import sys
from peewee import *
 
db = SqliteDatabase('matherials.db')
class BaseModel(Model):
    class Meta:
        database = db

############ Описание модели

class User(BaseModel):
    user_id = AutoField()
    name = CharField()
    login = CharField()
    
    class Meta:
        db = db

class Store(BaseModel):
    store_id = AutoField()
    name = CharField()
    address = TextField()
        
    class Meta:
        db = db
        
class Category(BaseModel):
    category_id = AutoField()
    category_name = TextField()
        
    class Meta:
        db = db
    
class Characheristic(BaseModel):
    characheristic_id = AutoField()
    characheristic_name = TextField()
        
    class Meta:
        db = db
    
class Category_char(BaseModel):
    characheristic_id = ForeignKeyField(Characheristic)
    category_id = ForeignKeyField(Category)
    
    class Meta:
        db = db
        primary_key = CompositeKey('characheristic_id', 'category_id')
        
class Product(BaseModel):
    prod_id = DecimalField(primary_key=True) #артикул
    name = CharField()
    category_id = ForeignKeyField(Category)
    
    class Meta:
        db = db
        
class Product_char(BaseModel):
    prod_id = ForeignKeyField(Product)
    characheristic_id = ForeignKeyField(Characheristic)
    value = TextField()
    
    class Meta:
        db = db
        primary_key = CompositeKey('prod_id', 'characheristic_id')
        
class Prod_store(BaseModel):
    prod_id = ForeignKeyField(Product)
    store_id = ForeignKeyField(Store)
    price = DecimalField()
    available = DecimalField()
    
    class Meta:
        db = db
        primary_key = CompositeKey('prod_id', 'store_id')

class Product_list(BaseModel):
    product_list_id = AutoField()
    store_id = ForeignKeyField(Store)
    user_id = ForeignKeyField(User)
    total_sum = DecimalField()
    create_date = DateTimeField(default=datetime.datetime.now)
    archive_date = DateTimeField(null = True)
    export = BooleanField()
    
    class Meta:
        db = db
        
class Product_in_list(BaseModel):
    product_list_id = ForeignKeyField(Product_list)
    prod_id = ForeignKeyField(Product)
    
    class Meta:
        db = db
        primary_key = CompositeKey('product_list_id', 'prod_id')
    
class Notification(BaseModel):
    notification_id = AutoField()
    user = ForeignKeyField(User)
    notify_type = TextField()
    text = TextField()
    
    class Meta:
        db = db
        
class Compare_list(BaseModel):
    compare_list_id = AutoField()
    category_id = ForeignKeyField(Category)
    
    class Meta:
        db = db
        
class Product_compare(BaseModel):
    compare_list_id = ForeignKeyField(Compare_list)
    prod_id = ForeignKeyField(Product)
    
    class Meta:
        db = db
        primary_key = CompositeKey('compare_list_id', 'prod_id')
    
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
    category = Category.select(Category.category_name).where(Category.category_id == product.category)
    print("Категория: " + category)
    price = Prod_store.select(fn.MIN(Prod_store.price)).where(Prod_store.prod_id == product.prod_id)
    print("Цена: " + price)
    store_id = Prod_store.get((Prod_store.price == price) & (Prod_store.prod_id == product.prod_id)).store_id
    store = Store.select(Store.name).where(Store.store_id == store_id)
    print(store)

def show_full_product(product):
    show_product(product)
    specs = Characheristic.select().where(Characheristic.characheristic_id == (Product_char.select().where(Product_char.prod_id == product.prod_id).characheristic_id))
    for spec in specs:
        print(spec.characheristic_name + ": ")
        value = Product_char.select().where((Product_char.prod_id == product.prod_id) & (Product_char.characheristic_id == spec.characheristic_id))[0].value
        print(value)
        
# подаётся: запрос с названием товара, наибольшая желаемая цена, дальше список id характеристик, по которым есть фильтр, и дальше лист листов со значениями характеристик
def find_product(searchfield, price, spec_ids_list, spec_list):
    searchfield_result = Product.select(Product.prod_id).where(Product.name == searchfield)
    price_result = Prod_store.select(Prod_store.prod_id).where((Prod_store.prod_id in searchfield_result) & (Prod_store.price <= price))
    final_prod_ids = []
    if spec_ids_list:
        for x in range(len(spec_ids_list)):
            final_prod_ids.extend(Product_char.select(Product_char.prod_id).where((Product_char.prod_id in price_result) & (Product_char.characheristic_id == x) & (Product_char.value in spec_list[x])))
    final_prod_ids = set(final_prod_ids)
    for prod in final_prod_ids:
        product = Product.select().where(Product.prod_id == prod)[0]
        show_product(product)

def add_product(user_id, product_id, store_id):
    list_exist = Product_list.select().where((Product_list.store_id == store_id) & (Product_list.user_id == user_id))[0]
    price = Prod_store.select(Prod_store.price).where((Prod_store.prod_id == product_id) & (Prod_store.store_id == store_id))
    if not list_exist or list_exist == 0:
        prod_list = Product_list.create(
            user_id = user_id,
            store_id = store_id,
            total_sum = price,
            archive_date = None,
            export = False
        )
        Product_in_list.create(
            product_list_id = prod_list.product_list_id,
            prod_id = product_id
        )
    else:
        new_total_sum = list_exist.total_sum + price
        Product_list.update({Product_list.total_sum: new_total_sum}).where((Product_list.store_id == store_id) & (Product_list.user_id == user_id))
        Product_in_list.create(
            product_list_id = list_exist.product_list_id,
            prod_id = product_id
        )
        
def compare_full(product_list):
    prod_ids = Product_in_list.select(Product_in_list.prod_id).where(Product_in_list.product_list_id == product_list.product_list_id)
    for item in prod_ids:
        name = Product.select(Product.name).where(Product.prod_id == item)
        print(name)
    print('###')
    for item in prod_ids:
        price = Prod_store.select(fn.MIN(Prod_store.price)).where(Prod_store.prod_id == item)
        print(price)
    print('###')
    for item in prod_ids:
        chars = Product_char.select().where(Product_char.prod_id == item)
        for char_id in chars.characheristic_id:
            char_name = Characheristic.select(Characheristic.characheristic_name).where(Characheristic.characheristic_id == char_id)
            print(char_name + ": " + Product_char.select(value).where((Product_char.prod_id == item) & (Product_char.characheristic_id == char_ids)))
    
def compare(product_list):
    prod_ids = Product_in_list.select(Product_in_list.prod_id).where(Product_in_list.product_list_id == product_list.product_list_id)
    for item in prod_ids:
        name = Product.select(Product.name).where(Product.prod_id == item)
        print(name)
    print('###')
    for item in prod_ids:
        price = Prod_store.select(fn.MIN(Prod_store.price)).where(Prod_store.prod_id == item)
        print(price)
    print('###')
    char_ids = Product_char.select(Product_char.characheristic_id).where(Product_char.prod_id == item)
    for char_id in char_ids:
        sample_value = Product_char.select(Product_char.value).where(Product_char.prod_id == prod_ids[0] & Product_char.characheristic_id == char_id)
        change = False
        for item in prod_ids:
            value = Product_char.select(Product_char.value).where(Product_char.prod_id == item & Product_char.characheristic_id == char_id)
            if value != sample_value:
                break
        if change:
            char_name = Characheristic.select(Characheristic.characheristic_name).where(Characheristic.characheristic_id == char_id)
            print(char_name + ": ")
            for item in prod_ids:
                value = Product_char.select(Product_char.value).where(Product_char.prod_id == item & Product_char.characheristic_id == char_id)
                prod_name = Product.select(Product.name).where(Product.prod_id == item)
                print(prod_name + ": " + value)
                
def add_to_compare(prod_id):
    product = Product.select().where(Product.prod_id == prod_id)[0]
    list_exist = Compare_list.select().where(Compare_list.category_id == product.category_id)[0]
    if not list_exist or list_exist == 0:
        compare_list = Compare_list.create(
            category_id = product.category_id
        )
        Product_compare.create(
            compare_list_id = compare_list.compare_list_id,
            prod_id = prod_id
        )
    else:
        Product_compare.create(
            compare_list_id = list_exist.compare_list_id,
            prod_id = prod_id
        )

def update_shops():
    update = Prod_store.update({Prod_store.available: 1}).where((Prod_store.prod_id == 2) & (Prod_store.store_id == 1))
    #верхнее работает, если создать таблицу с примерами, а пока:
    update = True
    if update:
        product_list_ids = Product_in_list.select(Product_in_list.product_list_id).where(Product_in_list.prod_id == 2)                                              
        for list_id in product_list_ids:
            user_id = Product_list.select(Product_list.user).where(Product_list.product_list_id == list_id)
            Notification.create(
                user = user_id,
                notify_type = 'mail',
                text = Product.select(Product.name).where(Product.prod_id == 2) + ' появился в наличии в магазине ' + Store.select(Store.name).where(Store.store_id == 1)
            )

############ Пример для тестирования
db.connect()
db.create_tables([
    User, Store, Category, Characheristic, Category_char, Product, Product_char, Prod_store,
    Product_list, Product_in_list, Notification, Compare_list, Product_compare
])
new_user = create_new_user('veram', 'Vera')

############ Реализация шагов

### Сценарий 1.1
# Запросили плитку по цене меньше 1000 за кв.м, любого цвета, прочность выше 6 (из 10), легкость обращения выше 6 (из 10)
find_product("кафель", 1000, [1, 2], [[7, 8, 9, 10], [7, 8, 9, 10]])

### Сценарий 2.1
# Добавляем в списки обои из Максидома и ламинат из Леруа, характеристики: любой цвет, любой материал, любая страна
find_product("обои", sys.maxsize, [], [])
add_product(1, 5, 1)
find_product("ламинат", sys.maxsize, [], [])
add_product(1, 4, 0)

### Сценарий 3.2
update_shops()

### Сценарий 4.1
# Сравниваем 3 душевых кабины, их характеристики: тип стекла, ограждение, форма, высота поддона, конструкция дверей

find_product("душевая кабина", sys.maxsize, [], [])
add_to_compare(7)
add_to_compare(8)
add_to_compare(9)
compare_list_id = Compare_list.select(Compare_list.compare_list_id).where(Compare_list.category_id == 3)
compare(Compare_list.select().where(Compare_list.compare_list_id == compare_list_id)[0])

### Здесь использованы значения:
#Категории товаров: 0 - кафель, 1 - обои, 2 - ламинат, 3 - душевая кабина
#Магазины: 0 - Леруа мерлен, 1 - Максидом


