import pymongo

from get_restaurants_list import links_collection, restaurants_collection
from mongodb_utils import get_db


def unmark_doing(collection_name):
    db = get_db()
    query = {
        'doing': True,
        'done': None,
    }
    update = {
        "$set": {
            'doing': None,
        }
    }
    rs = db.update_many(collection_name, query, update)
    return rs.modified_count


if __name__ == "__main__":
    rs1 = unmark_doing(links_collection)
    rs2 = unmark_doing(restaurants_collection)
    print('标记links数目:{}'.format(rs1))
    print('标记restaurant数目:{}'.format(rs2))
