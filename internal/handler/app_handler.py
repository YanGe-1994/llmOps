#!/use/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   :2026/1/2 11:15
@Author :yange2615@gmail.com
@File   :app_handler
"""
from flask import request
from openai import OpenAI
class AppHandler():
    """应用控制器"""
    def completion(self):
        # 1. 提取用户输入
        query = request.json.get('query')
        print('query',query)
        # 2. 构建openid客户端
        client = OpenAI(
            api_key="sk-2a8e9040e53e4cf1ba8b0391e3ef0786",
            # 以下是北京地域base_url，如果使用新加坡地域的模型，需要将base_url替换为：https://dashscope-intl.aliyuncs.com/compatible-mode/v1
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
        completion = client.chat.completions.create(
            model="qwen-plus",
            messages=[{'role': 'user', 'content': query}]
        )
        return completion.choices[0].message.content

    def ping(self):
        return {"ping": "pong"}