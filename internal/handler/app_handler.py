#!/use/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   :2026/1/2 11:15
@Author :yange2615@gmail.com
@File   :app_handler
"""
import os

from flask import request
from openai import OpenAI

from internal.schema.app_schema import CompletionReq


class AppHandler():
    """应用控制器"""
    def completion(self):
        # 1. 提取用户输入
        req = CompletionReq()
        if not req.validate():
            return req.errors

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
        return completion.choices[0].message.content

    def ping(self):
        return {"ping": "pong"}