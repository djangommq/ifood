import csv
import pickle
import json
import logging
import traceback
from bs4 import BeautifulSoup

import os
from time import sleep

from get_restaurants_list import check_element_by_xpath, wait_to_display, update_restaurant, find_todo_restaurant, \
    mark_restaurant_done, restaurants_collection, unmark_doing
from utils import VERSION, launch_driver

from mongodb_utils import *
# 创建链接mongo数据的对象
client_mongo=get_db()

# 存储评论数据的表名称
table_name=VERSION+'comment'

# 主方法
def get_restaurant_info(r):
    driver = launch_driver()

    try:
        # 请求链接
        url = r.get('url')
        logging.info(url)
        driver.get(url)

        # 重定向判定
        if driver.current_url == url:
            pass
        else:
            logging.info('该网页进行了重定向,稍后再请求.')
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

        # 首先分析参观信息,更新到new_info, 如果评论数量为0,直接跳过,不再点击评论
        # 从script中解析出新信息
        new_info = parse_new_info(driver)
        if new_info.get('count_rating') is None:
            pass
        elif int(new_info.get('count_rating')) == 0:
            logging.info('餐馆评论为0, 可以直接跳过')
            new_info['state'] = r.get('state')
            new_info['rid'] = r.get('rid')
            update_restaurant(new_info)
            return 0

        # 20181219 ifood退出新版网页, 弹窗选择取消
        cancelModal_tag = check_element_by_xpath(driver, '//*[@id="cancelModal"]')
        if cancelModal_tag is None:
            logging.info('新页面提醒没有弹出')
        else:
            cancelModal_tag.click()
            logging.info('点击下一个按钮, 稍后再看')
            sleep(2)

        # 开始点击加载评论
        show_rate = check_element_by_xpath(driver, '//*[@id="showRating"]/a')
        show_rate.click()

        # 增加判断,如果js加载失败或点击加载失败,没有active表示没有加载出评论,直接跳过
        parent_tag = check_element_by_xpath(show_rate, '..')
        if parent_tag.get_attribute('class') != 'active':
            logging.info('评论加载失败,跳过')
            return -1

        # 拉取评论之前先判断是否没有评论
        sleep(2)
        no_comment= driver.find_element_by_class_name('no-comments')
        if no_comment.is_displayed() is True:
            logging.info('评论还是为零, 结束下拉.')
            new_info['state'] = r.get('state')
            new_info['rid'] = r.get('rid')
            new_info['count_rating'] = 0
            update_restaurant(new_info)
            return 0

        # 拉取评论
        logging.info('拉取评论中...')
        while True:
            driver.execute_script("$('html,body').animate({'scrollTop':'700000000'},1000)")
            ver_mais = check_element_by_xpath(driver, '//*[@id="ratingContent"]/div[3]/div[2]')
            # 没有ver_mais, 就结束. 实际正常应该是ver_mais不可见了
            if ver_mais == -1:
                break
            else:
                # logging.info('没找到评论加载完毕,说明等待加载')
                wait_to_display(ver_mais)
                if ver_mais.is_displayed() is True:
                    ver_mais.click()
                    sleep(2)
                else:
                    break

        # 加载结束, 解析源代码
        source_page = BeautifulSoup(driver.page_source, 'html.parser')

        # 解析出评论
        comments = parse_comments(source_page, new_info)

        # 更新餐馆信息，保存评论信息
        # 获得的新的信息，不再更新到源文件，直接输出到csv文件吧
        # r.update(new_info)
        new_info['state'] = r.get('state')
        new_info['rid'] = r.get('rid')
        # 统计不含评论内容的评论
        tmp_count = 0
        for comment in comments.values():
            if comment.get('source') == "R":
                tmp_count += 1
        new_info['count_rating'] = tmp_count
        update_restaurant(new_info)
        save_comments(comments, r)
        return 0
    except Exception as e:
        logging.info(traceback.format_exc())
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
                logging.info('修复json数据')
                code = int(str(e1).split(' ')[-1].replace(')', ''))
                error_c_index = r.rfind(',', 0, code)
                r = r[:error_c_index] + r[error_c_index + 1:]
                loop_mark -= 1

        if r_info is None:
            new_info = None
            pass
        else:
            new_info = {
                'url': driver.current_url,
                'name': r_info.get('name'),
                'cuisine': r_info.get('servesCuisine'),
                'price': r_info.get('priceRange'),
                'max_rating_date': None,
                'min_rating_date': None,
            }
            if r_info.get('aggregateRating') is None:
                new_info['rating_summary'] = None
                new_info['count_rating'] = None
            else:
                new_info['rating_summary'] = r_info.get('aggregateRating').get('ratingValue')
                new_info['count_rating'] = r_info.get('aggregateRating').get('reviewCount')

            if r_info.get('geo') is None:
                new_info['latitude'] = None
                new_info['longitude'] = None
            else:
                new_info['latitude'] = r_info.get('geo').get('latitude')
                new_info['longitude'] = r_info.get('geo').get('longitude')
                
            if r_info.get('address') is None:
                new_info['address_locality'] = None
                new_info['address_region'] = None
                new_info['address_street'] = None
                new_info['postalcode'] = None
            else:
                new_info['address_locality'] = r_info.get('address').get('addressLocality')
                new_info['address_region'] = r_info.get('address').get('addressRegion')
                new_info['address_street'] = r_info.get('address').get('streetAddress')
                new_info['postalcode'] = r_info.get('address').get('postalCode')

            # 增加log,和下面统计的评论进行比对
        return new_info
    except Exception as e:
        logging.info('获取餐馆坐标出错')
        logging.info(traceback.format_exc())
        raise e


def parse_comments(source_page, new_info):  # 11
    logging.info('解析评论中。。。')
    # eval_boxes = web_driver.find_elements_by_class_name('evaluation')
    # eval_boxes = source_page.find_all('.evaluation')
    eval_boxes = source_page.findAll('article', {'class': 'evaluation'})
    # 不能这样判断,因为expect_count只是没有内容的评级的数量
    logging.info('全部评论{}条'.format(len(eval_boxes)))
    # logging.info(type(expect_count))
    # if int(expect_count) != len(eval_boxes):
    #     logging.info('评论加载没有结束,需要跳过重新加载')
    #     return None.get('len')
    comments = {}
    count = 0
    for box in eval_boxes:
        count += 1
        # logging.info(count)
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
            # logging.info(tmp_r)
        except:
            logging.info(traceback.format_exc())
            logging.info('获取评论细节出错')
    logging.info('解析评论结束')
    return comments


def save_comments(comments, r):
    #https://www.ifood.com.br/delivery/sao-paulo-sp/vip-sushi-1-peca--r1-indianopolis
    # 访问餐厅的url
    rest_url = r.get('url')
    str_list = rest_url.split('/')
    # 最终餐厅信息保存名称
    name =str_list[-2] + '_' + str_list[-1]

    file_path = '../data/{}/comments/{}.csv'.format(VERSION, name)
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
    # with open(file_path, 'w', newline='', encoding='utf-8') as f:
    #     csv_f = csv.writer(f)
    #     csv_f.writerow(header)
    # 该列表用于存储该餐馆的所有评论信息
    comment_info_list=[]
    for comment in comments.values():
        tmp_row = []
        for h in header:
            tmp_content = comment.get(h)
            if tmp_content is None:
                pass
            elif type(tmp_content) == str:
                tmp_content = tmp_content.encode("gbk", 'ignore').decode("gbk", "ignore")
            tmp_row.append(tmp_content)
        # csv_f.writerow(tmp_row)
        comment_info_list.append(tmp_row)
    comment_info_strb=json.dumps(comment_info_list)
    comment_dict={
        'comment_name':name+'.csv',
        'comment_content':comment_info_strb
    }
    client_mongo.insert_one(table_name,comment_dict,condition=['comment_name'])



def get_all_restaurants_info():
    while True:
        r = find_todo_restaurant()
        if r is None:
            logging.info('所有餐馆处理完毕')
            new_todo = unmark_doing(restaurants_collection)
            print('标记restaurant数目:{}'.format(new_todo))
            if new_todo == 0:
                # 运行完了, 尽可能等待1小时,
                sleep(3600)
            break
        return_code = get_restaurant_info(r)
        if return_code == 0:
            mark_restaurant_done(r)
        else:
            logging.error("{}餐馆出现错误".format(r))


# 分段统计数据, 后两个参数是起始和末尾id
# 包含start, 不包含end
if __name__ == '__main__':
    get_all_restaurants_info()