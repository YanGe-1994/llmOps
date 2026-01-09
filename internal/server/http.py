#!/use/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   :2026/1/2 11:32
@Author :yange2615@gmail.com
@File   :http
"""
import os

from flask import Flask
from internal.router import Router
from config import Config

from internal.exception import CustomException
from pkg.response import Response, json, HttpCode

from flask_sqlalchemy import SQLAlchemy

from internal.model import App
app = Flask(__name__)

class Http(Flask):
    def __init__(self,*args,conf:Config,router:Router,db:SQLAlchemy,**kwargs):
        # 调用父类构造函数初始化
        super().__init__(*args,**kwargs)

        # 初始化应用配置
        self.config.from_object(conf)

        # 初始化flask扩展
        db.init_app(self)
        with self.app_context():
            _ =App()
            db.create_all()

        # 绑定异常错误处理
        self.register_error_handler(Exception,self._register_error_handler)

        # 注册应用路由
        router.register_route(self)

    def _register_error_handler(self, error:Exception):
        print('error', error)
        if isinstance(error, CustomException):
            return json(Response(
                code=error.code,
                message=error.message,
                data=error.data if error.data is not None else {}
            ))
        elif self.debug or os.getenv('FLASK_ENV') == 'development':
            raise error
        else:
            return json(Response(
                code = HttpCode.Fail,
                message=str(error),
                data={}
            ))