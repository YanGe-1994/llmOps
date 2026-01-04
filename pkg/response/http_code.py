#!/use/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   :2026/1/4 16:58
@Author :yange2615@gmail.com
@File   :http_code
"""
from  enum import Enum

class HttpCode(str,Enum):
    SUCCESS = 'success' # 成功
    Fail = 'fail' # 失败
    NOT_FOUND = 'not_found' # 未找到
    UNAUTHORIZED = 'unauthorized' # 未授权
    FORBIDDEN = 'forbidden' # 无权限
    VALIDATE_ERROR = 'validate_error' #数据验证错误