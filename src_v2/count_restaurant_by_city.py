from get_restaurants_list import restaurants_collection
from mongodb_utils import get_db
from utils import VERSION


def init_statistic_collection():
    db = get_db()
    statistic_collection = 'ifood_statistic'
    file_path = '../input/links.csv'
    with open(file_path, 'r') as f:
        links = f.readlines()
    for link in links:
        print(link)
        city_name= get_name_from_link(link)
        input = {
            'link': link.strip(),
            'city_name': city_name,
        }
        db.insert_one(statistic_collection, input)


def get_name_from_link(link):
    city = link.split('/')[-2]
    new_city = city.rsplit('-', 1)[0].replace('-', ' ').upper()
    return new_city


def count_restaurant_by_city():
    db=get_db()
    statistic_collection = 'ifood_statistic'
    links = db.find(statistic_collection)
    print(links)
    for l in links:
        link = l.get('link')
        print(link)
        query1 = {
            'url':{
                '$regex': "^{}.*?".format(link),
            }
        }
        print(query1)
        count = db.find(restaurants_collection, query1).count()
        print(count)

        query2 = {
            'link': link,
        }
        form = {
            "$set":{
                VERSION: count,
            }
        }
        db.update_one(statistic_collection, query2, form, upsert=True)
        # break

if __name__ == "__main__":
    # init_statistic_collection()
    count_restaurant_by_city()