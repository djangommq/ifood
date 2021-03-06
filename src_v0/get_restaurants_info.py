import csv
import json
import sys
import traceback
from bs4 import BeautifulSoup
from time import sleep

import os

from get_restaurants_list import check_element_by_xpath, wait_to_display, load_restaurants, save_restaurants
from utils import VERSION, log, launch_driver, save_file


# 主方法
def get_restaurant_info(r):
    driver = launch_driver()

    try:
        # 请求链接
        url = r.get('url')
        log(url)
        driver.get(url)

        # 重定向判定
        if driver.current_url == url:
            pass
        else:
            log('该网页进行了重定向,不再获取.')
            return 0

        # 首先分析参观信息,更新到new_info, 如果评论数量为0,直接跳过,不再点击评论
        # 从script中解析出新信息
        sleep(2)
        new_info = parse_new_info(driver)
        if int(new_info.get('count_rating')) == 0:
            log('餐馆评论为0, 可以直接跳过')
            return 0

        # 开始点击加载评论
        show_rate = check_element_by_xpath(driver, '//*[@id="showRating"]/a')
        show_rate.click()

        # 增加判断,如果js加载失败或点击加载失败,没有active表示没有加载出评论,直接跳过
        parent_tag = check_element_by_xpath(show_rate, '..')
        if parent_tag.get_attribute('class') != 'active':
            log('评论加载失败,跳过')
            return -1

        # 拉取评论
        log('拉取评论中...')
        while True:
            driver.execute_script("$('html,body').animate({'scrollTop':'700000000'},1000)")
            ver_mais = check_element_by_xpath(driver, '//*[@id="ratingContent"]/div[3]/div[2]')
            # 没有ver_mais, 就结束. 实际正常应该是ver_mais不可见了
            if ver_mais == -1:
                break
            else:
                # log('没找到评论加载完毕,说明等待加载')
                wait_to_display(ver_mais)
                if ver_mais.is_displayed() is False:
                    break
                ver_mais.click()
                # log('加载更多评论。。。')
                # 等待三秒页面加载
                sleep(2)

        # 加载结束, 解析源代码
        source_page = BeautifulSoup(driver.page_source, 'html.parser')

        # 解析出评论
        comments = parse_comments(source_page, new_info)

        # 更新餐馆信息，保存评论信息
        # 获得的新的信息，不再更新到源文件，直接输出到csv文件吧

        # r.update(new_info)
        new_info['state'] = r.get('state')
        new_info['id'] = r.get('id')
        r_to_csv(new_info)
        save_comments(comments, r)
        return 0
    except Exception as e:
        log(traceback.format_exc())
        return -1
    finally:
        driver.close()


def parse_new_info(driver):
    try:
        source_page = BeautifulSoup(driver.page_source, 'html.parser')
        geo_content = source_page.find('script', type='application/ld+json')

        # 异常修复5次，还不行就跳过
        r = geo_content.text.strip()
        loop_mark = 5
        r_info = None
        while loop_mark > 0:
            try:
                r_info = json.loads(r)
                break
            except Exception as e1:
                log('修复json数据')
                code = int(str(e1).split(' ')[-1].replace(')', ''))
                error_c_index = r.rfind(',', 0, code)
                r = r[:error_c_index] + r[error_c_index + 1:]
                loop_mark -= 1
                ...

        if r_info is None:
            new_info = None
            pass
        else:
            new_info = {
                'url': r_info.get('url'),
                'name': r_info.get('name'),
                'cuisine': r_info.get('servesCuisine'),
                'rating_summary': r_info.get('aggregateRating').get('ratingValue'),
                'price': r_info.get('priceRange'),
                'latitude': r_info.get('geo').get('latitude'),
                'longitude': r_info.get('geo').get('longitude'),
                'address_locality': r_info.get('address').get('addressLocality'),
                'address_region': r_info.get('address').get('addressRegion'),
                'address_street': r_info.get('address').get('streetAddress'),
                'postalcode': r_info.get('address').get('postalCode'),
                'count_rating': r_info.get('aggregateRating').get('reviewCount'),
                'max_rating_date': None,
                'min_rating_date': None,
            }
            # 增加log,和下面统计的评论进行比对
        return new_info
    except Exception as e:
        log('获取餐馆坐标出错')
        log(traceback.format_exc())
        raise e


def parse_comments(source_page, new_info):  # 11
    log('解析评论中。。。')
    # eval_boxes = web_driver.find_elements_by_class_name('evaluation')
    # eval_boxes = source_page.find_all('.evaluation')
    eval_boxes = source_page.findAll('article', {'class': 'evaluation'})
    # 不能这样判断,因为expect_count只是没有内容的评级的数量
    log('全部评论{}条'.format(len(eval_boxes)))
    # log(type(expect_count))
    # if int(expect_count) != len(eval_boxes):
    #     log('评论加载没有结束,需要跳过重新加载')
    #     return None.get('len')
    comments = {}
    count = 0
    for box in eval_boxes:
        count += 1
        # log(count)
        # print(box.find('div', {'class':'evaluation-header'}))
        if box.find('div', {'class': 'evaluation-header'}):
            source = 'C'
        else:
            source = 'R'
        try:
            if source == 'C':
                comment_name = box.find('h1', {'class': 'user-name'}).text
                user_score_str = box.find('div', {'class': 'user-score'}).text
                comment_rating = int(user_score_str.replace(',', '')) / 10.0
                comment_date = box.find('div', {'class': 'comment-date'}).text
                comment_desc = box.find('div', {'class': 'user-comment'}).text
                try:
                    # 店家没有评论，返回None
                    comment_reply = box.find('div', {'class': 'restaurant-comment'}).text
                except:
                    comment_reply = None
                tmp_r = {
                    'source': source,
                    'comment_name': comment_name,
                    'comment_date': comment_date,
                    'comment_rating': comment_rating,
                    'comment_desc': comment_desc,
                    'comment_reply': comment_reply,
                }
                comments[count] = tmp_r
            elif source == 'R':
                rating_name = box.find('h1', {'class': 'user-name'}).text
                user_score_str = box.find('div', {'class': 'user-score'}).text
                rating_value = int(user_score_str.replace(',', '')) / 10.0
                rating_date = box.find('div', {'class': 'comment-date'}).text
                if new_info.get('max_rating_date') is None:
                    new_info['max_rating_date'] = rating_date
                new_info['min_rating_date'] = rating_date
                tmp_r = {
                    'source': source,
                    'rating_name': rating_name,
                    'rating_value': rating_value,
                    'rating_date': rating_date,
                }
                comments[count] = tmp_r
            # log(tmp_r)
        except:
            log(traceback.format_exc())
            log('获取评论细节出错')
    log('解析评论结束')
    return comments


def save_comments(comments, r):
    state = r.get('state')
    name = r.get('id')
    file_path = '../data/{}/comments/{}/{}.csv'.format(VERSION, state, name)
    header = [
        'source',
        'comment_name',
        'comment_date',
        'comment_rating',
        'comment_desc',
        'comment_reply',
        'rating_name',
        'rating_value',
        'rating_date'
    ]
    file_dir = os.path.split(file_path)[0]
    if not os.path.exists(file_dir):
        os.makedirs(file_dir)
    with open(file_path, 'w', newline='', encoding='utf-8') as f:
        csv_f = csv.writer(f)
        csv_f.writerow(header)
        for comment in comments.values():
            tmp_row = []
            for h in header:
                tmp_content = comment.get(h)
                if tmp_content is None:
                    pass
                elif type(tmp_content) == str:
                    tmp_content = tmp_content.encode("gbk", 'ignore').decode("gbk", "ignore")
                tmp_row.append(tmp_content)
            csv_f.writerow(tmp_row)


def r_to_csv(r):
    # rs_info_path = '../data/{}/restaurants/{}.txt'.format(VERSION, state)
    header = [
        'url',
        'name',
        'cuisine',
        'rating_summary',
        'price',
        'latitude',
        'longitude',
        'address_locality',
        'address_region',
        'address_street',
        'postalcode',
        'max_rating_date',
        'min_rating_date',
        'count_rating',
        'id'
    ]
    state = r.get('state')
    csv_path = '../data/{}/restaurants/{}.csv'.format(VERSION, state)
    csv_dir = os.path.split(csv_path)[0]
    if not os.path.exists(csv_dir):
        os.makedirs(csv_dir)
    if not os.path.exists(csv_path):
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            csv_f = csv.writer(f)
            csv_f.writerow(header)
    with open(csv_path, 'a+', newline='', encoding='utf-8') as f:
        csv_f = csv.writer(f)
        tmp_raw = []
        for h in header:
            try:
                tmp_content = r.get(h)
                if tmp_content is not None:
                    tmp_content = tmp_content.encode("gbk", 'ignore').decode("gbk", "ignore")
                # print(r.get(h))
                tmp_raw.append(tmp_content)
            # tmp_raw.append(r.get(h))
            except:
                print(r.get(h))
                pass
        csv_f.writerow(tmp_raw)


def get_restaurants_info_by_state(state, start_num=1, end_num=0):

    rs = load_restaurants(state)

    # 开始获取数据, 允许程序意外中断10次
    count = 10
    while count > 0:
        # 确定运行数据范围
        total = len(list(rs.keys()))

        if start_num == 0:
            start_num = 1
        if end_num == 0 or end_num > total:
            end_num = total + 1
        log('脚本将要获取州:{}, id为{}至{}的餐馆的数据'.format(state, start_num, end_num - 1))

        # 统计目前进度
        has_get_count = 0
        for i in range(start_num, end_num):
            r = rs.get(str(i))
            if r.get('has_get') is True:
                has_get_count += 1
        log('脚本重新启动, 目前进展：{}/{}'.format(has_get_count, end_num - start_num))

        try:
            for r_id in range(start_num, end_num):
                r = rs.get(str(r_id))
                if r.get('has_get') is True:
                    # log(r_name, "已经获取了数据")
                    continue
                log('开始进行', r_id)
                return_mark = get_restaurant_info(r)
                if return_mark == 0:
                    r['has_get'] = True
                    save_restaurants(rs, state)
                    has_get_count += 1
                    # 输出下当前进展
                    log('目前进展：{}/{}'.format(has_get_count, end_num - start_num))
                else:
                    log(r_id, '的地址出现错误，要查看异常原因')
                sleep(5)

            # check
            rs = load_restaurants(state)
            for i_id in range(start_num, end_num):
                r = rs.get(str(i_id))
                if r.get('has_get') is None:
                    count = -1
                    break
                count = 0
        except Exception as e:
            log('异常退出一次, 原因：', e)
            count -= 1
    return 0

# 分段统计数据, 后两个参数是起始和末尾id
# 包含start, 不包含end
if __name__ == '__main__':

    states = ['SP', 'PR', 'RS', 'RJ', 'MG', 'DF']

    start = 1
    end = 0
    # 获取输入
    if len(sys.argv) == 2:
        index = int(sys.argv[1])
    elif len(sys.argv) == 4:
        index = int(sys.argv[1])
        start = int(sys.argv[2])
        end = int(sys.argv[3]) + 1
    else:
        index = 0

    state = states[index]
    get_restaurants_info_by_state(state, start, end)
