"""
@File   : adbcmd.py
@Desc   :
@Author : gql
@Date   : 2023/12/7 13:02
"""
import re
import subprocess


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
            self.adb_path + 'adb shell input swipe ' + str(x1) + ' ' + str(y1) + ' ' + str(x2) + ' ' + str(
                y2) + ' 2000')
        print(f'adbcmd: 滑动操作({x1, y1})->({x2, y2})')

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
        # print('adbcmd: 截图操作')

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
