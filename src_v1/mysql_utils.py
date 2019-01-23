import datetime
import os
import pymysql
import logging
"""
1. 要保证有数据库
2. 可以自动创建不存在的表

"""


class Mysql(object):

    # 初始化
    def __init__(self, dbconfig):
        self.host = dbconfig.get('host')
        self.port = dbconfig.get('port')
        self.user = dbconfig.get('user')
        self.password = dbconfig.get('password')
        self.database = dbconfig.get('database')
        self.charset = dbconfig.get('charset')
        self.cursorclass = dbconfig.get('cursorclass')
        self._conn = None
        self._createdb(self.database)
        self._connect()
        self._cursor = self._conn.cursor()

    # 判断数据库是否存在, 不存在自动创建
    def _createdb(self, database):
        self._conn = pymysql.connect(host=self.host, port=self.port,
                                     user=self.user, password=self.password,
                                     cursorclass=self.cursorclass,
                                     )
        self._cursor = self._conn.cursor()
        try:
            self._cursor.execute('create database if not exists {}'.format(database))
        except pymysql.Error as e:
            logging.error('数据库已经存在')

    # 链接数据库
    def _connect(self):
        try:
            self._conn = pymysql.connect(host=self.host, port=self.port,
                                         user=self.user, password=self.password,
                                         database=self.database, cursorclass=self.cursorclass,
                                         )
        except pymysql.Error as e:
            logging.error(e)

    # 执行查询
    def query(self, sql):
        try:
            result = self._cursor.execute(sql)
        except pymysql.Error as e:
            result = None
            logging.error(e)
        return result

    # 选择
    def select(self, table, column='*', condition=''):
        if condition != '':
            condition = 'where {}'.format(condition)
        sql = 'select {} from {} {}'.format(column, table, condition)
        logging.debug(sql)
        self.query(sql)
        return self._cursor.fetchall()

    # 插入
    def insert(self, table, data):
        column = ''
        value = ''
        for k, v in data.items():
            column += ',{}'.format(k)
            value = value + ',"{}"'.format(v)
        column = column[1:]
        value = value[1:]
        sql = "insert ignore into {} ({}) values ({})".format(table, column, value)
        logging.debug(sql)
        self._cursor.execute(sql)
        self._conn.commit()
        return self._cursor.lastrowid  # 返回最后一行的id

    # 修改
    def update(self, table, data, condition=''):
        if condition == '':
            logging.debug('更改时错误, 没有提供condition')
        else:
            condition = 'where {}'.format(condition)
        value = ''
        for k, v in data.items():
            value += ',{}="{}"'.format(k, v)
        value = value[1:]
        sql = 'update {} set {} {}'.format(table, value, condition)
        logging.debug(sql)
        self._cursor.execute(sql)
        self._conn.commit()
        return self._cursor.rowcount  # 返回更新的行数

    # 删除
    def delete(self, table, condition=''):
        if condition != '':
            condition = 'where {}'.format(condition)
        sql = 'delete from {} {}'.format(table, condition)
        self._cursor.execute(sql)
        self._conn.commit()
        return self._cursor.rowcount

    # rollback 回滚
    def rollback(self):
        self._conn.rollback()

    def __del__(self):
        try:
            self._cursor.close()
            self._conn.close()
        except pymysql.Error as e:
            logging.error(e)

    def close(self):
        self.__del__()


def test():
    dbconfig = {
        'host': 'localhost',
        "port": 3306,
        'user': 'root',
        'password': '',
        'database': 'military',
        'charset': 'utf-8',
    }

    db = Mysql(dbconfig)
    result = db.select('weapon01', '*', '')
    # result type: tuple
    # 返回的是一个tuple, 内部也是tuple
    for row in result:
        print(row)
        # (1, 'AS34/鸬鹚', 'missile', '导弹武器', '舰舰导弹', 'http://weapon.huanqiu.com/as34', '1532437411')
        print(type(row))
        # <class 'tuple'>
        print(row[0])
        # 1
        break


if __name__ == '__main__':
    test()
