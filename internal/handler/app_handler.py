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
from langchain_core.callbacks import StdOutCallbackHandler
from langchain_core.prompts import ChatPromptTemplate
from injector import inject
from dataclasses import dataclass

from internal.schema.app_schema import CompletionReq
from internal.service import AppService
from pkg.response import success_json, validate_error_json, success_message
from internal.exception import FailException

from pydantic import BaseModel,Field
from langchain_qwq import ChatQwen
from langchain_core.output_parsers import JsonOutputParser

class Joke(BaseModel):
    joke: str = Field(description="回答用户的冷笑话")
    punchline: str= Field(description="冷笑话的笑点")

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
        # 生成提示词
        prompt = ChatPromptTemplate.from_template("""
            你是一个超级搞笑的脱口秀演员，请认真回答用户的问题。
            {format_instructions}
            用户问题: {query}
        """)

        # 构建通义千问llm客户端
        llm = ChatQwen(
            model="qwen-plus",
            max_tokens=3_000,
            timeout=None,
            max_retries=2,
            api_key=os.environ.get('DASHSCOPE_API_KEY'),
            base_url=os.environ.get('DASHSCOPE_BASE_URL'),
            callbacks=[StdOutCallbackHandler()]
        )

        # 构建输出解析器
        parser = JsonOutputParser(pydantic_object=Joke)
        # 构建链式调用
        chain = prompt | llm

        # 执行链式调用
        response = chain.invoke({
            "query": query,
            "format_instructions": parser.get_format_instructions()
        })
        print('content', response.content)
        # 返回结果
        return success_json({'content': response.content})

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