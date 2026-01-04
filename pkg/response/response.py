#!/use/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   :2026/1/4 17:02
@Author :yange2615@gmail.com
@File   :response
"""
from dataclasses import dataclass,field
from typing import Any

from flask import jsonify

from .http_code import HttpCode

@dataclass
class Response:
    code: HttpCode = HttpCode.SUCCESS
    message: str = ""
    data: Any = field(default_factory=dict)

def json(data: Response = None):
    return  jsonify(data), 200

# 成功数据响应
def success_json(data: Any = None):
    return json(Response(code=HttpCode.SUCCESS,message="",data=data))

# 失败数据响应
def error_json(data: Response = None):
    return json(Response(code=HttpCode.Fail,message="",data=data))

# 数据验证错误响应
def validate_error_json(errors: dict=None):
    first_key = next(iter(errors))
    if first_key is not  None:
        mes = errors.get(first_key)[0]
    else:
        mes = ""
    return json(Response(code=HttpCode.VALIDATE_ERROR,message=mes,data=errors))

# 基础消息响应，固定返回消息提示， 数据固定为空字典
def message(code: HttpCode = None, msg: str = ""):
    return json(Response(code=code,message=msg, data={}))

# 成功的消息响应
def success_message(msg: str = ""):
    return  message(code=HttpCode.SUCCESS, msg=msg )

# 失败的消息响应
def fail_message(msg: str = ""):
    return message(code=HttpCode.FAIL, msg=msg)

# 未找到消息响应
def not_found_message(msg: str = ""):
    return message(code=HttpCode.NOT_FOUND, msg=msg)

# 未授权的消息响应
def unauthorized_message(msg: str = ""):
    return message(code=HttpCode.UNAUTHORIZED, msg=msg)

# 无权限消息响应
def forbidden_message(msg: str = ""):
    return message(code=HttpCode.FORBIDDEN, msg=msg)