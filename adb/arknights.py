import re
import subprocess
import time
from enum import Enum
from pathlib import Path
import numpy
import cv2


class AdbCmd:
    """
    将ADB命令封装成一个类，便于以后使用
    """

    def __init__(self):
        """初始化ADB,包括检查ADB是否正确安装，设备是否正确连接"""
        self.path = 'C:\\cplay\\LDPlayer9\\'
        version = subprocess.check_output(self.path + 'adb version')
        if 'Android Debug Bridge version' in str(version):
            print('ADB安装正常')
            devices = subprocess.check_output(self.path + 'adb devices')
            # devices=List of devices attached \r\nemulator-5556\tdevice\r\n\r\n
            if len(devices) > 28:
                print('设备', devices[27:-11].decode('UTF-8'), '加载成功')
            else:
                print('没有找到设备，请重新连接')
                exit(0)
        else:
            print('ADB没有正常加载，请检查环境变量或当前文件夹\n' + 'Error: ' + version)
        # subprocess.check_output('adb shell mkdir /sdcard/auto_arknights')

    def start_arknights(self):
        subprocess.check_output(
            self.path + 'adb shell monkey -p com.hypergryph.arknights -c android.intent.category.LAUNCHER 1'
        )

    def swipe(self, x1=500, y1=1200, x2=500, y2=600):
        """滑动屏幕"""
        subprocess.check_output(
            self.path + 'adb shell input swipe ' + str(x1) + ' ' + str(y1) + ' ' + str(x2) + ' ' + str(y2))

    def swipe_up(self):
        self.swipe(x1=500, y1=1200, x2=500, y2=600)

    def swipe_down(self):
        self.swipe(x1=500, y1=600, x2=500, y2=1200)

    def click_power(self):
        """点击电源键"""
        subprocess.check_output(self.path + 'adb shell input keyevent 26')

    def click(self, x, y):
        """点击屏幕中某个点"""
        subprocess.check_output(self.path + 'adb shell input tap ' + str(x) + ' ' + str(y))
        print('adbcmd: 模拟单击操作(' + str(x) + ', ' + str(y) + ')')

    def click_home(self):
        """点击Home键"""
        subprocess.check_output(self.path + 'adb shell input keyevent 3')

    def back(self):
        """点击返回键"""
        subprocess.check_output(self.path + 'adb shell input keyevent 4')

    def screen_capture_save(self, filename):
        # subprocess.check_output(self.path + 'adb exec-out screencap -p > C:\\sc.png')
        # subprocess.check_output(self.path + 'adb shell screencap -p /sdcard/auto_arknights/ark1.png')
        # subprocess.check_output(self.path + 'adb pull /sdcard/auto_arknights/ark1.png -p ' +
        #                         'C:\\Users\\catzzz\\Desktop\\ark1.png')
        # subprocess.check_output(self.path + 'adb shell screencap -p /sdcard/' + filename)
        # subprocess.check_output(self.path + 'adb pull /sdcard/' + filename + ' ./auto_arknights/' + filename)
        # subprocess.check_output(self.path + 'adb shell rm -f /sdcard/' + filename)
        subprocess.run(self.path + 'adb shell screencap -p /sdcard/' + filename, shell=True)
        subprocess.run(self.path + 'adb pull /sdcard/' + filename + ' ./auto_arknights/' + filename, shell=True)
        # subprocess.run(self.path + 'adb shell rm -f /sdcard/' + filename, shell=True)
        print('adbcmd: 截图操作')

    def get_screen_size(self):
        """
        获得屏幕的宽和高
        :return: (width, height)
        """
        # res=b'Physical size: 1600x900\r\n'
        res = str(subprocess.check_output(self.path + 'adb shell wm size'))
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
        print('not exist file')
    try:
        image = Image(str(path))
        return image
    except cv2.error as e:
        print(e)


class ActionType(Enum):
    NO_ACTION = 1
    CLICK = 2


class AutoArknights:
    def __init__(self):
        self.screen_path = './auto_arknights/'  # 保存匹配截图
        self.adb_cmd = AdbCmd()
        self.width, self.height = self.adb_cmd.get_screen_size()

    def enter_arknights(self):
        """
        启动明日方舟并进入到到主菜单
        """
        # 1 启动app
        # 通过包名的方式启动 Main Activity
        self.adb_cmd.start_arknights()
        time.sleep(3)
        # 2 进入主菜单
        i = 0
        while i < 100:  # 超时判断
            # 先截图
            ark2_file = 'ark2.png'
            ark2_2_file = 'ark2_2.png'
            self.adb_cmd.screen_capture_save(ark2_file)
            # 再检测
            src = load_image_file(self.screen_path + ark2_file)
            des = load_image_file(self.screen_path + ark2_2_file)
            process = MatchImg(src, des)
            points = process.get_img_center()  # src图片中每个des图片的中心坐标
            if points:
                self.adb_cmd.click(points[0][0], points[0][1])
                print('点击开始游戏')
                break
            else:
                self.adb_cmd.click(self.width / 2, self.height / 2)
            time.sleep(1)
            i += 1
        i = 0
        # 判断是否进入到主菜单
        while i < 100:
            ark2_file = 'ark3.png'
            ark2_2_file = 'ark3_2.png'
            self.adb_cmd.screen_capture_save(ark2_file)
            src = load_image_file(self.screen_path + ark2_file)
            des = load_image_file(self.screen_path + ark2_2_file)
            process = MatchImg(src, des)
            points = process.get_img_center()  # src图片中每个des图片的中心坐标
            if points:
                # self.adb_cmd.click(points[0][0], points[0][1])
                print('成功进入游戏主界面')
                break
            else:
                self.adb_cmd.click(self.width / 2, self.height / 2)
            time.sleep(1)
            i += 1

    def update_build(self, **kwargs):
        pass
        # points = kwargs['points']
        # print(points)
        # print(points[0][1], points[0][1])

    def update_build1(self):
        ark_img_name = 'ark4.png'
        ark_2_img_name = 'ark4_2.png'  # 基建小图标
        self.func1(ark_img_name, ark_2_img_name, ActionType.CLICK)  # 从主菜单进入基建
        # 判断是否已进入到基建
        ark_img_name = 'ark6.png'
        ark_2_img_name = 'ark6_2.png'
        flag = self.func1(ark_img_name, ark_2_img_name, ActionType.NO_ACTION)
        if not flag:  # 没有成功进入基建
            print('从主菜单进入基建失败')
            pass
        print('成功进入基建')
        # 领收益
        # 判断左上角有没有收益图标并点击
        ark_img_name = 'ark7.png'
        ark_2_img_name = 'ark7_2.png'
        flag = self.is_match_screen(ark_img_name, ark_2_img_name, ActionType.CLICK)
        if flag:  # 有图标，则需要领收益
            print('有收益图标')
            ark_img_name = 'ark7.png'
            ark_2_img_name = 'ark7_3.png'
            self.func2(ark_img_name, ark_2_img_name, ActionType.CLICK)
            print('制造站收取完成')
            ark_2_img_name = 'ark7_4.png'
            self.func2(ark_img_name, ark_2_img_name, ActionType.CLICK)
            print('贸易站收取完成')
            ark_2_img_name = 'ark7_5.png'
            self.func2(ark_img_name, ark_2_img_name, ActionType.CLICK)
            print('干员信赖收取完成')

    def func1(self, ark_img, ark_2_img, action: ActionType, is_default_click=False):
        """
        当满足在ark_img中含有图片ark_2_img时，执行action动作
        :param ark_img:
        :param ark_2_img:
        :param action 图片匹配之后要进行的动作
        :param is_default_click: 图片不匹配时，是否进行默认点击（点击屏幕中心点）
        :return 在100次循环之内匹配成功，则返回True；否则，返回False
        """
        i = 0
        while i < 100:
            # ark2_file = 'ark3.png'
            # ark2_2_file = 'ark3_2.png'
            self.adb_cmd.screen_capture_save(ark_img)
            src = load_image_file(self.screen_path + ark_img)
            des = load_image_file(self.screen_path + ark_2_img)
            process = MatchImg(src, des)
            points = process.get_img_center()  # src图片中每个des图片的中心坐标
            if points:
                # print('主框架代码')
                # func(points=points)
                if action == ActionType.CLICK:
                    self.adb_cmd.click(points[0][0], points[0][1])
                return True
            elif is_default_click:
                self.adb_cmd.click(self.width / 2, self.height / 2)
            time.sleep(1)
            i += 1
        return False

    def func2(self, ark_img, ark_2_img, action1: ActionType):
        """
        满足条件就一直执行action1，直到不满足条件为止
        :param ark_img:
        :param ark_2_img:
        :param action1:
        :return:
        """
        i = 0
        while i < 100:
            self.adb_cmd.screen_capture_save(ark_img)
            src = load_image_file(self.screen_path + ark_img)
            des = load_image_file(self.screen_path + ark_2_img)
            process = MatchImg(src, des)
            points = process.get_img_center()  # src图片中每个des图片的中心坐标
            if points is not None and len(points) > 0:
                if action1 == ActionType.CLICK:
                    self.adb_cmd.click(points[0][0], points[0][1])
            else:
                return True
            time.sleep(1)
            i += 1
        return False

    def func3(self, ark_img, ark_2_img, ark_3_img, ark_4_img, action1: ActionType, action2: ActionType):
        """
        1 满足条件就一直执行action1，直到不满足条件为止，不满足条件执行action2
        2 不满足条件就一直判断并执行action1，直到满足条件为止，且在满足条件时，执行一次action2
        此函数最多之能有三个条件
        :return:
        """
        self.adb_cmd.screen_capture_save(ark_img)  # 屏幕截图
        src = load_image_file(self.screen_path + ark_img)
        des = load_image_file(self.screen_path + ark_2_img)  # 匹配子图

    def is_match_screen(self, ark_img, ark_2_img, action1, action2=ActionType.NO_ACTION):
        """
        判断ark_img中是否含有ark_2_img，若有采取action1，否则采取action2
        :return:
        """
        self.adb_cmd.screen_capture_save(ark_img)
        src = load_image_file(self.screen_path + ark_img)
        des = load_image_file(self.screen_path + ark_2_img)
        process = MatchImg(src, des)
        points = process.get_img_center()  # src中每个des的中心坐标
        if points:
            if action1 == ActionType.CLICK:
                self.adb_cmd.click(points[0][0], points[0][1])
            return True
        else:
            if action2 == ActionType.CLICK:
                self.adb_cmd.click(points[0][0], points[0][1])
            return False


def auto_arknights():
    # adb截图
    # 匹配“开始游戏”的位置
    path = './auto_arknights/'
    # 1 打开ADB
    adb_cmd = AdbCmd()
    width, height = adb_cmd.get_screen_size()
    # 2 启动app
    # 通过包名的方式启动主Activity
    adb_cmd.start_arknights()
    # 2.2 等待8秒
    time.sleep(1)
    # 3 进入主菜单
    # 不断循环点击，通过不断截图判断是否进入到主菜单
    i = 0
    while i < 100:
        # 先截图
        ark2_file = 'ark2.png'
        ark2_2_file = 'ark2_2.png'
        adb_cmd.screen_capture_save(ark2_file)
        # 再检测
        src = load_image_file(path + ark2_file)
        des = load_image_file(path + ark2_2_file)
        process = MatchImg(src, des)
        points = process.get_img_center()
        if points:
            adb_cmd.click(points[0][0], points[0][1])
            break
        else:
            adb_cmd.click(width / 2, height / 2)
        time.sleep(1)
        i += 1


if __name__ == '__main__':
    auto = AutoArknights()
    auto.enter_arknights()
    auto.update_build1()

    # text = subprocess.check_output('C:\\cplay\\LDPlayer9\\adb devices')
    # print(text.decode('UTF-8'))
    # a = AdbCmd()
    #
    # img1 = load_image_file('C:\\Users\\catzzz\\Desktop\\11.png')
    # img2 = load_image_file('C:\\Users\\catzzz\\Desktop\\ark2_2.png')
    # process = MatchImg(img1, img2, 0.96)
    # points = process.get_img_center()
    # print(points)
    # a.click(points[0][0], points[0][1])
