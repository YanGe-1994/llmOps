#!/use/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   :2026/1/2 11:18
@Author :yange2615@gmail.com
@File   :router
"""
from dataclasses import dataclass
from flask import Flask, Blueprint
from injector import inject

from internal.handler import AppHandler

@inject
@dataclass
class Router:
    """路由"""
    app_handler: AppHandler
    def register_route(self, app:Flask):
        """注册路由"""
        # 1. 创建一个蓝图
        bp = Blueprint("llmops", __name__, url_prefix="")
        # 2.将url与对应的控制器方法绑定
        bp.add_url_rule('ping', view_func=self.app_handler.ping)
        bp.add_url_rule('app/completion',methods=["post"], view_func=self.app_handler.completion)
        # 3.在应用上注册蓝图
        app.register_blueprint(bp)