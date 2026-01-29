#!/use/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   :2026/1/29 22:23
@Author :yange2615@gmail.com
@File   :记忆功能测试
"""
import os
from dotenv import load_dotenv

load_dotenv()

from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_qwq import ChatQwen

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
    input_messages_key="input",      # 输入中的消息键名
    history_messages_key="history"   # 提示模板中的历史占位符名
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

# 示例使用
if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    
    print(chat("你好我是焚影，喜欢唱跳rap篮球", session_id="user_001"))
    print(chat("我是谁？我喜欢什么？", session_id="user_001"))
    # 输出: 你喜欢吃苹果和香蕉

    print(chat("我是谁？我喜欢什么？", session_id="user_002"))