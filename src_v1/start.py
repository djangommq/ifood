import logging
import sys

from get_restaurants_info import get_restaurants_info_by_state
from get_restaurants_list import get_all_restaurants_list


if __name__ == '__main__':

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

    state = states.get(index)
    loop = 5
    return_code = 0
    while loop > 0:
        return_code = get_all_restaurants_list()
        if return_code == 0:
            break
        else:
            loop -= 1
    loop = 5
    if return_code == -1:
        logging.info('运行失败，查看日志')
    else:
        while loop > 0 and return_code == 0:
            return_code = get_restaurants_info_by_state(state, start, end)
            if return_code == 0:
                break
            else:
                loop -= 1
        if return_code == 0:
            logging.info('运行结束')
        else:
            logging.info('运行失败，查看日志')
