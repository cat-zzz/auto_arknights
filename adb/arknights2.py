"""
@File   : arknights2.py
@Desc   :
@Author : gql
@Date   : 2023/11/19 22:14
"""
import math
import re
import subprocess
import time
from enum import Enum

from easyocr import easyocr

from adb import util
from adb.adbcmd import AdbCmd
from adb.match_img import MatchImg, load_image_file


class ActionType(Enum):
    NO_ACTION = 1
    CLICK = 2
    CLICK_CENTER = 3  # 点击整个屏幕中间
    CLICK_LAST = 4  # 点击self.points最后一个位置坐标
    SWIPE_LAST_TO_FIRST = 5
    CLICK_1TH_3RD = 6  # 点击整个屏幕中间偏上1/3的地方


class AutoArknights:
    def __init__(self, is_use_ocr=True):
        print('init():')
        self.simulator_name = 'Leidian-Arknights'
        self.save_screen_path = './auto_arknights2/'  # 保存匹配截图
        self.adb_path = 'C:\\cplay\\LDPlayer9\\'
        self.adb_cmd = AdbCmd()
        src = load_image_file(self.save_screen_path + 'ark.png')
        tmpl = load_image_file(self.save_screen_path + 'ark_tmpl.png')
        self.match_img = MatchImg(src, tmpl)
        self.width, self.height = 0, 0
        self.points = None
        if is_use_ocr:
            self.reader = easyocr.Reader(['ch_sim', 'en'], gpu=False)
            print('EasyOCR启动成功')
        else:
            self.reader = None
            print('未使用EasyOCR')
        self.start_simulator()

    class Flag(Enum):
        SATISFY_CONDITION = 1
        NO_SATISFY_CONDITION = 2

    def take_action(self, action: ActionType):
        if action == ActionType.CLICK:
            self.adb_cmd.click(self.points[0][0], self.points[0][1])
        elif action == ActionType.CLICK_CENTER:
            self.adb_cmd.click(self.width / 2, self.height / 2)
        elif action == ActionType.CLICK_LAST:
            self.adb_cmd.click(self.points[-1][0], self.points[-1][1])
        elif action == ActionType.SWIPE_LAST_TO_FIRST:
            x1, y1, x2, y2 = self.points[0][0], self.points[0][1], self.points[-1][0], self.points[-1][1]
            self.adb_cmd.swipe(x2, y2, x1, y1)
        elif action == ActionType.CLICK_1TH_3RD:
            self.adb_cmd.click(self.width / 2, self.height / 3)
        else:
            pass

    def simply_points(self):
        # 通过is_match()函数得到的self.points有许多重复的、类似的结果，此函数用于简化self.points
        if self.points is None or len(self.points) <= 2:
            return False  # self.points为空或长度小于2，则不简化，返回False
        points = self.points[:]
        j = points[0]
        # 遍历拷贝的列表，删除原列表
        for i in points[1:]:
            if math.fabs(i[0] - j[0]) <= 3 and math.fabs(i[1] - j[1]) <= 3:
                self.points.remove(i)
            else:
                j = i

    def is_match(self, src_path, des_path):
        """
        截图并判断是否匹配
        note: 会同步更改self.points的值
        :return 匹配成功返回1，失败返回0，有网络不佳的提示返回-1
        """
        self.adb_cmd.screen_capture_save(src_path)
        src = load_image_file(self.save_screen_path + src_path)
        des = load_image_file(self.save_screen_path + des_path)
        self.match_img.set_images(src, des)
        self.points = self.match_img.get_img_center()
        self.simply_points()
        if self.points is not None and len(self.points) > 0:
            return 1
        elif util.ocr_poor_network_hint(self.reader, self.save_screen_path + src_path):
            return -1
        else:
            return 0

    class MatchTmpl(enumerate):
        HOME_PAGE = 1  # 主菜单首页
        BUILD_HOME_PAGE = 2  # 基建首页
        GARRISON_HERO_PAGE = 3  # 进驻干员总览页

    def match_tmpl(self, src_path):
        """
        判断src图片与哪张模板图片匹配（即判断src处于哪个页面中）
        :param src_path:
        :return:
        """
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

    def continue_several_cond_actions(self, src_path, des_path, cond_paths, des_action, cond_actions,
                                      default_action=ActionType.NO_ACTION):
        """
        src_path如果和目标(des_path)匹配，则执行完毕（只有这一种情况函数才会执行完成，其他情况都会一直循环判断）
        否则，判断和哪个条件(cond_paths)匹配，就执行该条件对应的动作，此时仍会继续循环判断
        如果都不符合，执行默认动作(default_action)
        :return: 循环判断100次(每次间隔1秒)，一旦和目标匹配，返回True；否则，循环结束后返回False
        """
        i = 0
        while i < 100:
            is_match_flag = self.is_match(src_path, des_path)
            if is_match_flag:  # 判断和目标des_path是否匹配
                self.take_action(des_action)
                return True
            else:
                cond_flag = 0
                # 依次判断和cond_paths里的条件是否符合，如果有多个符合的条件，只会执行最靠前的那个条件7
                for j, cond_path in enumerate(cond_paths):
                    is_match_flag = self.is_match(src_path, cond_path)
                    if is_match_flag:
                        self.take_action(cond_actions[j])
                        cond_flag = 1
                        break
                # 和cond_paths里的任一条件都不符合，则执行默认动作
                if cond_flag == 0:
                    self.take_action(default_action)
            time.sleep(1)
            i += 1
        return False

    def continue_serval_des_and_cond_actions(self, src_path, des_paths, cond_paths, des_actions, cond_actions,
                                             default_action=ActionType.NO_ACTION):
        """
        src_path如果和目标(des_paths)其中任一一个匹配，则执行完毕（只有这一种情况函数才会执行完成，其他情况都会一直循环判断）
        否则，判断和哪个条件匹配，就执行该条件对应的动作，此时仍会继续循环判断
        如果都不符合，执行默认动作(default_action)
        :return: 循环判断100次(每次间隔1秒)，一旦和目标其中之一匹配，返回对应的索引；否则，循环结束后返回-1
        """
        i = 0
        while i < 100:
            for j, cond_path in enumerate(des_paths):
                is_match_flag = self.is_match(src_path, cond_path)
                if is_match_flag:  # 判断和目标des_path是否匹配
                    self.take_action(des_actions[j])
                    return j
            cond_flag = 0
            # 依次判断和cond_paths里的条件是否符合，如果有多个符合的条件，只会执行最靠前的那个条件
            for j, cond_path in enumerate(cond_paths):
                is_match_flag = self.is_match(src_path, cond_path)
                if is_match_flag:
                    self.take_action(cond_actions[j])
                    cond_flag = 1
                    break
            # 和cond_paths里的任一条件都不符合，则执行默认动作
            if cond_flag == 0:
                self.take_action(default_action)
            time.sleep(1)
            i += 1
        return -1

    def start_simulator(self, index=1):
        """
        启动雷电模拟器
        :param index: 模拟器索引序号
        """
        print('--------start_simulator()--------')
        subprocess.check_output(self.adb_path + 'ldconsole launch --index ' + str(index))  # 启动雷电模拟器的指令
        i = 0
        while i < 100:
            # result格式
            # 0,Leidian,0,0,0,-1,-1,1600,900,240
            # 1,Leidian-Arknights,1379204,6293428,1,18244,20288,1600,900,240
            result = subprocess.check_output(self.adb_path + 'ldconsole list2').decode('utf-8')
            split = re.split(',', result)
            a = split[split.index(self.simulator_name) + 3]  # 模拟器状态
            if a == '1':
                break
            time.sleep(0.5)
            i += 1
        if i > 0:  # i==0说明模拟器已经启动成功，此时不用进行等待
            time.sleep(5)  # 需要等模拟器先加载一会，不然程序会提示“找不到设备”
        print('模拟器启动成功')
        # 有bug
        self.width, self.height = self.adb_cmd.get_screen_size()  # 获取模拟器屏幕尺寸
        print('---------------------------------')

    def enter_game(self):
        print('--------enter_game()--------')
        # 1 启动app
        self.adb_cmd.start_arknights()
        print('启动明日方舟')
        # 2 进入主菜单
        # 2.1 点击”开始唤醒“
        src = 'ark_start_btn_1.png'
        des = ['ark_btn_start.png', 'ark_tmpl_home.png']
        cond = []
        des_actions = [ActionType.CLICK, ActionType.NO_ACTION]
        cond_actions = []
        flag = self.continue_serval_des_and_cond_actions(src, des, cond, des_actions=des_actions,
                                                         cond_actions=cond_actions,
                                                         default_action=ActionType.CLICK_CENTER)
        # todo 进入签到页之前，会有一小段时间的延迟，如果在延迟这段时间截图，则会误认为已经进入到主菜单
        if flag == 1:
            # 延迟两秒后再次截图，判断这次截图是否还是在主菜单页面
            time.sleep(2)
            des = 'ark_tmpl_home.png'
            if self.is_match(src, des):
                return
        # 2.2 判断是否成功进入主菜单，并关闭签到页、活动页
        src = 'ark_home_1.png'
        des = 'ark_tmpl_home.png'
        cond = ['ark_btn_quit.png']
        cond_action = [ActionType.CLICK]
        self.continue_several_cond_actions(src, des, cond, des_action=ActionType.NO_ACTION,
                                           cond_actions=cond_action, default_action=ActionType.CLICK_1TH_3RD)
        print('成功进入主菜单')
        print('----------------------------')

    def enter_build(self):
        """
        从主菜单页面进入基建并收取奖励
        """
        print('--------enter_build--------')
        print('正在从主菜单进入基建...')
        src = 'ark_build.png'
        des = 'ark_tmpl_build.png'
        cond = ['ark_btn_build.png']
        cond_action = [ActionType.CLICK]
        flag = self.continue_several_cond_actions(src, des, cond, des_action=ActionType.NO_ACTION,
                                                  cond_actions=cond_action)
        if not flag:
            print('进入基建失败')
            return
        print('已成功进入基建')
        # 领收益
        src = 'ark_build_reward.png'
        des = 'ark_btn_build_notice.png'
        flag = self.is_match(src, des)
        if flag:
            print('有基建通知图标')
            self.take_action(ActionType.CLICK)
            des = 'ark_btn_make.png'
            self.continue_action(src, des, action1=ActionType.CLICK, flag=self.Flag.SATISFY_CONDITION)
            print('制造站收取完成')
            des = 'ark_btn_trade.png'
            self.continue_action(src, des, action1=ActionType.CLICK, flag=self.Flag.SATISFY_CONDITION)
            print('贸易站收取完成')
            des = 'ark_btn_trust.png'
            self.continue_action(src, des, action1=ActionType.CLICK, flag=self.Flag.SATISFY_CONDITION)
            print('干员信赖收取完成')
            des = 'ark_btn_build_notice_2.png'
            flag = self.is_match(src, des)
            if flag:
                time.sleep(3)
                self.take_action(ActionType.CLICK)
                print('退出收取基建奖励')
        else:
            print('无基建通知图标')
        print('---------------------------')

    def update_all_builds_hero(self):
        print('----update_all_builds_hero()----')
        print('正在进入(基建内)干员总览页面')
        # src = 'ark_build.png'
        # des = 'ark_btn_build_hero.png'
        # self.continue_action(src, des, action2=ActionType.CLICK, flag=self.Flag.NO_SATISFY_CONDITION)
        src = 'ark_build.png'
        des = 'ark_tmpl_garrison_hero.png'
        des_action = ActionType.NO_ACTION
        cond = ['ark_tmpl_build.png', 'ark_btn_build_notice_2.png', 'ark_btn_build_notice.png']
        cond_actions = [ActionType.CLICK, ActionType.CLICK, ActionType.NO_ACTION]
        self.continue_several_cond_actions(src, des, cond, des_action, cond_actions)
        print('成功进入(基建内)干员总览页面')
        self.remove_all_builds_hero()
        # print('正在撤下干员')
        # src = 'ark_build_hero.png'
        # des = 'ark_btn_build_hero_remove.png'
        # # 点击撤下干员按钮
        # self.continue_action(src, des, action2=ActionType.CLICK, flag=self.Flag.NO_SATISFY_CONDITION)
        # # 撤下干员
        # des = 'ark_btn_build_hero_remove_2.png'
        # self.is_match(src, des)
        # points = self.points[0::len(self.points) - 1]  # 浅拷贝
        # self.remove_last_build_hero()   # 第一次只需撤下最后一个
        # j = 0
        # while j < 6:  # 滑动6次即可撤下全部干员
        #     self.points = points[:]  # 浅拷贝
        #     self.take_action(ActionType.SWIPE_LAST_TO_FIRST)
        #     print(f'第{j}次滑动')
        #     time.sleep(0.3)
        #     self.is_match(src, des)
        #     points = self.points[:]
        #     while self.points is not None and len(self.points) > 0:
        #         self.remove_last_build_hero()
        #         self.points = self.points[0: -1]
        #         # self.points.pop()
        #     j += 1
        # # 点击取消撤下干员按钮
        # des = 'ark_btn_cancel_remove_build_hero.png'
        # self.continue_action(src, des, action2=ActionType.CLICK, flag=self.Flag.NO_SATISFY_CONDITION)
        # print('取消撤下干员')
        # todo 更换新干员
        print('---------------------------')

    def remove_all_builds_hero(self):
        """
        在进驻总览页面撤下干员，仅撤下干员而不更换新干员（只能从头撤到尾）
        """
        print('----remove_all_builds_hero()----')
        src = 'ark_build_hero.png'
        des = 'ark_btn_build_hero_remove.png'
        # 点击撤下干员按钮
        self.continue_action(src, des, action2=ActionType.CLICK, flag=self.Flag.NO_SATISFY_CONDITION)
        print('正在撤下干员')
        # 撤下所有建筑干员
        des = 'ark_btn_build_hero_remove_2.png'
        self.is_match(src, des)
        points = self.points[0::len(self.points) - 1]  # 浅拷贝
        self.remove_last_build_hero()  # 第一次只需撤下最后一个建筑的干员
        j = 0
        while j < 6:  # 滑动6次即可撤下全部干员
            self.points = points[:]  # 浅拷贝
            self.take_action(ActionType.SWIPE_LAST_TO_FIRST)
            print(f'第{j}次滑动')
            time.sleep(0.3)
            self.is_match(src, des)
            points = self.points[:]
            while self.points is not None and len(self.points) > 0:
                self.remove_last_build_hero()
                self.points = self.points[0: -1]
                # self.points.pop()
            j += 1
        # 点击取消撤下干员按钮
        des = 'ark_btn_cancel_remove_build_hero.png'
        self.continue_action(src, des, action2=ActionType.CLICK, flag=self.Flag.NO_SATISFY_CONDITION)
        print('所有干员均已撤下')

    def remove_last_build_hero(self):
        """
        点击匹配的最后一个撤下干员按钮。不会重新调用is_match()再匹配一遍，而是直接点击self.points的最后一个坐标
        :return:
        """
        src = 'ark_build_hero.png'
        if self.points is None or len(self.points) == 0:
            return
        self.take_action(ActionType.CLICK_LAST)
        time.sleep(1)  # 可能会出现网络不好的情况
        while util.ocr_poor_network_hint(self.reader, self.save_screen_path + src):
            # todo 出现’正在提交反馈至神经‘的提示，说明网络状况不好，此时不断循环截图、判断，直到此提示消失
            pass
        points = self.points  # 在self.is_match()那里，self.points可能会改变，需要提前保存个副本
        des = 'ark_btn_confirm.png'
        # 处理”确认换下“弹框
        flag = self.is_match(src, des)
        if flag:
            print('干员正在工作，确认换下')
            self.continue_action(src, des, ActionType.CLICK, ActionType.NO_ACTION)
        self.points = points
        pass

    def add_single_build_hero(self):
        """
        更新单个建筑内的干员
        """
        print('----update_one_build_hero()----')
        src = 'ark_update_one_build_hero.png'
        des_paths = ['ark_btn_update_1_hero.png', 'ark_btn_update_3_heroes.png', 'ark_btn_update_5_heroes.png']
        des_actions = [ActionType.CLICK, ActionType.CLICK, ActionType.CLICK]
        cond_paths = []
        cond_actions = []
        # 进入更换干员详情页
        flag = self.continue_serval_des_and_cond_actions(src, des_paths, cond_paths, des_actions, cond_actions)
        print('flag:', flag)
        print('成功进入干员选择页面')
        time.sleep(1)
        # 选择新干员
        # todo 当只有一个干员时，没有”清空选择“按钮
        src = 'ark_1.png'
        des = 'ark_btn_update_build_hero_detail_1.png'
        self.is_match(src, des)
        if self.points is not None and len(self.points) > 0:
            down_point = self.points[0]  # 需要临时存储一下此处得到的self.points
        else:
            down_point = (0, 0)
        des = 'ark_btn_update_build_hero_detail_2.png'
        self.is_match(src, des)
        if self.points is not None and len(self.points) > 0:
            up_point = self.points[0]
        else:
            up_point = (0, 0)
        print('up,down', up_point, down_point)
        if up_point == (0, 0) or down_point == (0, 0):
            return
        # 计算第一个干员的坐标及后续干员的x轴、y轴的增量
        x = (up_point[0] + down_point[0]) / 2
        y = (down_point[1] + 3 * up_point[1]) / 4
        x_one_step = 140  # 设置为固定值（仅在屏幕大小为1600*900时有效）
        y_one_step = (down_point[1] + up_point[1]) / 2
        # 无论实际需要几个干员，都按照5个干员添加
        x_step = [0, 0, x_one_step, x_one_step, x_one_step + x_one_step]
        y_step = [0, y_one_step, 0, y_one_step, 0]
        for i in range(5):
            self.points = [(x + x_step[i], y + y_step[i])]
            self.take_action(ActionType.CLICK)
            time.sleep(0.1)
        des = 'ark_btn_update_build_hero_confirm.png'
        # 先点击”确认“按钮
        self.is_match(src, des)
        if self.points is None or len(self.points) == 0:
            self.points = [(1475, 850)]  # ”确认“按钮的默认位置
        self.take_action(ActionType.CLICK)
        # 循环判断直到返回进驻总览页面之后才结束判断（防止网络不好的情况）
        des = 'ark_tmpl_garrison_hero.png'
        self.continue_action(src, des, flag=self.Flag.NO_SATISFY_CONDITION)
        print('单个建筑更换完成')

    def main(self):
        pass

    def _test(self):
        print('test')


def return_home():
    pass


if __name__ == '__main__':
    arknights = AutoArknights()
    # arknights._test()
    # arknights.start_simulator()
    # arknights.enter_game()
    # arknights.enter_build()
    arknights.update_all_builds_hero()
    # arknights.update_one_build_hero()

    # test-4
    # a = [1, 2, 3, 4]
    # print(a[-1:0])
    # print(a[0:-1])
    # print(a[0::len(a) - 1])

    # test-3
    # arknights.points = [(1503, 247), (1504, 247), (1502, 248), (1503, 248), (1504, 248), (1505, 248), (1502, 249),
    #                     (1503, 249), (1504, 249), (1505, 249), (1503, 250), (1504, 250), (1504, 445), (1503, 446),
    #                     (1504, 446), (1505, 446), (1502, 447), (1503, 447), (1504, 447), (1505, 447), (1503, 448),
    #                     (1504, 448), (1505, 448), (1504, 449), (1504, 709), (1503, 710), (1504, 710), (1505, 710),
    #                     (1502, 711), (1503, 711)]
    # arknights.simply_points()
    # print(arknights.points)

    # test-1
    # print(auto.is_match('ark_home_1.png', 'ark_btn_quit.png'))
    # load_image_file('./auto_arknights2/ark_home.png')
    # a = [1, 1, 1, 1, 1]
    # j = 1
    # for j, v in enumerate(a):
    #     print(j, v)
    # print('j', j)

    # test-2
    # a = ['a', 'bb', 'c', 'dd', 'e', 'ff']
    # for i, v in enumerate(a):
    #     print(i, v)
    #     a.pop(i)
    # print(a)
