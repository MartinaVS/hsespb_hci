import datetime
import sys
from peewee import *
from playhouse.reflection import print_table_sql
 
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
    charachteristic_id = AutoField()
    characheristic_name = TextField()
        
    class Meta:
        db = db
    
class Category_char(BaseModel):
    charachteristic_id = ForeignKeyField(Characheristic)
    category_id = ForeignKeyField(Category)
    
    class Meta:
        db = db
        primary_key = CompositeKey('charachteristic_id', 'category_id')
        
class Product(BaseModel):
    prod_id = DecimalField(primary_key=True) #артикул
    name = CharField()
    category_id = ForeignKeyField(Category)
    
    class Meta:
        db = db
        
class Product_char(BaseModel):
    product_char_id = AutoField()
    prod_id = ForeignKeyField(Product)
    charachteristic_id = ForeignKeyField(Characheristic)
    value = TextField()
    
    class Meta:
        db = db
        #primary_key = CompositeKey('prod_id', 'charachteristic_id')
        
class Prod_store(BaseModel):
    prod_id = ForeignKeyField(Product)
    store_id = ForeignKeyField(Store)
    price = DecimalField()
    available = DecimalField()
    
    class Meta:
        db = db
        primary_key = CompositeKey('prod_id', 'store_id')

class Product_list(BaseModel):
    # в Product_list нельзя сделать композитный ключ, потому что на композитный ключ нельзя ссылаться, а product_in_list ссылается
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
    count = DecimalField()
    cost = FloatField()
    availability = BooleanField()
    
    class Meta:
        db = db
        primary_key = CompositeKey('product_list_id', 'prod_id')
    
class Notification(BaseModel):
    notification_id = AutoField()
    user = ForeignKeyField(User)
    notify_type = TextField()
    text = TextField()
    smtp = ForeignKeyField(User)
    
    class Meta:
        db = db
        
class Compare_list(BaseModel):
    compare_list_id = AutoField()
    category_id = ForeignKeyField(Category)
    user_id = ForeignKeyField(User)
                              
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
    category = Category.select(Category.category_name).where(Category.category_id == product.category_id).scalar()
    print("Категория: " + category)
    price = Prod_store.select(fn.MIN(Prod_store.price)).where(Prod_store.prod_id == product.prod_id).scalar()
    print("Цена: " + str(price))
    store_id = Prod_store.get((Prod_store.price == price) & (Prod_store.prod_id == product.prod_id)).store_id
    store = Store.select(Store.name).where(Store.store_id == store_id).scalar()
    print(store)

def show_full_product(product):
    show_product(product)
    specs = Characheristic.select().where(Characheristic.charachteristic_id == (Product_char.select().where(Product_char.prod_id == product.prod_id).charachteristic_id))
    for spec in specs:
        print(spec.characheristic_name + ": ")
        value = Product_char.select().where((Product_char.prod_id == product.prod_id) & (Product_char.charachteristic_id == spec.charachteristic_id))[0].value
        print(value)
        
# подаётся: запрос с названием товара, наибольшая желаемая цена, дальше список id характеристик, по которым есть фильтр, и дальше лист листов со значениями характеристик
def find_product(searchfield, price, spec_ids_list, spec_list):
    searchfield_result = Product.select(Product.prod_id).where(Product.name == searchfield)
    searchfield_result = list(searchfield_result)
    searchfield_result = [int(t.prod_id) for t in searchfield_result]
    price_result = Prod_store.select(Prod_store.prod_id, Prod_store.store_id).where((Prod_store.prod_id << searchfield_result) & (Prod_store.price <= price))
    price_result = list(price_result)
    price_result = [int(t.prod_id.prod_id) for t in price_result]
    final_prod_ids = []
    if spec_ids_list:
        for x in spec_ids_list:
            final_prod_ids.extend(Product_char.select(Product_char.prod_id, Product_char.charachteristic_id).where((Product_char.prod_id << price_result) & (Product_char.charachteristic_id == x) & (Product_char.value << spec_list[x - 2])))
        final_prod_ids = [int(t.prod_id.prod_id) for t in final_prod_ids]
        final_prod_ids = set(final_prod_ids)
        for prod in final_prod_ids:
            product = Product.select().where(Product.prod_id == prod)[0]
            show_product(product)
            print("\n")
    else:
        for prod in price_result:
            product = Product.select().where(Product.prod_id == prod)[0]
            show_product(product)
            print("\n")

def add_product(user_id, product_id, store_id, count):
    list_exist = Product_list.select().where((Product_list.store_id == store_id) & (Product_list.user_id == user_id))
    price = Prod_store.select(Prod_store.price).where((Prod_store.prod_id == product_id) & (Prod_store.store_id == store_id)).scalar()
    available = Prod_store.select(Prod_store.available).where((Prod_store.prod_id == product_id) & (Prod_store.store_id == store_id)).scalar()
    price = price * count
    if available >= count:
        availability = True
    else:
        availability = False
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
            prod_id = product_id,
            count = count,
            cost = price,
            availability = availability
        )
    else:
        new_total_sum = list_exist.total_sum + price
        Product_list.update({Product_list.total_sum: new_total_sum}).where((Product_list.store_id == store_id) & (Product_list.user_id == user_id))
        Product_in_list.create(
            product_list_id = list_exist.product_list_id,
            prod_id = product_id,
            count = count,
            cost = price,
            availability = availability
        )
        
def compare_full(product_list):
    prod_ids = Product_compare.select(Product_compare.compare_list_id, Product_compare.prod_id).where(Product_compare.compare_list_id == product_list.compare_list_id)
    prod_ids = list(prod_ids)
    prod_ids = [int(t.prod_id.prod_id) for t in prod_ids]
    for item in prod_ids:
        name = Product.select(Product.name).where(Product.prod_id == item).scalar()
        print(name)
    print('###')
    for item in prod_ids:
        price = Prod_store.select(fn.MIN(Prod_store.price)).where(Prod_store.prod_id == item).scalar()
        print(price)
    print('###')
    for item in prod_ids:
        chars = Product_char.select(Product_char.charachteristic_id).where(Product_char.prod_id == item)
        chars = list(chars)
        chars = [int(t.charachteristic_id.charachteristic_id) for t in chars]
        for char_id in chars:
            char_name = Characheristic.select(Characheristic.characheristic_name).where(Characheristic.charachteristic_id == char_id).scalar()
            print(char_name + ": " + Product_char.select(Product_char.value).where((Product_char.prod_id == item) & (Product_char.charachteristic_id == char_id)).scalar())
    
def compare(product_list):
    prod_ids = Product_compare.select(Product_compare.compare_list_id, Product_compare.prod_id).where(Product_compare.compare_list_id == product_list.compare_list_id)
    prod_ids = list(prod_ids)
    prod_ids = [int(t.prod_id.prod_id) for t in prod_ids]
    for item in prod_ids:
        name = Product.select(Product.name).where(Product.prod_id == item).scalar()
        print(name)
    print('###')
    for item in prod_ids:
        price = Prod_store.select(fn.MIN(Prod_store.price)).where(Prod_store.prod_id == item).scalar()
        print(price)
    print('###')
    char_ids = Product_char.select(Product_char.prod_id, Product_char.charachteristic_id).where(Product_char.prod_id == item)
    char_ids = list(char_ids)
    char_ids = [int(t.charachteristic_id.charachteristic_id) for t in char_ids]
    for char_id in char_ids:
        sample_value = Product_char.select(Product_char.value).where((Product_char.prod_id == prod_ids[0]) & (Product_char.charachteristic_id == char_id)).scalar()
        change = False
        for item in prod_ids:
            value = Product_char.select(Product_char.value).where((Product_char.prod_id == item) & (Product_char.charachteristic_id == char_id)).scalar()
            if value != sample_value:
                change = True
                break
        if change:
            char_name = Characheristic.select(Characheristic.characheristic_name).where(Characheristic.charachteristic_id == char_id).scalar()
            print(char_name + ": ")
            for item in prod_ids:
                value = Product_char.select(Product_char.value).where((Product_char.prod_id == item) & (Product_char.charachteristic_id == char_id)).scalar()
                prod_name = Product.select(Product.name).where(Product.prod_id == item).scalar()
                print(prod_name + " " + str(item) + ": " + str(value))
                
def add_to_compare(prod_id):
    product = Product.select().where(Product.prod_id == prod_id)[0]
    list_exist = Compare_list.select().where(Compare_list.category_id == product.category_id)
    if not list_exist:
        compare_list = Compare_list.create(
            category_id = product.category_id,
            user_id = 1
        )
        Product_compare.create(
            compare_list_id = compare_list.compare_list_id,
            prod_id = prod_id
        )
    else:
        Product_compare.create(
            compare_list_id = list_exist[0].compare_list_id,
            prod_id = prod_id
        )

def update_shops():
    update = Prod_store.update({Prod_store.available: 1}).where((Prod_store.prod_id == 333) & (Prod_store.store_id == 1)).execute()
    if update:
        product_list_ids = []
        result = (Product_in_list.select(Product_in_list.product_list_id).where(Product_in_list.prod_id == 333).scalar())
        if isinstance(result, list):
            product_list_ids.extend(result)
        else:
            product_list_ids.append(result)
        for list_id in product_list_ids:
            user_id = Product_list.select(Product_list.user_id).where(Product_list.product_list_id == list_id).scalar()
            prod_name = Product.select(Product.name).where(Product.prod_id == 333).scalar()
            store_name = Store.select(Store.name).where(Store.store_id == 1).scalar()
            text = prod_name + ' появился в наличии в магазине ' + store_name
            Notification.create(
                user = user_id,
                notify_type = 'mail',
                text = text,
                smtp = user_id
            )

############ Пример для тестирования
db.connect()
User.drop_table()
Store.drop_table()
Category.drop_table()
Characheristic.drop_table()
Category_char.drop_table()
Product.drop_table()
Product_char.drop_table()
Prod_store.drop_table()
Product_list.drop_table()
Product_in_list.drop_table()
Notification.drop_table()
Compare_list.drop_table()
Product_compare.drop_table()
db.create_tables([
    User, Store, Category, Characheristic, Category_char, Product, Product_char, Prod_store,
    Product_list, Product_in_list, Notification, Compare_list, Product_compare
])
new_user = create_new_user('veram', 'Vera')
Store.create(name = 'Леруа Мерлен', address = 'СПб')
Store.create(name =  'Максидом', address = 'Мск')
Category.create(category_name = 'отделка пола')
Category.create(category_name = 'отделка стен')
Category.create(category_name = 'сантехника')
Product.create(prod_id = 111, name = 'кафель', category_id = 2)
Product.create(prod_id = 222, name = 'обои', category_id = 2)
Product.create(prod_id = 333, name = 'ламинат', category_id = 1)
Product.create(prod_id = 444, name = 'душевая кабина', category_id = 3)
Product.create(prod_id = 555, name = 'душевая кабина', category_id = 3)
Product.create(prod_id = 666, name = 'душевая кабина', category_id = 3)
Product.create(prod_id = 777, name = 'кафель', category_id = 2)
Characheristic.create(characheristic_name = 'цвет')
Characheristic.create(characheristic_name = 'прочность')
Characheristic.create(characheristic_name = 'лёгкость обращения')
Characheristic.create(characheristic_name = 'материал')
Characheristic.create(characheristic_name = 'страна')
Characheristic.create(characheristic_name = 'тип стекла')
Characheristic.create(characheristic_name = 'ограждение')
Characheristic.create(characheristic_name = 'форма')
Characheristic.create(characheristic_name = 'высота поддона')
Characheristic.create(characheristic_name = 'конструкция дверей')
Category_char.create(charachteristic_id = 2, category_id = 2)
Category_char.create(charachteristic_id = 1, category_id = 2)
Category_char.create(charachteristic_id = 2, category_id = 1)
Category_char.create(charachteristic_id = 3, category_id = 1)
Category_char.create(charachteristic_id = 4, category_id = 2)
Category_char.create(charachteristic_id = 5, category_id = 2)
Category_char.create(charachteristic_id = 6, category_id = 3)
Category_char.create(charachteristic_id = 7, category_id = 3)
Category_char.create(charachteristic_id = 8, category_id = 3)
Category_char.create(charachteristic_id = 9, category_id = 3)
Category_char.create(charachteristic_id = 10, category_id = 3)
Product_char.create(prod_id = 111, charachteristic_id = 1, value = 'белый')
Product_char.create(prod_id = 111, charachteristic_id = 2, value = 8)
Product_char.create(prod_id = 111, charachteristic_id = 3, value = 10)
Product_char.create(prod_id = 222, charachteristic_id = 1, value = 'синий')
Product_char.create(prod_id = 222, charachteristic_id = 4, value = 'бумага')
Product_char.create(prod_id = 222, charachteristic_id = 5, value = 'Россия')
Product_char.create(prod_id = 333, charachteristic_id = 1, value = 'бежевый')
Product_char.create(prod_id = 333, charachteristic_id = 4, value = 'дсп')
Product_char.create(prod_id = 333, charachteristic_id = 5, value = 'Россия')
Product_char.create(prod_id = 444, charachteristic_id = 6, value = 'матовый')
Product_char.create(prod_id = 555, charachteristic_id = 6, value = 'матовый')
Product_char.create(prod_id = 666, charachteristic_id = 6, value = 'матовый')
Product_char.create(prod_id = 444, charachteristic_id = 7, value = 'есть')
Product_char.create(prod_id = 555, charachteristic_id = 7, value = 'есть')
Product_char.create(prod_id = 666, charachteristic_id = 7, value = 'нет')
Product_char.create(prod_id = 444, charachteristic_id = 8, value = 'прямоугольный')
Product_char.create(prod_id = 555, charachteristic_id = 8, value = 'прямоугольный')
Product_char.create(prod_id = 666, charachteristic_id = 8, value = 'прямоугольный')
Product_char.create(prod_id = 444, charachteristic_id = 9, value = '10')
Product_char.create(prod_id = 555, charachteristic_id = 9, value = '15')
Product_char.create(prod_id = 666, charachteristic_id = 9, value = '20')
Product_char.create(prod_id = 444, charachteristic_id = 10, value = 'раздвижные')
Product_char.create(prod_id = 555, charachteristic_id = 10, value = 'раздвижные')
Product_char.create(prod_id = 666, charachteristic_id = 10, value = 'пуш')
Product_char.create(prod_id = 777, charachteristic_id = 1, value = 'чёрный')
Product_char.create(prod_id = 777, charachteristic_id = 2, value = 7)
Product_char.create(prod_id = 777, charachteristic_id = 3, value = 9)
Prod_store.create(prod_id = 111, store_id = 2, price = 400, available = 20)
Prod_store.create(prod_id = 222, store_id = 2, price = 500, available = 2)
Prod_store.create(prod_id = 333, store_id = 1, price = 1000, available = 0)
Prod_store.create(prod_id = 444, store_id = 1, price = 10000, available = 1)
Prod_store.create(prod_id = 555, store_id = 2, price = 15000, available = 0)
Prod_store.create(prod_id = 666, store_id = 2, price = 20000, available = 4)
Prod_store.create(prod_id = 777, store_id = 1, price = 600, available = 50)


############ Реализация шагов

### Сценарий 1.1
# Запросили плитку по цене меньше 1000 за кв.м, любого цвета, прочность выше 6 (из 10), легкость обращения выше 6 (из 10)
find_product("кафель", 1000, [2, 3], [[7, 8, 9, 10], [7, 8, 9, 10]])

### Сценарий 2.1
# Добавляем в списки обои из Максидома и ламинат из Леруа, характеристики: любой цвет, любой материал, любая страна
find_product("обои", sys.maxsize, [], [])
add_product(1, 222, 2, 5)
find_product("ламинат", sys.maxsize, [], [])
add_product(1, 333, 1, 6)
maxidom = Product_list.select().where(Product_list.store_id == 2)
leroy = Product_list.select().where(Product_list.store_id == 1)
print("Проверка списка Максидома:")
for item in maxidom:
    print(item.store_id)
    print(item.create_date)
    print(item.total_sum)
print("\n")
print("Проверка списка Леруа мерлен:")
for item in leroy:
    print(item.store_id)
    print(item.create_date)
    print(item.total_sum)
print("\n")

### Сценарий 3.2
# Появился ламинат в Максидоме
update_shops()

### Сценарий 4.1
# Сравниваем 3 душевых кабины, их характеристики: тип стекла, ограждение, форма, высота поддона, конструкция дверей

find_product("душевая кабина", sys.maxsize, [], [])
add_to_compare(444)
add_to_compare(555)
add_to_compare(666)
compare_list_id = Compare_list.select(Compare_list.compare_list_id).where(Compare_list.category_id == 3)
compare(Compare_list.select().where(Compare_list.compare_list_id == compare_list_id)[0])

### Здесь использованы значения:
#Категории товаров: 1 - кафель, 2 - обои, 3 - ламинат, 4 - душевая кабина
#Магазины: 1 - Леруа мерлен, 2 - Максидом

