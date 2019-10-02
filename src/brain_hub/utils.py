import sys
from brain_hub.conf import *


def append_api_path(root, api):
    '''
    导入api所在的目录
    :return:
    '''
    paths = api.split('/')
    if len(paths) > 1:
        path = SLASH.join(paths[: -1])
        sys.path.append(root + path)
    return __import__(paths[-1] if paths[-1] != '' else INDEX_API_NAME)
