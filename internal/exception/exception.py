#!/use/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   :2026/1/5 14:09
@Author :yange2615@gmail.com
@File   :exception
"""
from pkg.response import HttpCode
from typing import Any
from dataclasses import field

# 基础自定义异常信息
class CustomException(Exception):
    code = HttpCode.Fail
    message: str = ""
    data: Any = field(default_factory=dict)

    def __init__(self, message: str = None, data: Any = None):
        super().__init__()
        self.message = message
        self.data = data

# 通用失败异常
class FailException(CustomException):
    pass

# 未找到数据异常
class NotFoundException(CustomException):
    code = HttpCode.NOT_FOUND

# 未授权异常
class UnauthorizedException(CustomException):
    code = HttpCode.UNAUTHORIZED

# 无权限异常
class ForbiddenException(CustomException):
    code = HttpCode.FORBIDDEN

# 数据验证异常
class ValidateErrorException(CustomException):
    code = HttpCode.VALIDATE_ERROR