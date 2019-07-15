import os, sys, platform

if platform.system() == "Windows":
    BASE_DIR = '\\'.join(os.path.abspath(os.path.dirname(__file__)).split('\\')[:-1])  # 客户端目录
else:
    BASE_DIR = '/'.join(os.path.abspath(os.path.dirname(__file__)).split('/')[:-1])

sys.path.append(BASE_DIR)  # 把客户端加入环境变量, 就可以像下面这样调用了
from core import HouseStark


if __name__ == '__main__':
    HouseStark.ArgvHandler(sys.argv)
