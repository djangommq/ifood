import json
import time
import traceback
import os

from selenium import webdriver

VERSION = '20180802'


def log(*args, **kwargs):
    # time.time() 返回 unix time
    # 如何把 unix time 转换为普通人类可以看懂的格式呢？
    format_str = '%Y/%m/%d %H:%M:%S'
    value = time.localtime(int(time.time()))
    dt = time.strftime(format_str, value)
    format_str2 = '%Y_%m_%d'
    date = time.strftime(format_str2, value)
    log_path = '../log/{}_log.txt'.format(date)
    log_dir = os.path.split(log_path)[0]
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    with open(log_path, 'a', encoding='utf-8') as f:
        print(dt, *args, file=f, **kwargs)


def save_file(data_input, file_path):
    try:
        tmp_dir = os.path.split(file_path)[0]
        if not os.path.exists(tmp_dir):
            os.makedirs(tmp_dir)
        with open(file_path, 'w', encoding='utf-8') as fw:
            s = json.dumps(data_input)
            fw.write(s)
            log('文件{}保存正常'.format(file_path))
    except Exception as e:
        log(e)
        log(traceback.format_exc())


def launch_driver():
    # Chrome配置
    # ===================================================================
    option = webdriver.ChromeOptions()
    option.add_argument('headless')
    prefs = {"profile.managed_default_content_settings.images": 2}
    option.add_experimental_option("prefs", prefs)

    driver = webdriver.Chrome(chrome_options=option)
    driver.implicitly_wait(10)
    # ===================================================================

    # Phantomjs配置
    # ===================================================================
    # driver = webdriver.PhantomJS()
    # dcap = dict(DesiredCapabilities.PHANTOMJS)
    # dcap["phantomjs.page.settings.userAgent"] = (
    #     'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)
    # Chrome/67.0.3396.99 Safari/537.36')
    # # 设置user-agent请求头
    # # SERVICE_ARGS = ['--load-images=false', '--disk-cache=true']
    # service_args = ['--ignore-ssl-errors=true']
    # # dcap["phantomjs.page.settings.loadImages"] = False  # 禁止加载图片
    # driver = webdriver.PhantomJS(
    #     desired_capabilities=dcap,
    #     service_args=service_args,
    # )
    # driver.set_page_load_timeout(40)
    # driver.set_window_size(1920, 1080)
    # ===================================================================
    return driver
