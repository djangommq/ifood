import os
import csv
import json
from utils import VERSION
from mongodb_utils import get_db

# 获取链接数据库的对象
c_mongo=get_db()

# 表名称
table_name=VERSION+'comment'

# 文件保存位置
filepath='../data/{}/comments/'.format(VERSION)

# 评论文件头
comments_header = [
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


if __name__ == '__main__':
    if not os.path.exists(filepath):
      os.makedirs(filepath)
    # 获取表中的所有数据信息
    data_dict=c_mongo.all_items(table_name)
    for data in data_dict:
      # 评论文件的文件名称
      comment_name=data['comment_name']
      print(comment_name)
      # 评论内容
      comment_str=data['comment_content']
      if comment_str=='[]':
        continue
      comment_content=json.loads(comment_str)
      # 评论文件的保存位置
      filename=filepath+comment_name
      # 创建文件保存目录
      if not os.path.exists(filepath):
          os.makedirs(filepath)
      with open(filename,'w',encoding='utf-8',newline='')as f:
        writer=csv.writer(f)
        writer.writerow(comments_header)
        for r in comment_content:
          writer.writerow(r)

