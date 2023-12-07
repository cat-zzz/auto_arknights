import re

import pymysql
import requests


def get_response(html_url):
    """
    发起请求得到响应体，请求地址为html_url
    """
    # 伪造请求头，主要是伪造User-Agent
    # 固定写法
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:43.0) Gecko/20100101 Firefox/43.0'
    }
    # 通过requests模块发送get请求，得到响应结果response
    response = requests.get(url=html_url, headers=headers)
    return response


def get_list_url(html_url):
    """
    获取所有榜单的url，存储为list形式
    """
    response = get_response(html_url=html_url)  # 发起请求
    # 检索出所有榜单的url
    list_url = re.findall('<a title="(.*?)".*?href="(.*?)"', response.text)  # re是正则表达式模块
    return list_url


def get_music_id(html_url):
    """
    获取当前榜单（html_url）中所有歌曲的hash和album_id，并打包成一个list
    """
    response = get_response(html_url)
    # 此处代码可以根据具体的网页内容理解
    hash_list = re.findall('"Hash":"(.*?)"', response.text)
    album_id_list = re.findall('"album_id":(\d+)', response.text)
    music_id_list = zip(hash_list, album_id_list)  # 将两个list压缩为一个list
    return music_id_list


def get_music_info(Hash, music_id):
    """
    获取单首歌曲的相关信息
    """
    # link_list示例：https://wwwapi.kugou.com//yy/index.php?r=play/getdata&hash=7daec71a5878a5f2788d431abde79783&dfid=08yHnP1NIxEY4F1hXr3wleBb&appid=1014&mid=bebaa22b82662cab54aa33fb486be51d&platid=4&album_id=80299950&_=1639379015124
    music_info_url = f'https://wwwapi.kugou.com//yy/index.php?r=play/getdata&hash={Hash}&dfid=08yHnP1NIxEY4F1hXr3wleBb&appid=1014&mid=bebaa22b82662cab54aa33fb486be51d&platid=4&album_id={music_id}&_=1639379015124'
    response = get_response(music_info_url)
    title = response.json()['data']['album_name']  # 格式为”歌曲名-作者名
    play_url = response.json()['data']['play_url']  # 下载歌曲的url
    music_name = response.json()['data']['song_name']  # 歌曲名
    author_name = response.json()['data']['author_name']  # 作者名
    album_name = response.json()['data']['album_name']  # 专辑名
    music_img_url = response.json()['data']['img']  # 歌曲封面的url
    timelength = response.json()['data']['timelength']  # 歌曲时长（以毫秒为单位）
    try:
        duration = int(timelength)  # 歌曲时长，单位为秒
        duration /= 1000  # timelength以毫秒为单位，我们精确到秒即可
    except Exception as e:
        print('歌曲时长信息处理出错', e)
        duration = 0
    # 将歌曲相关信息封装为一个list
    music_info = [title, play_url, music_name, author_name, album_name, music_img_url, duration]
    return music_info


def save_to_mysql(music_name, author_name, album_name, play_url, music_img_url, duration):
    """
    执行 插入歌曲相关信息的 sql
    """
    # 构建sql语句
    sql = f"insert into music_info(music_name,author_name,album_name,play_url,music_img_url,duration) " \
          f"values ('{music_name}','{author_name}','{album_name}','{play_url}','{music_img_url}','{duration}')"
    try:
        # 执行sql语句
        print('sql', sql)
        cursor.execute(sql)
        # 提交
        db.commit()
        print("sql执行成功")
    except Exception as e:
        # sql执行失败时回滚
        db.rollback()
        print("sql执行失败", e)


def save_to_dict(title, play_url):
    """
    将歌曲保存到磁盘
    """
    music_content = get_response(html_url=play_url).content
    with open("C:/musics/{}.mp3".format(title), mode='wb') as f:
        f.write(music_content)
        print(title, '保存成功')


def main(html_url):
    list_url = get_list_url(html_url=html_url)
    # 遍历所有的榜单
    for list_name, link in list_url:
        print(f'-----------正在爬取{list_name}-------------------')
        # 获取当前榜单中的所有歌曲
        music_id_list = get_music_id(html_url=link)
        # 遍历当前榜单中的所有歌曲
        for Hash, music_id in music_id_list:
            try:
                # 获取歌曲相关信息
                music_info = get_music_info(Hash, music_id)
                # 歌曲相关信息保存到数据库
                save_to_mysql(music_info[2], music_info[3], music_info[4], music_info[1], music_info[5], music_info[6])
                # 歌曲保存到磁盘
                save_to_dict(music_info[0], music_info[1])
            except Exception as e:
                # 异常处理，此处只是简单输出一下
                print(e)


# 数据库连接配置信息
config = {
    "host": "127.0.0.1",
    "user": "root",
    "password": "2281498",
    "database": "music_system"
}
# 连接数据库
db = pymysql.connect(**config)
# 创建指针，通过该指针执行sql语句
cursor = db.cursor()

if __name__ == '__main__':
    url = 'https://www.kugou.com/yy/html/rank.html'  # 总榜单url
    main(url)
