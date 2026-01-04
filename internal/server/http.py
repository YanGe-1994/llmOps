#!/use/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   :2026/1/2 11:32
@Author :yange2615@gmail.com
@File   :http
"""
from flask import Flask
from internal.router import Router
from config import Config
app = Flask(__name__)

class Http(Flask):
    def __init__(self,*args,conf:Config,router:Router,**kwargs):
        super().__init__(*args,**kwargs)
        # 注册应用路由
        router.register_route(self)

        self.config.from_object(conf)