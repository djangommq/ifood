import csv
import json

import os

from get_restaurants_list import load_addresses
from utils import VERSION


# 为地址数据添加唯一标识， id
def process_address():
    origin_path = '../input/addresses_20180618.csv'
    new_path = '../data/{}/addresses.txt'.format(VERSION)
    new_dir = os.path.split(new_path)[0]
    if not os.path.exists(new_dir):
        os.makedirs(new_dir)
    with open(origin_path, 'r', encoding='utf-8') as fr, open(new_path, 'w', encoding='utf-8') as fw:
        csv_reader = csv.reader(fr)
        addresses = {}
        for row in csv_reader:
            if csv_reader.line_num == 1:
                continue

            state = row[0]
            if state not in addresses.keys():
                addresses[state] = []
            address = {
                'state': row[0],
                'city': row[1],
                'street': row[2],
            }
            # 将‘7,658’ → 7658
            tmp_num = row[3]
            if ',' in tmp_num:
                tmp_num = tmp_num.replace(',', '')
                tmp_num = tmp_num.replace('"', '')
            address['number'] = int(tmp_num)
            addresses[state].append(address)
        s = json.dumps(addresses)
        fw.write(s)
    ...


if __name__ == '__main__':
    process_address()