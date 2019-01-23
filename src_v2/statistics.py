import time

from get_restaurants_list import links_collection, restaurants_collection
from mongodb_utils import get_db


def count_done_links():
    db = get_db()
    query = {
        "done": True,
    }
    rs = db.find(links_collection, query)
    return rs.count()


def count_todo_links():
    db = get_db()
    query = {
        'done': None,
    }
    rs = db.find(links_collection, query)
    return rs.count()


def count_done_restaurants():
    db = get_db()
    query = {
        "done": True,
    }
    rs = db.find(restaurants_collection, query)
    return rs.count()


def count_todo_restaurants():
    db = get_db()
    query = {
        'done': None,
    }
    rs = db.find(restaurants_collection, query)
    return rs.count()


def count_all_links():
    db = get_db()
    rs = db.find(links_collection)
    return rs.count()


def count_all_restaurants():
    db = get_db()
    rs = db.find(restaurants_collection)
    return rs.count()


def count_doing_restaurants():
    db = get_db()
    query = {
        'doing': True,
        'done': None,
    }
    rs = db.find(restaurants_collection, query)
    return rs.count()


def count_doing_links():
    db = get_db()
    query = {
        'doing': True,
        'done': None,
    }
    rs = db.find(links_collection, query)
    return rs.count()


if __name__ == "__main__":
    format = '%Y-%m-%d-%H-%M-%S'
    current = time.localtime(time.time())
    dt = time.strftime(format, current)
    statistics_path = './progress_info.txt'
    with open(statistics_path, 'a', encoding='utf-8') as f:
        f.writelines('{}, 目前进展如下:\n'.format(dt))
        f.writelines(
            '链接总数:{}\t已处理:{}\t待处理:{}\t正在处理{}\n'.format(count_all_links(), count_done_links(), count_todo_links(),
                                                       count_doing_links()))
        f.writelines('餐馆总数:{}\t已处理:{}\t待处理:{}\t正在处理{}\n'.format(count_all_restaurants(), count_done_restaurants(),
                                                                count_todo_restaurants(), count_doing_restaurants()))
        print('{}, 目前进展如下:\n'.format(dt))
        print('链接总数:{}\t已处理:{}\t待处理:{}\t正在处理{}\n'.format(count_all_links(), count_done_links(), count_todo_links(), count_doing_links()))
        print('餐馆总数:{}\t已处理:{}\t待处理:{}\t正在处理{}\n'.format(count_all_restaurants(), count_done_restaurants(), count_todo_restaurants(), count_doing_restaurants()))
