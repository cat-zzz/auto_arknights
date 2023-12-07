"""
@File   : util.py
@Desc   :
@Author : gql
@Date   : 2023/11/22 11:14
"""
import easyocr as easyocr


def ocr_poor_network_hint(reader, path='./arknights/test.png'):
    """
    识别图片中是否包含’正在提交反馈至神经‘中的任意字符
    """
    if reader is None:
        return False
    key_list = ['正', '在', '交', '反', '馈', '反馈', '神', '经', '神经']
    result = reader.readtext(path, detail=1, text_threshold=0.8, low_text=0.5)
    if any(key in r for key in key_list for r in result):
        print('OCR: 正在提交反馈至神经')
        return True
    else:
        return False


if __name__ == '__main__':
    path1 = './arknights/ark_home_1.png'
    reader1 = easyocr.Reader(['ch_sim', 'en'], gpu=False)  # need to run only once to load model into memory
    # result = reader.readtext(r"C:\cdev\projects\python\auto_arknights\adb\arknights\test.png", detail=0)
    # result = reader.readtext('./arknights/test.png')
    # ocr_poor_network_hint(reader1, path1)
    # print()
    # path1 = './arknights/test.png'
    # ocr_poor_network_hint(reader1, path1)
    # print()
    path1 = './arknights/test3.png'
    ocr_poor_network_hint(reader1, path1)
