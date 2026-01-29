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
from langchain_core.prompts import ChatPromptTemplate,MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.chat_history import InMemoryChatMessageHistory

from injector import inject
from dataclasses import dataclass

from internal.schema.app_schema import CompletionReq
from internal.service import AppService
from pkg.response import success_json, validate_error_json, success_message
from internal.exception import FailException

from pydantic import BaseModel,Field
from langchain_qwq import ChatQwen
from langchain_core.output_parsers import JsonOutputParser

# 1. 创建会话存储（字典存储所有会话的历史）
store = {}

def get_session_history(session_id: str) -> InMemoryChatMessageHistory:
    """
    获取或创建会话历史

    Args:
        session_id: 会话ID
    Returns:
        InMemoryChatMessageHistory: 消息历史对象
    """
    if session_id not in store:
        store[session_id] = InMemoryChatMessageHistory()
    return store[session_id]

# 2. 创建提示模板
prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个有帮助的助手。请记住用户之前说过的内容。"),
    MessagesPlaceholder(variable_name="history"),  # 历史消息占位符
    ("human", "{input}")  # 当前用户输入
])

# 3. 创建 LLM 和链
# 构建通义千问llm客户端
llm = ChatQwen(
    model="qwen-plus",
    max_tokens=3_000,
    timeout=None,
    max_retries=2,
    api_key=os.environ.get('DASHSCOPE_API_KEY'),
    base_url=os.environ.get('DASHSCOPE_BASE_URL')
)
chain = prompt | llm

# 4. 包装成带历史的链
chain_with_history = RunnableWithMessageHistory(
    chain,
    get_session_history,
    input_messages_key="input",  # 输入中的消息键名
    history_messages_key="history"  # 提示模板中的历史占位符名
)


# 5. 使用
def chat(user_input: str, session_id: str = "default"):
    """
    发送消息并获取回复

    Args:
        user_input: 用户输入
        session_id: 会话ID
    """
    response = chain_with_history.invoke(
        {"input": user_input},
        config={"configurable": {"session_id": session_id}}
    )
    return response.content

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

        # 执行链式调用
        content = chat(query, session_id="user_002")
        print('content', content)
        # 返回结果
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