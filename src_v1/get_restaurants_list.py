import logging
import random
import sys
import traceback
from time import sleep

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.wait import WebDriverWait

from utils import launch_driver, get_db


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


def get_state_by_name(name):
    states = {
        '1': {
            "name": 'SP',
            "id": 1,
        },
        '2': {
            "name": 'PR',
            "id": 2,
        },
        '3': {
            "name": 'RS',
            "id": 3,
        },
        '4': {
            "name": 'RJ',
            "id": 4,
        },
        '5': {
            "name": 'MG',
            "id": 5,
        },
        '6': {
            "name": 'DF',
            "id": 6,
        }
    }
    for s in states.values():
        if s.get('name') == name:
            return s


def get_state_by_id(id):
    states = {
        '1': {
            "name": 'SP',
            "id": 1,
        },
        '2': {
            "name": 'PR',
            "id": 2,
        },
        '3': {
            "name": 'RS',
            "id": 3,
        },
        '4': {
            "name": 'RJ',
            "id": 4,
        },
        '5': {
            "name": 'MG',
            "id": 5,
        },
        '6': {
            "name": 'DF',
            "id": 6,
        }
    }
    return states.get(str(id))


# 获取没有请求过的数据, 返回字典
def find_null_address(count=1):
    db = get_db()
    table = 'addresses'
    column = '*'
    condition = 'has_get is null limit {}'.format(count)
    result = list(db.select(table, column, condition))
    if len(result) == 0:
        return None
    else:
        return result[0]


def find_all_null_addresses():
    db = get_db()
    table = 'addresses'
    column = '*'
    condition = 'has_get is null'
    result = db.select(table, column, condition)
    return list(result)


def all_addresses():
    db = get_db()
    table = 'addresses'
    column = '*'
    result = db.select(table, column)
    return list(result)


def mark_address_has_get(address):
    db = get_db()
    table = 'addresses'
    data = {
        'has_get': '',
    }
    condition = 'id={}'.format(address.get('id'))
    result = db.update(table, data, condition)
    return result


def insert_restaurants(restaurants):
    db = get_db()
    state = ''
    for r in restaurants.values():
        state = get_state_by_name(r.get('state'))
        break
    table = state.get('name') + str(state.get('id'))
    sql = """
        CREATE TABLE IF NOT EXISTS {} 
        (id INT AUTO_INCREMENT PRIMARY KEY, 
        rid VARCHAR(50) UNIQUE,
        name VARCHAR(50),
        url VARCHAR(200),
        state VARCHAR(10),
        price VARCHAR(10),
        cuisine VARCHAR(50),
        evaluation VARCHAR(100),
        latitude VARCHAR(20),
        longitude VARCHAR(20),
        address_locality VARCHAR(50),
        address_region VARCHAR(50),
        address_street VARCHAR(50),
        postalcode VARCHAR(20),
        count_rating VARCHAR(10),
        max_rating_date VARCHAR(20),
        min_rating_date VARCHAR(20),
        has_get char(0) DEFAULT NULL)""".format(table)
    db.query(sql)
    for r in restaurants.values():
        last_id = db.insert(table, r)
        logging.info(last_id)


def find_null_restaurant(state, id):
    db = get_db()
    table = state.get('name') + str(state.get('id'))
    column = '*'
    condition = 'has_get is null and id = {} limit 1'.format(id)
    result = list(db.select(table, column, condition))
    if len(result) == 0:
        return None
    else:
        return result[0]


def update_restaurant(r):
    db = get_db()
    state = get_state_by_name(r.get('name'))
    table = state.get('name') + str(state.get('id'))
    rid = r.get('rid')
    condition = 'rid = {}'.format(rid)
    result = db.update(table, r, condition)
    return result


def find_all_null_restaurants(state):
    db = get_db()
    table = state.get('name') + str(state.get('id'))
    column = '*'
    condition = 'has_get is null'
    result = list(db.select(table, column, condition))
    if len(result) == 0:
        return None
    else:
        return result


def all_restaurants(state):
    db = get_db()
    table = state.get('name') + str(state.get('id'))
    column = '*'
    result = db.select(table, column)
    return list(result)


def mark_restaurant_has_get(restaurant):
    db = get_db()
    state = get_state_by_name(restaurant.get('state'))
    table = state.get('name') + str(state.get('id'))
    data = {
        'has_get': '',
    }
    condition = 'id={}'.format(restaurant.get('rid'))
    result = db.update(table, data, condition)
    return result


def get_restaurants_page(address):
    # 启动浏览器
    driver = launch_driver()

    host_url = 'https://www.ifood.com.br/'
    driver.get(host_url)
    try:
        # 先找到邮编和街道的切换链接
        switch_link = check_element_by_xpath(driver, '//*[@id="buscaCepPorEndereco"]')
        wait_to_display(switch_link)
        switch_link.click()

        # 看看是否得到了输入地址信息的表单
        # 为select标签选择值
        state_element = check_element_by_xpath(driver, '//*[@id="box7"]/form/div[1]/div[1]/select')
        wait_to_display(state_element)
        Select(state_element).select_by_value(address.get('state'))

        # 看看是否得到了输入地址信息的表单
        # 为select标签选择值, 选择两次，因为选择state后重新加载了
        sleep(3)
        city_element = check_element_by_xpath(driver, '//*[@id="box7"]/form/div[1]/div[2]/select')
        wait_to_display(city_element)
        Select(city_element).select_by_visible_text(address.get('city').upper())

        # 为两个input标签添加信息
        street_input = check_element_by_xpath(driver, '//*[@id="box7"]/form/div[2]/input[1]')
        number_input = check_element_by_xpath(driver, '//*[@id="box7"]/form/div[2]/input[2]')

        wait_to_display(street_input)
        wait_to_display(number_input)
        street_input.send_keys(address.get('street'))
        number_input.send_keys(address.get('number'))
        # 点击下街道编号输入框，确保自动补全的下拉框收回
        number_input.click()
        sleep(2)
        number_input.click()
        # 提交数据
        # 确保加载结束, 要么超时,要么找到标签
        submit_button = check_element_by_xpath(driver, '//*[@id="pre-search-naoSeiMeuCep"]/input[1]')
        wait_to_display(submit_button)
        submit_button.click()
        logging.info('提交登录')

        # 确保加载结束, 要么超时,要么找到搜索结果，点击标签1标签
        # 搜索地址成功，选择第一个地址
        select_result = check_element_by_xpath(driver, '//*[@id="box7"]/form/div[4]/div/table/tbody/tr[1]/td[3]/a')
        wait_to_display(select_result)
        select_result.click()

        # 此处应该就能加载出餐馆列表了。
        # 下拉加载所有餐馆
        count_mark = 0
        logging.info('加载餐馆列表中。。。')
        while count_mark < 1000:
            driver.execute_script("$('html,body').animate({'scrollTop':'700000000'},1000)")
            # 查找有没有加载
            if check_element_by_xpath(driver, '//*[@id="content"]/div[2]/div[2]') != -1:
                # 找到了就继续
                count_mark += 1
                # logging.info('拉取餐馆列表进度', count_mark)
                continue
            else:
                # 查看到了底部
                if check_element_by_xpath(driver, '//*[@id="suggestLink"]') != -1:
                    logging.info('加载结束')
                    break
            count_mark += 1

        logging.info('开始获取所有餐馆的url')
        r_state = address.get('state')
        rs_new = get_restaurants_list(driver, r_state)
        logging.info('新获取餐馆{}家。'.format(len(list(rs_new.keys()))))

        insert_restaurants(rs_new)
        # 清理缓存
        # driver.delete_all_cookies()
        driver.close()
        return 0
    except Exception as e:
        logging.info(e)
        logging.info(traceback.format_exc())
        driver.close()
        return -1


def get_restaurants_list(driver, r_state):
    rs_result = {}
    boxes = driver.find_elements_by_class_name('restaurant-card-link')
    for box in boxes:
        r_dict = {
            'url': box.get_attribute('href'),
            'name': box.get_attribute('data-name'),
            'id': box.get_attribute('data-rid'),
            'state': r_state,
        }
        id = box.get_attribute('data-rid')
        rs_result[id] = r_dict

    return rs_result


def get_all_restaurants_list():
    try:
        # 加载地址，计算下目前进展
        total = len(all_addresses())

        address = 0
        while address is not None:
            remind_addresses = len(find_all_null_addresses())
            logging.info('目前剩余:{}/{}'.format(remind_addresses, total))
            address = find_null_address()
            if address is None:
                break
            return_code = get_restaurants_page(address)
            if return_code == 0:
                mark_address_has_get(address)
            sleep(random.randint(3, 8))
        logging.info('全部地址处理完毕, 剩余:{}'.format(len(find_all_null_addresses())))
    except Exception as e:
        logging.warning('异常退出一次, 原因：', e)
        return -1
    return 0


if __name__ == '__main__':
    # sp:180
    # pr:62
    # rs:36
    # rj:77
    # mg:46
    # df:20
    # }
    # states = ['SP', 'PR', 'RS', 'RJ', 'MG', 'DF']
    states = {
        '1': {
            "name": 'SP',
            "id": 1,
        },
        '2': {
            "name": 'PR',
            "id": 2,
        },
        '3': {
            "name": 'RS',
            "id": 3,
        },
        '4': {
            "name": 'RJ',
            "id": 4,
        },
        '5': {
            "name": 'MG',
            "id": 5,
        },
        '6': {
            "name": 'DF',
            "id": 6,
        }
    }

    if len(sys.argv) > 1:
        index = sys.argv[1]
    else:
        index = '1'
    state = states.get(index)
    get_restaurants_list()
