"""
@File   : test.py
@Desc   :
@Author : gql
@Date   : 2023/11/22 11:14
"""
import easyocr as easyocr

if __name__ == '__main__':
    reader = easyocr.Reader(['ch_sim'], gpu=False)  # need to run only once to load model into memory
    # result = reader.readtext(r"C:\cdev\projects\python\auto_arknights\adb\arknights\test.png", detail=0)
    result = reader.readtext('./arknights/test.png')
    print(result)
