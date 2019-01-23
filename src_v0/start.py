from time import sleep

import sys

from get_restaurants_info import get_restaurants_info_by_state
from get_restaurants_list import load_addresses, get_restaurants_page, save_addresses, get_restaurants_list, \
    get_restaurants_list_by_state
from utils import log

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
    loop = 5
    return_code = 0
    while loop > 0:
        return_code = get_restaurants_list_by_state(state)
        if return_code == 0:
            break
        else:
            loop -= 1
    loop = 5
    if return_code == -1:
        log('运行失败，查看日志')
    else:
        while loop > 0 and return_code == 0:
            return_code = get_restaurants_info_by_state(state, start, end)
            if return_code == 0:
                break
            else:
                loop -= 1
        if return_code == 0:
            log('运行结束')
        else:
            log('运行失败，查看日志')
