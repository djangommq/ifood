import json
import os
import random
import sys
import traceback
from time import sleep

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.wait import WebDriverWait

from utils import save_file, VERSION, log, launch_driver


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


def load_addresses():
    file_path = '../data/{}/addresses.txt'.format(VERSION)
    if not os.path.exists(file_path):
        result = {}
    else:
        with open(file_path, 'r', encoding='utf-8') as fr:
            s = fr.read()
            if len(s) == 0:
                result = {}
            else:
                result = json.loads(s)
    return result


def save_addresses(addresses):
    file_path = '../data/{}/addresses.txt'.format(VERSION)
    save_file(addresses, file_path)


def save_restaurants(rs, state):
    file_path = '../data/{}/restaurants/{}.txt'.format(VERSION, state)
    save_file(rs, file_path)


def load_restaurants(state):
    file_path = '../data/{}/restaurants/{}.txt'.format(VERSION, state)
    if not os.path.exists(file_path):
        result = {}
    else:
        with open(file_path, 'r', encoding='utf-8') as fr:
            s = fr.read()
            if len(s) == 0:
                result = {}
            else:
                result = json.loads(s)
    return result


# 之前餐馆以mongodb的id为key，便于update，
# 改为1,2,3...有序的key，便于分段请求
def process_restaurants(state):
    file_path = '../data/{}/restaurants/{}.txt'.format(VERSION, state)
    count = 0
    rs = {}
    with open(file_path, 'r', encoding='utf-8') as fr:
        s = fr.read()
        rs_dict = json.loads(s)
        for r in rs_dict.values():
            count += 1
            r_key = count
            r['restaurant_id'] = r_key
            rs[r_key] = r
    save_restaurants(rs, state)
    print('{}州共有餐馆：{}家'.format(state, count))


def get_restaurants_page(local_data):
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
        Select(state_element).select_by_value(local_data.get('state'))

        # 看看是否得到了输入地址信息的表单
        # 为select标签选择值, 选择两次，因为选择state后重新加载了
        sleep(3)
        city_element = check_element_by_xpath(driver, '//*[@id="box7"]/form/div[1]/div[2]/select')
        wait_to_display(city_element)
        Select(city_element).select_by_visible_text(local_data.get('city').upper())

        # 为两个input标签添加信息
        street_input = check_element_by_xpath(driver, '//*[@id="box7"]/form/div[2]/input[1]')
        number_input = check_element_by_xpath(driver, '//*[@id="box7"]/form/div[2]/input[2]')

        wait_to_display(street_input)
        wait_to_display(number_input)
        street_input.send_keys(local_data.get('street'))
        number_input.send_keys(local_data.get('number'))
        # 点击下街道编号输入框，确保自动补全的下拉框收回
        number_input.click()
        sleep(2)
        number_input.click()
        # 提交数据
        # 确保加载结束, 要么超时,要么找到标签
        submit_button = check_element_by_xpath(driver, '//*[@id="pre-search-naoSeiMeuCep"]/input[1]')
        wait_to_display(submit_button)
        submit_button.click()
        log('提交登录')

        # 确保加载结束, 要么超时,要么找到搜索结果，点击标签1标签
        # 搜索地址成功，选择第一个地址
        select_result = check_element_by_xpath(driver, '//*[@id="box7"]/form/div[4]/div/table/tbody/tr[1]/td[3]/a')
        wait_to_display(select_result)
        select_result.click()

        # 此处应该就能加载出餐馆列表了。
        # 下拉加载所有餐馆
        count_mark = 0
        log('加载餐馆列表中。。。')
        while count_mark < 1000:
            driver.execute_script("$('html,body').animate({'scrollTop':'700000000'},1000)")
            # 查找有没有加载
            if check_element_by_xpath(driver, '//*[@id="content"]/div[2]/div[2]') != -1:
                # 找到了就继续
                count_mark += 1
                # log('拉取餐馆列表进度', count_mark)
                continue
            else:
                # 查看到了底部
                if check_element_by_xpath(driver, '//*[@id="suggestLink"]') != -1:
                    log('加载结束')
                    break
            count_mark += 1

        log('开始获取所有餐馆的url')
        r_state = local_data.get('state')
        rs_new = get_restaurants_list(driver, r_state)
        log('新获取餐馆{}家。'.format(len(list(rs_new.keys()))))
        rs_origin = load_restaurants(r_state)
        log('原有餐馆{}家。'.format(len(list(rs_origin.keys()))))
        rs_origin.update(rs_new)
        log('更新后共有餐馆{}家。'.format(len(list(rs_origin.keys()))))
        save_restaurants(rs_origin, r_state)
        # 清理缓存
        # driver.delete_all_cookies()
        driver.close()
        return 0
    except Exception as e:
        log(e)
        log(traceback.format_exc())
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


def get_restaurants_list_by_state(state):
    count = -1
    while count == -1:
        try:
            # 加载地址，计算下目前进展
            all_addresses = load_addresses()
            addresses = all_addresses.get(state)
            has_get = 0
            all_count = len(addresses)
            for v in addresses:
                if v.get('has_get') is True:
                    has_get += 1
            log('获取餐馆列表的进度：{}/{}'.format(has_get, all_count))

            for v in addresses:
                if v.get('has_get') is True:
                    # log(v_id, "已经获取了数据")
                    continue
                log('正在获取。。。')
                return_code = get_restaurants_page(v)
                if return_code == 0:
                    v['has_get'] = True
                    save_addresses(all_addresses)
                    has_get += 1
                    log('获取成功')
                else:
                    log('获取{}出现错误，要查看异常原因'.format(v))
                log('获取餐馆列表的进度：{}/{}'.format(has_get, all_count))
                sleep(random.randint(3, 8))
            # check
            count = 0  # 假设已完成
            addresses = load_addresses().get(state)
            for a in addresses:
                if a.get('has_get') is None:
                    count = -1
                    break
            # 如果全部街道都获取了，就进行转换。
            if count == 0:
                process_restaurants(state)
        except Exception as e:
            log('异常退出一次, 原因：', e)
            return -1
    log(state, '的餐馆全部获取')
    return 0


if __name__ == '__main__':
    # sp:180
    # pr:62
    # rs:36
    # rj:77
    # mg:46
    # df:20
    # }
    states = ['SP', 'PR', 'RS', 'RJ', 'MG', 'DF']

    if len(sys.argv) > 1:
        index = int(sys.argv[1])
    else:
        index = 0
    state = states[index]
    get_restaurants_list_by_state(state)
