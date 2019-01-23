import csv
import time

import os

from mongodb_utils import get_db
from get_restaurants_list import restaurants_collection
from utils import VERSION


def r_to_csv(r):
    # rs_info_path = '../data/{}/restaurants/{}.txt'.format(VERSION, state)
    header = [
        'rid',
        'url',
        'name',
        'cuisine',
        'rating_summary',
        'price',
        'latitude',
        'longitude',
        'address_locality',
        'address_region',
        'max_rating_date',
        'min_rating_date',
        'count_rating',

    ]
    csv_path = '../data/{}/{}_ifood.csv'.format(VERSION, VERSION)
    csv_dir = os.path.split(csv_path)[0]
    if not os.path.exists(csv_dir):
        os.makedirs(csv_dir)
    if not os.path.exists(csv_path):
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            csv_f = csv.DictWriter(f, fieldnames=header)
            csv_f.writeheader()
    with open(csv_path, 'a+', newline='', encoding='utf-8') as f:
        csv_f = csv.DictWriter(f, fieldnames=header)
        tmp_dict = {}
        for h in header:
            if h == 'address_region':
                url = r.get('url')
                tmp_dict[h] = url.split('/')[-2].split('-')[-1]
                # print(url, tmp_dict[h])
            else:
                tmp_dict[h] = r.get(h)
        csv_f.writerow(tmp_dict)


# 导出字典, 旧的数据也保存成1个字典, 然后旧的.update(新的)

if __name__ == "__main__":
    db = get_db()
    format = '%Y-%m-%d-%H-%M-%S'
    current = time.localtime(time.time())
    dt = time.strftime(format, current)
    query = {
        'done': True,
        'price': {"$exists": True}
    }
    all = db.find(restaurants_collection, query)
    for a in all:
        r_to_csv(a)
    # 输出下统计结果
    all_count = all.count()
    # 有评论的
    rate_zero = db.find_count(restaurants_collection, {
        'done': True,
        'price': {"$exists": True},
        'count_rating': '0',
    })
    rate_other = db.find_count(restaurants_collection, {
        'done': True,
        'price': {"$exists": True},
        'count_rating': {
            "$ne": '0',
        },
    })
    print('一共有餐馆{}的详细信息,\n 其中{}家餐馆评论为0,\n {}家餐馆有评论文件\n'.format(all_count, rate_zero, rate_other))
