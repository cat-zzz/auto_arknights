"""
@File   : arknights2.py
@Desc   :
@Author : gql
@Date   : 2023/11/19 22:14
"""
import re
import subprocess
import time
from enum import Enum
from pathlib import Path

import cv2
import numpy


class AdbCmd:
    """
    将ADB命令封装成一个类，便于以后使用
    """

    def __init__(self, adb_path='C:\\cplay\\LDPlayer9\\'):
        """初始化ADB,包括检查ADB是否正确安装，设备是否正确连接"""
        self.adb_path = adb_path
        version = subprocess.check_output(self.adb_path + 'adb version')
        if 'Android Debug Bridge version' in str(version):
            print('ADB安装正常')
            devices = subprocess.check_output(self.adb_path + 'adb devices')
            # devices=List of devices attached \r\nemulator-5556\tdevice\r\n\r\n
            if len(devices) > 28:
                print('设备', devices[27:-11].decode('UTF-8'), '加载成功')
            else:
                print('没有找到设备，请重新连接')
                exit(0)
        else:
            print('ADB没有正常加载，请检查环境变量或当前文件夹\n' + 'Error: ' + version)

    def start_arknights(self):
        # 通过包名启动
        subprocess.check_output(
            self.adb_path + 'adb shell monkey -p com.hypergryph.arknights -c android.intent.category.LAUNCHER 1'
        )

    def swipe(self, x1=500, y1=1200, x2=500, y2=600):
        """滑动屏幕"""
        subprocess.check_output(
            self.adb_path + 'adb shell input swipe ' + str(x1) + ' ' + str(y1) + ' ' + str(x2) + ' ' + str(y2))

    def click_power(self):
        """点击电源键"""
        subprocess.check_output(self.adb_path + 'adb shell input keyevent 26')

    def click(self, x, y):
        """点击屏幕中某个点"""
        subprocess.check_output(self.adb_path + 'adb shell input tap ' + str(x) + ' ' + str(y))
        print('adbcmd: 点击操作(' + str(x) + ', ' + str(y) + ')')

    def back(self):
        """点击返回键"""
        subprocess.check_output(self.adb_path + 'adb shell input keyevent 4')

    def screen_capture_save(self, filename):
        # subprocess.check_output(self.path + 'adb exec-out screencap -p > C:\\sc.png')
        subprocess.run(self.adb_path + 'adb shell screencap -p /sdcard/' + filename, shell=True)
        subprocess.run(self.adb_path + 'adb pull /sdcard/' + filename + ' ./auto_arknights2/' + filename, shell=True)
        # subprocess.run(self.path + 'adb shell rm -f /sdcard/' + filename, shell=True)
        print('adbcmd: 截图操作')

    def get_screen_size(self):
        """
        获得屏幕的宽和高
        :return: (width, height)
        """
        # res=b'Physical size: 1600x900\r\n'
        res = str(subprocess.check_output(self.adb_path + 'adb shell wm size'))
        res = res[17:-5]
        res = re.split('x', res)
        try:
            width = int(res[0])
            height = int(res[1])
        except ValueError:
            width = 100
            height = 100
        return width, height


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
    def __init__(self, source=None, template=None, similarity=0.80):
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


class ActionType(Enum):
    NO_ACTION = 1
    CLICK = 2
    CLICK_CENTER = 3  # 点击屏幕中间


class AutoArknights:
    def __init__(self):
        self.save_screen_path = './auto_arknights2/'  # 保存匹配截图
        self.adb_cmd = AdbCmd()
        self.match_img = MatchImg()
        self.width, self.height = self.adb_cmd.get_screen_size()
        self.points = None

    class Flag(Enum):
        SATISFY_CONDITION = 1
        NO_SATISFY_CONDITION = 2

    def take_action(self, action: ActionType):
        if action == ActionType.CLICK:
            self.adb_cmd.click(self.points[0][0], self.points[0][1])
        elif action == ActionType.CLICK_CENTER:
            self.adb_cmd.click(self.width / 2, self.height / 2)
        else:
            pass

    def continue_action(self, src_path, des_path, action1=ActionType.NO_ACTION, action2=ActionType.NO_ACTION,
                        flag=Flag.SATISFY_CONDITION):
        """
        对应两种情况（通过flag标识是哪种情况）
        1 满足条件一直执行action1，直到不满足条件为止，且不满足条件时执行一次action2
        2 不满足条件一直执行action1，直到满足条件为止，且满足条件时执行一次action2
        :return: 无论flag取值如何，只要执行了一次action2，则返回True；否则返回False
        """
        i = 0
        while i < 100:  # 最多循环100次
            self.adb_cmd.screen_capture_save(src_path)
            is_match_flag = self.is_match(src_path, des_path)
            if flag == self.Flag.SATISFY_CONDITION:
                if is_match_flag:
                    self.take_action(action1)
                else:
                    self.take_action(action2)
                    return True
            elif flag == self.Flag.NO_SATISFY_CONDITION:
                if not is_match_flag:
                    self.take_action(action1)
                else:
                    self.take_action(action2)
                    return True
            else:
                pass
            time.sleep(1)
            i += 1
        return False

    def continue_several_action(self, src_path, des_path, cond_paths, des_action=ActionType.NO_ACTION,
                                cond_action=ActionType.CLICK, default_action=ActionType.NO_ACTION):
        """
        如果和目标(des)匹配，则执行完毕（只有这一种情况函数才会执行完成，其他情况都会一直循环判断）
        否则，判断和哪个条件匹配，就执行该条件对应的动作，此时仍会继续循环判断
        如果都不符合，执行默认动作
        :return: 循环判断100次(每次间隔1秒)，其中一旦和目标匹配，返回True；否则，返回False
        """

        i = 0
        while i < 100:
            self.adb_cmd.screen_capture_save(src_path)
            is_match_flag = self.is_match(src_path, des_path)
            if is_match_flag:  # 判断和目标des_path是否匹配
                self.take_action(des_action)
                return True
            else:
                cond_flag = 0
                # 依次判断和cond_paths里的条件是否符合，如果有多个符合的条件，只会执行最靠前的那个条件
                for j, cond_path in enumerate(cond_paths):
                    is_match_flag = self.is_match(src_path, cond_path)
                    if is_match_flag:
                        self.take_action(cond_action)
                        cond_flag = 1
                        break
                # 和cond_paths里的任一条件都不符合，则执行默认动作
                if cond_flag == 0:
                    self.take_action(default_action)
            time.sleep(1)
            i += 1
        return False

    def is_match(self, src_path, des_path):
        src = load_image_file(self.save_screen_path + src_path)
        des = load_image_file(self.save_screen_path + des_path)
        self.match_img.set_images(src, des)
        self.points = self.match_img.get_img_center()
        if self.points is not None and len(self.points) > 0:
            return True
        else:
            return False

    def enter_game(self):
        # 1 启动app
        self.adb_cmd.start_arknights()
        print('启动明日方舟')
        time.sleep(3)
        # 2 进入主菜单
        # 2.1 点击”开始唤醒“
        src = 'ark_start_btn_1.png'
        des = 'ark_btn_start.png'
        self.continue_action(src, des, action1=ActionType.CLICK_CENTER, action2=ActionType.CLICK,
                             flag=self.Flag.NO_SATISFY_CONDITION)
        print('点击‘开始唤醒’按钮')
        # 2.2 判断是否成功进入主菜单，并关闭签到页、活动页
        src = 'ark_home_1.png'
        des = 'ark_tmpl_home.png'
        cond = ['ark_btn_quit.png']
        self.continue_several_action(src, des, cond)
        print('成功进入主菜单')

    def update_build(self):
        """
        从主菜单页面进入基建并更换干员，但是只能从主菜单进入基建
        """
        print('正在从主菜单进入基建...')
        src = 'ark_build.png'
        des = 'ark_tmpl_build.png'
        cond = ['ark_btn_build.png']
        flag = self.continue_several_action(src, des, cond)
        if not flag:
            print('进入基建失败')
            return
        print('成功进入基建')
        # 领收益
        src = 'ark_build_reward.png'
        des = 'ark_btn_build_notification.png'
        self.adb_cmd.screen_capture_save(src)
        flag = self.is_match(src, des)
        if flag:
            print('有基建通知图标')
            des = 'ark_btn_make.png'
            self.continue_action(src, des, action1=ActionType.CLICK, flag=self.Flag.SATISFY_CONDITION)
            print('制造站收取完成')
            des = 'ark_btn_trade.png'
            self.continue_action(src, des, action1=ActionType.CLICK, flag=self.Flag.SATISFY_CONDITION)
            print('贸易站收取完成')
            des = 'ark_btn_trust.png'
            self.continue_action(src, des, action1=ActionType.CLICK, flag=self.Flag.SATISFY_CONDITION)
            print('干员信赖收取完成')
        else:
            print('无基建通知图标')
        # todo 更换干员
        print('正在更换干员')

    def main(self):
        pass


def return_home():
    pass


if __name__ == '__main__':
    auto = AutoArknights()
    auto.enter_game()
    # print(auto.is_match('ark_home_1.png', 'ark_btn_quit.png'))
    # load_image_file('./auto_arknights2/ark_home.png')
    # a = [1, 1, 1, 1, 1]
    # j = 1
    # for j, v in enumerate(a):
    #     print(j, v)
    # print('j', j)
