import csv

from utils import get_db


# 为地址数据添加唯一标识， id, 写入线上数据库 ifood20180802 → addresses(表示第二次)
def process_address(db, table):
    origin_path = '../input/addresses_20180618.csv'
    with open(origin_path, 'r', encoding='utf-8') as fr:
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
            db.insert(table, address)


if __name__ == '__main__':
    db = get_db()
    table = 'addresses'
    sql = 'CREATE TABLE IF NOT EXISTS {} (id INT AUTO_INCREMENT PRIMARY KEY, state VARCHAR(100),city VARCHAR(100), street VARCHAR(100), number INT(30), has_get char(0) DEFAULT NULL)'.format(table)
    db.query(sql)
    process_address(db, table)