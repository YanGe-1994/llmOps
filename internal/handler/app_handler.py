#!/use/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   :2026/1/2 11:15
@Author :yange2615@gmail.com
@File   :app_handler
"""
import os
import uuid

from flask import request
from openai import OpenAI
from injector import inject
from dataclasses import dataclass

from internal.schema.app_schema import CompletionReq
from internal.service import AppService
from pkg.response import success_json, validate_error_json, success_message
from internal.exception import FailException

@inject
@dataclass
class AppHandler:
    """应用控制器"""
    app_service: AppService
    def completion(self):
        # 1. 提取用户输入
        req = CompletionReq()
        if not req.validate():
            return validate_error_json(req.errors)

        query = request.json.get('query')
        # 2. 构建openid客户端
        client = OpenAI(
            api_key=os.environ.get("OPEN_API_KEY"),
            base_url=os.environ.get("BASE_URL"),
        )
        completion = client.chat.completions.create(
            model="qwen-plus",
            messages=[{'role': 'user', 'content': query}]
        )
        content = completion.choices[0].message.content
        return success_json({'content': content})

    def ping(self):
        # return {"ping": "pong"}
        raise FailException('数据未找到')

    def create_app(self):
        app = self.app_service.create_app()
        return success_message(f"应用成功创建{app.id}")

    def get_app(self, id: uuid.UUID):
        app = self.app_service.get_app(id)
        return success_json({'name': app.name})

    def update_app(self, id: uuid.UUID):
        app = self.app_service.update_app(id)
        return success_json({'name': app.name})

    def delete_app(self, id: uuid.UUID):
        app = self.app_service.delete_app(id)
        return success_json({'name': app.name})