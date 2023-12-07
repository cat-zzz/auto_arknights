"""
@File   : match_img.py
@Desc   :
@Author : gql
@Date   : 2023/12/7 12:58
"""
from pathlib import Path

import cv2
import numpy


class Image:
    def __init__(self, image):
        self.image = cv2.imread(image, cv2.IMREAD_COLOR)
        # self.image = cv2.cvtColor(cv2.imread(image, cv2.IMREAD_UNCHANGED), cv2.COLOR_BGR2RGB)

    @property
    def width(self):
        return self.image.shape[1]

    @property
    def height(self):
        return self.image.shape[0]

    def clip(self, x1, y1, x2, y2):
        self.image = self.image[x1:y1, x2:y2]


class MatchImg(object):
    def __init__(self, source, template, similarity=0.80):
        """
        匹配一个图片是否是另一个图片的局部图。source是大图，template是小图。即判断小图是否是大图的一部分。
        :param similarity: 匹配程度，值越大，匹配程度越高
        """
        self.source_img = source
        self.template_img = template
        self.similarity = similarity

    def set_images(self, source, template):
        self.source_img = source
        self.template_img = template

    def match_template(self, method=cv2.TM_CCOEFF_NORMED):
        """
        返回小图左上角的点，在大图中的坐标。
        :param method:
        :return: list[tuple(x,y),...]
        """
        try:
            result = cv2.matchTemplate(self.source_img.image, self.template_img.image, method)
            locations = numpy.where(result >= self.similarity)
            res = list(zip(locations[1], locations[0]))  # 返回的是匹配到的template左上角那个坐标点在image中的位置，可能有多个值
            return res
        except cv2.error as e:
            print('error:', e)

    def get_template_position(self):
        """
        获取小图在大图中，左上角和右下角的坐标
        :return: List[list[x,y,x,y],...]
        """
        res = self.match_template()
        new_pos = []
        if res is not None:
            for r in res:
                r = list(r)
                r.append(r[0] + self.template_img.width)
                r.append(r[1] + self.template_img.height)
                new_pos.append(r)
        return new_pos

    def get_img_center(self):
        """
        获取大图中，每个小图中心点所在的坐标
        :return:
        """
        pos = self.match_template()
        points = []
        if pos is not None:
            for p in pos:
                x, y = p[0] + int(self.template_img.width / 2), p[1] + int(self.template_img.height / 2)
                points.append((x, y))
        return points


def load_image_file(path):
    path = Path(path)
    if not path.exists():
        print('load_image_file(): not exist file')

    try:
        image = Image(str(path))
        return image
    except cv2.error as e:
        print(e)
