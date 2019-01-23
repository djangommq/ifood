import logging
import random
import traceback
from time import sleep

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait

from utils import launch_driver, VERSION
from mongodb_utils import get_db

links_collection = 'links_{}'.format(VERSION)
restaurants_collection = 'restaurant_{}'.format(VERSION)


def check_element_by_xpath(web_driver, value):
    try:
        # 判断是否加载完毕
        WebDriverWait(web_driver, 10).until(
            expected_conditions.presence_of_element_located((By.XPATH, value))
        )
        # 搜索地址成功，选择第一个地址
        select_result = web_driver.find_element_by_xpath(value)
        return select_result
    except Exception as e:
        # print('加载超时', e)
        # print(traceback.format_exc())
        return -1


def wait_to_display(element):
    count = 5
    if element != -1:
        while count > 0:
            if element.is_displayed() is False:
                sleep(1)
                print('等待1秒')
                count -= 1
                continue
            else:
                break


# 获取没有请求过的数据, 返回字典
# 找第一个doing是None的
def find_todo_link():
    db = get_db()
    query = {"doing": None}
    update = {"doing": True}
    link = db.find_one_and_mark(links_collection, query, update)
    return link


def all_addresses():
    db = get_db()
    table = 'addresses'
    column = '*'
    result = db.select(table, column)
    return list(result)


def mark_link_done(link):
    db = get_db()
    query = {
        "id": link.get('id'),
    }
    update = {
        "doing": True,
        "done": True,
    }
    db.find_and_mark(links_collection, query, update)


def insert_restaurants(restaurants):
    db = get_db()
    # 要求rid不重复
    # condition = ['rid']
    # db.insert_many(restaurants_collection, restaurants, condition)
    # 既然要求rid 不重复, 在插入大量是 使用update配合upsert, 如果存在则更新, 不存在则插入
    for r in restaurants:
        query = {
            "rid": r.get('rid'),
        }
        update = {
            "$set": r,
        }
        db.update_one(restaurants_collection, query, update, True)


def find_todo_restaurant():
    db = get_db()
    query = {"doing": None}
    update = {"doing": True}
    r = db.find_one_and_mark(restaurants_collection, query, update)
    return r


def update_restaurant(r):
    db = get_db()
    query = {'rid': r.get('rid')}
    db.find_one_and_mark(restaurants_collection, query, r)


def mark_restaurant_done(restaurant):
    db = get_db()
    query = {
        "rid": restaurant.get('rid'),
    }
    update = {
        "doing": True,
        "done": True,
    }
    db.find_and_mark(restaurants_collection, query, update)


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


def get_restaurants_page(link):
    # 启动浏览器
    driver = launch_driver()
    url = link.get('url')
    logging.info('当前请求:{}'.format(url))
    driver.get(url)
    try:
        # 此处应该就能加载出餐馆列表了。
        # 下拉加载所有餐馆
        # print(driver.page_source)

        # 重定向判定
        if driver.current_url == url:
            pass
        else:
            logging.info('该网页进行了重定向,稍后再请求.')
            return -1

        forbid = check_element_by_xpath(driver, '//*[@id="searchMsg"]')
        if forbid == -1:
            pass
        else:
            logging.info(forbid.text)
            logging.info('ip被禁止访问')
            return -1

        # 检测弹窗并模拟点击
        try:
            ad_button = driver.find_element_by_class_name('ab-message-button')
            if ad_button != -1:
                logging.info('页面弹出了广告')
                ad_button.click()
                sleep(1)
        except Exception as e:
            # logging.info(e)
            # logging.info(traceback.format_exc())
            pass

        count_mark = 0
        logging.info('加载餐馆列表中。。。')
        # 先判断是否需要请求多页, 如果为空或者一页显示完整, 不再请求
        if check_element_by_xpath(driver, '//*[@id="suggestLink"]') != -1:
            logging.info('加载结束')
            rs_new = get_restaurants_list(driver)
            logging.info('加载餐馆: {}'.format(len(rs_new)))
            insert_restaurants(rs_new)
        else:
            # 不使用下拉, 尝试使用js发送ajax请求, 请求内容见下文
            """
            $.ajax({
                url:'https://www.ifood.com.br/lista-restaurantes/filtro',
                method: 'post',
                data: {
                    page: 12,
                    city: 'SAO-PAULO',
                    state: 'SP',
                    ordenacao: 0
                },
                success: function(res) {
                    console.log(res)
                },
                fail: function(error) {
                    alert(error)
                },
                complete: function() {
                }
            })
            """
            logging.info('加载更多...')
            page = 1
            local_info = url.split("/")[-2]
            index = local_info.rfind('-')
            city_name = local_info[:index]
            state_name = local_info[index + 1:]
            while page < 500:
                # 因为访问首页会自动请求page=1, 所有这里从2开始
                page += 1
                post_data = {
                    'url':'https://www.ifood.com.br/lista-restaurantes/filtro',
                    'method': 'post',
                    'data': {
                        'page': page,
                        'city': city_name,
                        'state': state_name,
                        'ordenacao': 0
                    }

                }
                filtro_script_fore = '$.ajax({}'.format(post_data)[:-1]
                filtro_script_end = """
                    ,success: function(res) {
                        $(".tabs.flex-tab").append(res)
                    },
                    fail: function(error) {
                        console.log(error)
                    },
                    complete: function() {
                    }
                    })"""
                filtro_script = filtro_script_fore + filtro_script_end
                driver.execute_script(filtro_script)
                # 查找是否存在标签restaurant-card-link, 如果为空, 则说明没有餐馆或者加载结束
                rs_new = get_restaurants_list(driver)
                logging.info('加载餐馆: {}'.format(len(rs_new)))
                if len(rs_new) == 0:
                    logging.info('加载结束')
                    break
                else:
                    insert_restaurants(rs_new)
                    # 清空
                    driver.execute_script("$('.restaurant-card-link').remove()")

            logging.info('共下拉加载次数:{}'.format(page))
        driver.close()
        return 0
    except Exception as e:
        logging.info(e)
        logging.info(traceback.format_exc())
        driver.close()
        return -1


def get_restaurants_list(driver):
    rs_result = []
    boxes = driver.find_elements_by_class_name('restaurant-card-link')
    for box in boxes:
        r_dict = {
            'rid': box.get_attribute('data-rid'),
            'url': box.get_attribute('href'),
            'name': box.get_attribute('data-name'),
        }
        rs_result.append(r_dict)
    return rs_result


def get_all_restaurants_list():
    try:
        # 加载地址，计算下目前进展
        while True:
            link = find_todo_link()
            if link is None:
                logging.info('全部获取结束')
                break
            return_code = get_restaurants_page(link)
            if return_code == 0:
                mark_link_done(link)
            sleep(random.randint(2, 4))
        if find_todo_link() is None:
            logging.info('所有地址处理完毕')
            new_todo = unmark_doing(links_collection)
            print('标记link数目:{}'.format(new_todo))
            if new_todo == 0:
                # 运行完了, 尽可能等待1小时,
                sleep(3600)

    except Exception as e:
        logging.warning('异常退出一次, 原因：', e)
        return -1
    return 0


if __name__ == '__main__':
    get_all_restaurants_list()
    ...