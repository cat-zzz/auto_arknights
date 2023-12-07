"""
@File   : test2.py
@Desc   :
@Author : gql
@Date   : 2023/12/2 11:45
"""
import requests
import re
import time


def get_response(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:43.0) Gecko/20100101 Firefox/43.0'
    }
    response = requests.get(url=url, headers=headers)
    return response


def get_list_url(url):
    response = get_response(url)
    list_url = re.findall('<a title="(.*?)".*?href="(.*?)"', response.text)
    return list_url


def get_music_id(url):
    response = get_response(url)
    Hash_list = re.findall('"Hash":"(.*?)"', response.text)
    album_id_list = re.findall('"album_id":(\d+)', response.text)
    music_id_list = zip(Hash_list, album_id_list)
    return music_id_list


def get_music_info(Hash, music_id):
    """list"""
    link_list = f'https://wwwapi.kugou.com/yy/index.php?r=play/getdata&amp;hash={Hash}&amp;dfid=3ex60E2pQb582fRAwB1wYhA1&amp;appid=1014&amp;mid=94c23e6bf948c957d06d24c4dec18b1e&amp;platid=4&amp;album_id={music_id}&amp;_=1695860308340'
    response = get_response(url=link_list)
    title = response.json()['data']['album_name']
    play_url = response.json()['data']['play_url']
    music_info = [title, play_url]
    # print(music_info)
    return music_info


def save(title, play_url):
    music_content = get_response(url=play_url).content
    with open("C:/musics/{}.mp3".format(title), mode='wb') as f:
        f.write(music_content)
        print(title, '保存成功')
        print('*' * 20)


def main(url):
    music_id_list = get_music_id(url=url)
    for Hash, music_id in music_id_list:
        try:
            music_info = get_music_info(Hash, music_id)
            save(music_info[0], music_info[1])
        except Exception as e:
            pass
        continue


if __name__ == '__main__':
    url = 'https://www.kugou.com/yy/rank/home/1-8888.html?from=rank'
    url1 = 'https://www.kugou.com/yy/html/rank.html'
    main(url)
    time.sleep(2)
