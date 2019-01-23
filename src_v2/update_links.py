import json

from mongodb_utils import Mongodb, get_db
from utils import VERSION

db = get_db()
file_path = '../input/links.csv'
with open(file_path, 'r') as f:
    result = f.readlines()

links_collection = 'links_{}'.format(VERSION)
dict_links = []
count = 1
for l in result:
    data = {
        'id': count,
        'url': l.strip(),
    }
    dict_links.append(data)
    count += 1

db.insert_many(links_collection, dict_links, ['url'])