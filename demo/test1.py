"""
@File   : test1.py
@Desc   :
@Author : gql
@Date   : 2023/12/2 11:33
"""
import pprint
import re
import parsel
import requests


def get_response(html_url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0'
    }
    response = requests.get(url=html_url, headers=headers)
    return response


def get_list_url(html_url):
    response = get_response(html_url)
    list_url = re.findall('<a title="(.*?)".*?href="(.*?)"', response.text)
    # print(list_url)
    return list_url


def get_music_id(html_url):
    """hash id"""
    response = get_response(html_url)
    Hash_list = re.findall('"Hash":"(.*?)"', response.text)
    album_id_list = re.findall('"album_id":(\d+)', response.text)
    music_id_list = zip(Hash_list, album_id_list)
    return music_id_list


def get_music_info(Hash, music_id):
    """list"""
    link_list = f'https://wwwapi.kugou.com//yy/index.php?r=play/getdata&hash={Hash}&dfid=08yHnP1NIxEY4F1hXr3wleBb&appid=1014&mid=bebaa22b82662cab54aa33fb486be51d&platid=4&album_id={music_id}&_=1639379015124'
    response = get_response(html_url=link_list)
    title = response.json()['data']['album_name']
    play_url = response.json()['data']['play_url']
    music_info = [title, play_url]
    # print(music_info)
    return music_info


def save(title, play_url):
    music_content = get_response(html_url=play_url).content
    with open("C:/musics/{}.mp3".format(title), mode='wb') as f:
        f.write(music_content)
        print(title, '保存成功')


def main(html_url):
    list_url = get_list_url(html_url=html_url)
    for list_name, link in list_url:
        print(f'-----------正在爬取{list_name}-------------------')
        music_id_list = get_music_id(html_url=link)
        for Hash, music_id in music_id_list:
            try:
                music_info = get_music_info(Hash, music_id)
                save(music_info[0], music_info[1])
            except Exception as e:
                pass
            continue


if __name__ == '__main__':
    url = 'https://www.kugou.com/yy/html/rank.html'
    main(url)
