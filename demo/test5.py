"""
@File   : test5.py
@Desc   :
@Author : gql
@Date   : 2023/12/2 18:47
"""
import re

import requests
import json

# url = 'http://www.kuwo.cn/api/v1/www/music/playUrl?mid=198554068&type=music&httpsStatus=1&reqId=57fac750-d685-11ec-a7b9-235918cfe32e'
url = 'https://lx-sycdn.kuwo.cn/0012c4f7cf7d59556554e7f1c5e0500b/656b0a2b/resource/n1/83/71/2375904687.mp3'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36'
}
# r = requests.get(url=url, headers=headers).text
# b = json.loads(r)
# music_url = b['data']['url']  # 获取音乐链接
music_url = 'https://lx-sycdn.kuwo.cn/0012c4f7cf7d59556554e7f1c5e0500b/656b0a2b/resource/n1/83/71/2375904687.mp3'
r1 = requests.get(url=music_url, headers=headers).content
with open('C:/musics/孤勇者.mp3', 'wb') as f:
    f.write(r1)
    print("音乐下载成功！")

def get_response(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:43.0) Gecko/20100101 Firefox/43.0'
    }
    response = requests.get(url=url, headers=headers)  # 需要伪造请求头
    return response

def get_list_url(url):
    response = get_response(url)
    list_url = re.findall('<a title="(.*?)".*?href="(.*?)"', response.text)
    return list_url