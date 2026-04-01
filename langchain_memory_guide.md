# LangChain 记忆功能使用指南

> **适用版本**: langchain-core >= 1.0.0, langgraph >= 0.2.0
> **文档更新日期**: 2026-01-29
> **当前测试版本**: langchain-core 1.2.7, langchain-community 0.4.1

## 目录
- [概述](#概述)
- [版本变化说明](#版本变化说明)
- [推荐方案](#推荐方案)
  - [1. LangGraph Checkpointer（最推荐）](#1-langgraph-checkpointer最推荐)
  - [2. RunnableWithMessageHistory](#2-runnablewithmessagehistory)
  - [3. 手动管理消息历史](#3-手动管理消息历史)
- [持久化存储方案](#持久化存储方案)
- [长期记忆（Long-Term Memory）](#长期记忆long-term-memory)
- [旧版本方式（已弃用）](#旧版本方式已弃用)
- [最佳实践](#最佳实践)
- [常见问题](#常见问题)

---

## 概述

LangChain 的记忆功能用于在对话中保持上下文，使 AI 能够记住之前的对话内容。

### 记忆类型

1. **短期记忆（Short-Term Memory）**：单次会话内的对话历史
2. **长期记忆（Long-Term Memory）**：跨会话的持久化记忆（2025年新增）

### 实现方式演进

| 时期 | 方式 | 状态 |
|------|------|------|
| 旧版本（< 0.1.0） | `ConversationBufferMemory` 等 Memory 类 | ⚠️ 已弃用 |
| 当前版本（>= 1.0.0） | `RunnableWithMessageHistory` + 消息历史管理 | ✅ 推荐 |
| 最新版本（>= 1.0.0） | LangGraph Checkpointer + 持久化 | ✅ 最推荐 |

## 版本变化说明

### 旧版本（< 0.1.0）- 已弃用
```python
from langchain.memory import ConversationBufferMemory  # ⚠️ 已弃用
```

### 当前版本（>= 1.0.0）- 推荐使用
```python
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langgraph.checkpoint.memory import MemorySaver
```

### 关键变化

1. **Memory 类已弃用**：不再使用 `ConversationBufferMemory`、`ConversationSummaryMemory` 等
2. **消息历史管理**：使用 `BaseChatMessageHistory` 接口
3. **LangGraph 集成**：通过 Checkpointer 实现更强大的状态管理
4. **长期记忆支持**：2025年新增跨会话记忆能力

---

## 推荐方案

### 1. LangGraph Checkpointer（最推荐）

LangGraph 的 Checkpointer 是最新、最强大的记忆管理方式，支持自动状态持久化和复杂的对话流程。

#### 核心概念

- **Checkpointer**：在每个步骤后自动保存图状态
- **thread_id**：用于区分不同的对话会话
- **持久化**：支持内存、SQLite、PostgreSQL 等多种后端

#### 安装依赖
```bash
pip install langgraph langchain-core langchain-openai
```

#### 基础实现

```python
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, MessagesState, START, END
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI

# 1. 定义状态（使用内置的 MessagesState）
class State(MessagesState):
    """
    MessagesState 包含一个 messages 字段，类型为 list[BaseMessage]
    LangGraph 会自动管理消息的添加和更新
    """
    pass

# 2. 创建 LLM
llm = ChatOpenAI(model="gpt-4o", temperature=0.7)

# 3. 定义聊天节点
def chatbot(state: State):
    """处理用户消息并生成回复"""
    messages = state["messages"]

    # 可选：添加系统提示
    if not any(isinstance(m, SystemMessage) for m in messages):
        messages = [SystemMessage(content="你是一个有帮助的助手")] + messages

    # 调用 LLM
    response = llm.invoke(messages)

    # 返回新消息（LangGraph 会自动追加到 messages 列表）
    return {"messages": [response]}

# 4. 构建图
workflow = StateGraph(State)
workflow.add_node("chatbot", chatbot)
workflow.add_edge(START, "chatbot")
workflow.add_edge("chatbot", END)

# 5. 创建内存保存器并编译
memory = MemorySaver()
app = workflow.compile(checkpointer=memory)

# 6. 使用（通过 thread_id 区分不同会话）
def chat(user_input: str, thread_id: str = "default"):
    """
    发送消息并获取回复

    Args:
        user_input: 用户输入
        thread_id: 会话ID，用于区分不同用户或对话
    """
    config = {"configurable": {"thread_id": thread_id}}

    result = app.invoke(
        {"messages": [HumanMessage(content=user_input)]},
        config=config
    )

    return result["messages"][-1].content

# 示例使用
print(chat("我叫张三，今年25岁", thread_id="user_001"))
# 输出: 你好张三！很高兴认识你...

print(chat("我叫什么名字？多大了？", thread_id="user_001"))
# 输出: 你叫张三，今年25岁

print(chat("我叫什么名字？", thread_id="user_002"))
# 输出: 抱歉，我不知道你的名字... (不同会话，没有历史)
```

#### 流式输出

```python
def chat_stream(user_input: str, thread_id: str = "default"):
    """流式输出聊天回复"""
    config = {"configurable": {"thread_id": thread_id}}

    for chunk in app.stream(
        {"messages": [HumanMessage(content=user_input)]},
        config=config,
        stream_mode="values"
    ):
        if "messages" in chunk:
            # 获取最新的消息
            last_message = chunk["messages"][-1]
            if isinstance(last_message, AIMessage):
                print(last_message.content, end="", flush=True)
    print()  # 换行

# 使用
chat_stream("给我讲个笑话", thread_id="user_001")
```

#### 查看和管理历史

```python
# 1. 获取特定会话的当前状态
config = {"configurable": {"thread_id": "user_001"}}
state = app.get_state(config)

print("当前消息历史:")
for msg in state.values["messages"]:
    print(f"{msg.type}: {msg.content}")

# 2. 获取状态历史（所有 checkpoint）
history = app.get_state_history(config)
for state_snapshot in history:
    print(f"Checkpoint ID: {state_snapshot.config['configurable']['checkpoint_id']}")
    print(f"Messages count: {len(state_snapshot.values['messages'])}")

# 3. 更新状态（例如清除历史）
app.update_state(config, {"messages": []})

# 4. 更新状态（例如添加系统消息）
app.update_state(config, {
    "messages": [SystemMessage(content="你现在是一个专业的Python导师")]
})
```

#### 高级用法：自定义状态

```python
from typing import Annotated
from langgraph.graph import add_messages

class CustomState(MessagesState):
    """自定义状态，添加额外字段"""
    user_name: str = ""
    conversation_count: int = 0

def chatbot_with_state(state: CustomState):
    """使用自定义状态的聊天机器人"""
    messages = state["messages"]
    user_name = state.get("user_name", "")
    count = state.get("conversation_count", 0)

    # 如果有用户名，添加到系统提示
    if user_name:
        system_msg = SystemMessage(
            content=f"你是一个有帮助的助手。用户名是 {user_name}，这是第 {count + 1} 次对话。"
        )
        messages = [system_msg] + messages

    response = llm.invoke(messages)

    return {
        "messages": [response],
        "conversation_count": count + 1
    }

# 构建图
workflow = StateGraph(CustomState)
workflow.add_node("chatbot", chatbot_with_state)
workflow.add_edge(START, "chatbot")
workflow.add_edge("chatbot", END)

app = workflow.compile(checkpointer=MemorySaver())

# 使用
config = {"configurable": {"thread_id": "user_001"}}
result = app.invoke(
    {
        "messages": [HumanMessage(content="你好")],
        "user_name": "张三"
    },
    config=config
)
```

---

### 2. RunnableWithMessageHistory

适合使用 LCEL（LangChain Expression Language）链的场景，是当前版本推荐的标准方式。

#### 核心概念

- **RunnableWithMessageHistory**：包装任何 Runnable，自动管理消息历史
- **BaseChatMessageHistory**：消息历史的抽象接口
- **session_id**：用于区分不同会话

#### 基础实现

```python
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_openai import ChatOpenAI

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
llm = ChatOpenAI(model="gpt-4o", temperature=0.7)
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
print(chat("我喜欢吃苹果和香蕉", session_id="user_001"))
print(chat("我喜欢吃什么水果？", session_id="user_001"))
# 输出: 你喜欢吃苹果和香蕉

print(chat("我喜欢吃什么？", session_id="user_002"))
# 输出: 抱歉，我不知道... (不同会话)
```

#### 流式输出

```python
def chat_stream(user_input: str, session_id: str = "default"):
    """流式输出聊天回复"""
    for chunk in chain_with_history.stream(
        {"input": user_input},
        config={"configurable": {"session_id": session_id}}
    ):
        print(chunk.content, end="", flush=True)
    print()

# 使用
chat_stream("给我讲个故事", session_id="user_001")
```

#### 异步支持

```python
import asyncio

async def chat_async(user_input: str, session_id: str = "default"):
    """异步聊天"""
    response = await chain_with_history.ainvoke(
        {"input": user_input},
        config={"configurable": {"session_id": session_id}}
    )
    return response.content

# 使用
asyncio.run(chat_async("你好", session_id="user_001"))
```

#### 限制历史消息数量

```python
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import BaseMessage

class LimitedChatMessageHistory(BaseChatMessageHistory):
    """限制消息数量的历史记录"""

    def __init__(self, max_messages: int = 20):
        self.max_messages = max_messages
        self._messages: list[BaseMessage] = []

    @property
    def messages(self) -> list[BaseMessage]:
        """返回最近的 N 条消息"""
        return self._messages[-self.max_messages:]

    def add_message(self, message: BaseMessage) -> None:
        """添加消息"""
        self._messages.append(message)
        # 自动清理过多的消息
        if len(self._messages) > self.max_messages * 2:
            self._messages = self._messages[-self.max_messages:]

    def clear(self) -> None:
        """清空历史"""
        self._messages = []

# 使用限制历史的存储
limited_store = {}

def get_limited_session_history(session_id: str) -> BaseChatMessageHistory:
    if session_id not in limited_store:
        limited_store[session_id] = LimitedChatMessageHistory(max_messages=10)
    return limited_store[session_id]

# 创建带限制历史的链
chain_with_limited_history = RunnableWithMessageHistory(
    chain,
    get_limited_session_history,
    input_messages_key="input",
    history_messages_key="history"
)
```

#### 查看和管理历史

```python
# 1. 查看会话历史
def get_history(session_id: str):
    """获取会话的所有消息"""
    history = get_session_history(session_id)
    for msg in history.messages:
        print(f"{msg.type}: {msg.content}")

get_history("user_001")

# 2. 清除会话历史
def clear_history(session_id: str):
    """清除指定会话的历史"""
    if session_id in store:
        store[session_id].clear()

clear_history("user_001")

# 3. 删除会话
def delete_session(session_id: str):
    """删除整个会话"""
    if session_id in store:
        del store[session_id]

delete_session("user_001")

# 4. 获取所有会话ID
def list_sessions():
    """列出所有会话ID"""
    return list(store.keys())

print(list_sessions())
```

#### 高级用法：多输入输出

```python
from langchain_core.runnables import RunnablePassthrough

# 对于有多个输入的链
prompt_multi = ChatPromptTemplate.from_messages([
    ("system", "你是 {role}。"),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{input}")
])

chain_multi = prompt_multi | llm

chain_with_history_multi = RunnableWithMessageHistory(
    chain_multi,
    get_session_history,
    input_messages_key="input",
    history_messages_key="history"
)

# 使用
response = chain_with_history_multi.invoke(
    {"input": "你好", "role": "Python专家"},
    config={"configurable": {"session_id": "user_001"}}
)
```

---

### 3. 手动管理消息历史

最灵活的方式，完全控制消息的存储和检索。

```python
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI

class ConversationManager:
    def __init__(self, llm, system_message: str = "你是一个有帮助的助手"):
        self.llm = llm
        self.conversations = {}  # {session_id: [messages]}
        self.system_message = SystemMessage(content=system_message)

    def chat(self, user_input: str, session_id: str = "default", max_history: int = 20):
        # 获取或创建会话
        if session_id not in self.conversations:
            self.conversations[session_id] = [self.system_message]

        # 添加用户消息
        self.conversations[session_id].append(HumanMessage(content=user_input))

        # 限制历史长度（保留系统消息 + 最近的对话）
        if len(self.conversations[session_id]) > max_history:
            self.conversations[session_id] = (
                [self.system_message] +
                self.conversations[session_id][-(max_history-1):]
            )

        # 调用 LLM
        response = self.llm.invoke(self.conversations[session_id])

        # 保存 AI 回复
        self.conversations[session_id].append(AIMessage(content=response.content))

        return response.content

    def clear_session(self, session_id: str):
        """清除指定会话"""
        if session_id in self.conversations:
            self.conversations[session_id] = [self.system_message]

    def get_history(self, session_id: str):
        """获取会话历史"""
        return self.conversations.get(session_id, [])

# 使用
llm = ChatOpenAI(model="gpt-4")
manager = ConversationManager(llm)

print(manager.chat("你好，我是李四", session_id="user_001"))
print(manager.chat("我叫什么？", session_id="user_001"))
print(manager.get_history("user_001"))
```

---

## 持久化存储方案

内存存储在应用重启后会丢失，生产环境建议使用持久化存储。

### 1. SQLite 存储（推荐用于开发和小型应用）

#### 使用 SQLChatMessageHistory

```python
from langchain_community.chat_message_histories import SQLChatMessageHistory

def get_session_history(session_id: str):
    """使用 SQLite 存储消息历史"""
    return SQLChatMessageHistory(
        session_id=session_id,
        connection_string="sqlite:///chat_history.db",
        table_name="message_store"  # 可选，默认为 message_store
    )

# 使用方式与 InMemoryChatMessageHistory 相同
chain_with_history = RunnableWithMessageHistory(
    chain,
    get_session_history,
    input_messages_key="input",
    history_messages_key="history"
)

# 使用
response = chain_with_history.invoke(
    {"input": "你好"},
    config={"configurable": {"session_id": "user_001"}}
)
```

#### 使用 LangGraph SqliteSaver

```python
from langgraph.checkpoint.sqlite import SqliteSaver

# 方式1: 使用连接字符串
with SqliteSaver.from_conn_string("checkpoints.db") as checkpointer:
    app = workflow.compile(checkpointer=checkpointer)

    result = app.invoke(
        {"messages": [HumanMessage(content="你好")]},
        config={"configurable": {"thread_id": "user_001"}}
    )

# 方式2: 使用异步版本
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

async def main():
    async with AsyncSqliteSaver.from_conn_string("checkpoints.db") as checkpointer:
        app = workflow.compile(checkpointer=checkpointer)

        result = await app.ainvoke(
            {"messages": [HumanMessage(content="你好")]},
            config={"configurable": {"thread_id": "user_001"}}
        )
```

### 2. PostgreSQL 存储（推荐用于生产环境）

#### 安装依赖
```bash
pip install psycopg2-binary  # 或 psycopg2
```

#### 使用 PostgresChatMessageHistory

```python
from langchain_community.chat_message_histories import PostgresChatMessageHistory

def get_session_history(session_id: str):
    """使用 PostgreSQL 存储消息历史"""
    return PostgresChatMessageHistory(
        session_id=session_id,
        connection_string="postgresql://user:password@localhost:5432/dbname",
        table_name="chat_history"
    )

# 使用方式相同
chain_with_history = RunnableWithMessageHistory(
    chain,
    get_session_history,
    input_messages_key="input",
    history_messages_key="history"
)
```

#### 使用 LangGraph PostgresSaver

```python
from langgraph.checkpoint.postgres import PostgresSaver

# 同步版本
with PostgresSaver.from_conn_string(
    "postgresql://user:password@localhost:5432/dbname"
) as checkpointer:
    app = workflow.compile(checkpointer=checkpointer)

# 异步版本
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

async with AsyncPostgresSaver.from_conn_string(
    "postgresql://user:password@localhost:5432/dbname"
) as checkpointer:
    app = workflow.compile(checkpointer=checkpointer)
```

#### 连接池配置

```python
from psycopg_pool import ConnectionPool

# 创建连接池
pool = ConnectionPool(
    conninfo="postgresql://user:password@localhost:5432/dbname",
    min_size=1,
    max_size=10
)

# 使用连接池
checkpointer = PostgresSaver(pool)
app = workflow.compile(checkpointer=checkpointer)
```

### 3. Redis 存储（推荐用于高性能场景）

#### 安装依赖
```bash
pip install redis
```

#### 使用 RedisChatMessageHistory

```python
from langchain_community.chat_message_histories import RedisChatMessageHistory

def get_session_history(session_id: str):
    """使用 Redis 存储消息历史"""
    return RedisChatMessageHistory(
        session_id=session_id,
        url="redis://localhost:6379/0",
        ttl=3600  # 1小时过期（可选）
    )

# 使用方式相同
chain_with_history = RunnableWithMessageHistory(
    chain,
    get_session_history,
    input_messages_key="input",
    history_messages_key="history"
)
```

#### 自定义 Redis Checkpointer

```python
from langgraph.checkpoint.base import BaseCheckpointSaver
import redis
import json

class RedisCheckpointer(BaseCheckpointSaver):
    """自定义 Redis Checkpointer"""

    def __init__(self, redis_url: str, ttl: int = 3600):
        self.redis_client = redis.from_url(redis_url)
        self.ttl = ttl

    def put(self, config, checkpoint, metadata):
        """保存 checkpoint"""
        thread_id = config["configurable"]["thread_id"]
        key = f"checkpoint:{thread_id}"

        data = {
            "checkpoint": checkpoint,
            "metadata": metadata
        }

        self.redis_client.setex(
            key,
            self.ttl,
            json.dumps(data, default=str)
        )

    def get(self, config):
        """获取 checkpoint"""
        thread_id = config["configurable"]["thread_id"]
        key = f"checkpoint:{thread_id}"

        data = self.redis_client.get(key)
        if data:
            return json.loads(data)
        return None

# 使用
checkpointer = RedisCheckpointer("redis://localhost:6379/0")
app = workflow.compile(checkpointer=checkpointer)
```

### 4. MongoDB 存储

#### 安装依赖
```bash
pip install pymongo
```

#### 使用 MongoDBChatMessageHistory

```python
from langchain_community.chat_message_histories import MongoDBChatMessageHistory

def get_session_history(session_id: str):
    """使用 MongoDB 存储消息历史"""
    return MongoDBChatMessageHistory(
        session_id=session_id,
        connection_string="mongodb://localhost:27017/",
        database_name="chat_db",
        collection_name="chat_history"
    )

# 使用方式相同
chain_with_history = RunnableWithMessageHistory(
    chain,
    get_session_history,
    input_messages_key="input",
    history_messages_key="history"
)
```

### 5. 文件系统存储（简单场景）

```python
from langchain_community.chat_message_histories import FileChatMessageHistory
import os

def get_session_history(session_id: str):
    """使用文件系统存储消息历史"""
    # 创建存储目录
    os.makedirs("chat_histories", exist_ok=True)

    return FileChatMessageHistory(
        file_path=f"chat_histories/{session_id}.json"
    )

# 使用方式相同
chain_with_history = RunnableWithMessageHistory(
    chain,
    get_session_history,
    input_messages_key="input",
    history_messages_key="history"
)
```

### 存储方案对比

| 存储方案 | 优点 | 缺点 | 适用场景 |
|---------|------|------|---------|
| **内存** | 最快，无需配置 | 重启丢失，不支持分布式 | 开发测试 |
| **SQLite** | 简单，无需额外服务 | 并发性能有限 | 小型应用、单机部署 |
| **PostgreSQL** | 可靠，支持事务，功能强大 | 需要额外服务 | 生产环境、大型应用 |
| **Redis** | 极快，支持过期 | 内存占用，持久化配置复杂 | 高性能场景、临时数据 |
| **MongoDB** | 灵活的文档存储 | 需要额外服务 | 需要复杂查询的场景 |
| **文件系统** | 简单，易于调试 | 并发性能差 | 原型开发、单用户 |

---

## 长期记忆（Long-Term Memory）

LangChain 在 2025 年推出了长期记忆功能，允许跨会话存储和检索信息。

### 概念

- **短期记忆**：单次会话内的对话历史（上面介绍的所有方式）
- **长期记忆**：跨会话的持久化记忆，可以存储用户偏好、事实等信息

### 使用 LangGraph 的长期记忆

```python
from langgraph.store.memory import InMemoryStore
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, SystemMessage

# 1. 创建长期记忆存储
long_term_store = InMemoryStore()

# 2. 定义带长期记忆的状态
class StateWithMemory(MessagesState):
    user_id: str = ""

def chatbot_with_long_term_memory(state: StateWithMemory):
    """使用长期记忆的聊天机器人"""
    user_id = state["user_id"]
    messages = state["messages"]

    # 从长期记忆中检索用户信息
    user_memories = long_term_store.get(f"user:{user_id}")

    # 构建系统提示
    if user_memories:
        memory_text = "\n".join([
            f"- {mem['key']}: {mem['value']}"
            for mem in user_memories
        ])
        system_msg = SystemMessage(
            content=f"关于用户的已知信息:\n{memory_text}"
        )
        messages = [system_msg] + messages

    # 调用 LLM
    response = llm.invoke(messages)

    # 从回复中提取需要记住的信息（简化示例）
    # 实际应用中可以使用更复杂的提取逻辑
    if "我叫" in messages[-1].content:
        # 提取并存储用户名
        # 这里需要更复杂的 NLP 处理
        pass

    return {"messages": [response]}

# 3. 构建图
workflow = StateGraph(StateWithMemory)
workflow.add_node("chatbot", chatbot_with_long_term_memory)
workflow.add_edge(START, "chatbot")
workflow.add_edge("chatbot", END)

# 4. 编译（同时使用短期和长期记忆）
app = workflow.compile(
    checkpointer=MemorySaver(),  # 短期记忆
    store=long_term_store         # 长期记忆
)

# 5. 使用
def chat_with_memory(user_input: str, user_id: str, thread_id: str):
    """带长期记忆的聊天"""
    config = {"configurable": {"thread_id": thread_id}}

    result = app.invoke(
        {
            "messages": [HumanMessage(content=user_input)],
            "user_id": user_id
        },
        config=config
    )

    return result["messages"][-1].content

# 示例：第一次对话
print(chat_with_memory("我叫张三，喜欢编程", user_id="user_001", thread_id="conv_001"))

# 第二次对话（新会话，但同一用户）
print(chat_with_memory("我喜欢什么？", user_id="user_001", thread_id="conv_002"))
# 应该能记住用户喜欢编程
```

### 手动管理长期记忆

```python
class LongTermMemoryManager:
    """长期记忆管理器"""

    def __init__(self, storage):
        self.storage = storage  # 可以是数据库、Redis等

    def save_memory(self, user_id: str, key: str, value: str):
        """保存长期记忆"""
        memories = self.storage.get(user_id, {})
        memories[key] = value
        self.storage[user_id] = memories

    def get_memories(self, user_id: str) -> dict:
        """获取用户的所有长期记忆"""
        return self.storage.get(user_id, {})

    def search_memories(self, user_id: str, query: str) -> list:
        """搜索相关记忆（简化版）"""
        memories = self.get_memories(user_id)
        # 实际应用中可以使用向量搜索
        return [
            (k, v) for k, v in memories.items()
            if query.lower() in k.lower() or query.lower() in v.lower()
        ]

# 使用
memory_manager = LongTermMemoryManager(storage={})

# 保存记忆
memory_manager.save_memory("user_001", "name", "张三")
memory_manager.save_memory("user_001", "hobby", "编程")

# 检索记忆
memories = memory_manager.get_memories("user_001")
print(memories)  # {'name': '张三', 'hobby': '编程'}
```

---

## 旧版本方式（已弃用）

以下方式在新版本中已不推荐使用，但为了兼容性仍然可用。

### ConversationBufferMemory

```python
# ⚠️ 已弃用
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain
from langchain_openai import ChatOpenAI

llm = ChatOpenAI()
memory = ConversationBufferMemory()
conversation = ConversationChain(
    llm=llm,
    memory=memory,
    verbose=True
)

conversation.predict(input="你好")
conversation.predict(input="我刚才说了什么？")
```

### ConversationBufferWindowMemory

```python
# ⚠️ 已弃用
from langchain.memory import ConversationBufferWindowMemory

# 只保留最近 5 轮对话
memory = ConversationBufferWindowMemory(k=5)
conversation = ConversationChain(llm=llm, memory=memory)
```

### ConversationSummaryMemory

```python
# ⚠️ 已弃用
from langchain.memory import ConversationSummaryMemory

# 自动总结历史对话
memory = ConversationSummaryMemory(llm=llm)
conversation = ConversationChain(llm=llm, memory=memory)
```

---

## 最佳实践

### 1. 选择合适的方案

| 场景 | 推荐方案 | 理由 |
|------|---------|------|
| 复杂对话流程、多步骤任务、需要状态管理 | LangGraph Checkpointer | 最强大，支持复杂状态和流程控制 |
| 简单对话、使用 LCEL 链、快速开发 | RunnableWithMessageHistory | 简单易用，与 LCEL 无缝集成 |
| 需要完全控制、自定义逻辑、特殊需求 | 手动管理消息历史 | 最灵活，可以实现任何自定义逻辑 |
| 生产环境、高可用性 | PostgreSQL + LangGraph | 可靠、支持事务、易于扩展 |
| 高性能、临时会话 | Redis + RunnableWithMessageHistory | 极快、支持自动过期 |
| 开发测试 | 内存存储 | 无需配置，快速迭代 |

### 2. 限制历史长度

避免上下文过长导致 token 超限和成本增加。

#### 方法1：限制消息数量

```python
class LimitedChatMessageHistory(BaseChatMessageHistory):
    """只保留最近 N 条消息"""

    def __init__(self, max_messages: int = 20):
        self.max_messages = max_messages
        self._messages: list[BaseMessage] = []

    @property
    def messages(self) -> list[BaseMessage]:
        # 保留系统消息 + 最近的对话
        system_msgs = [m for m in self._messages if isinstance(m, SystemMessage)]
        other_msgs = [m for m in self._messages if not isinstance(m, SystemMessage)]

        if len(other_msgs) > self.max_messages:
            other_msgs = other_msgs[-self.max_messages:]

        return system_msgs + other_msgs

    def add_message(self, message: BaseMessage) -> None:
        self._messages.append(message)

    def clear(self) -> None:
        self._messages = []
```

#### 方法2：基于 Token 数量限制

```python
from langchain.text_splitter import TokenTextSplitter
from langchain_core.messages import BaseMessage

def trim_messages_by_tokens(
    messages: list[BaseMessage],
    max_tokens: int = 4000
) -> list[BaseMessage]:
    """根据 token 数量裁剪消息"""
    from tiktoken import encoding_for_model

    # 获取编码器
    enc = encoding_for_model("gpt-4")

    # 保留系统消息
    system_msgs = [m for m in messages if isinstance(m, SystemMessage)]
    other_msgs = [m for m in messages if not isinstance(m, SystemMessage)]

    # 计算 token 数
    total_tokens = sum(len(enc.encode(m.content)) for m in other_msgs)

    # 如果超过限制，从前面开始删除
    while total_tokens > max_tokens and other_msgs:
        removed = other_msgs.pop(0)
        total_tokens -= len(enc.encode(removed.content))

    return system_msgs + other_msgs

# 在聊天函数中使用
def chatbot_with_token_limit(state: State):
    messages = state["messages"]

    # 限制 token 数量
    messages = trim_messages_by_tokens(messages, max_tokens=3000)

    response = llm.invoke(messages)
    return {"messages": [response]}
```

#### 方法3：使用滑动窗口

```python
def get_windowed_messages(
    messages: list[BaseMessage],
    window_size: int = 10
) -> list[BaseMessage]:
    """
    滑动窗口：保留最近的 N 轮对话

    Args:
        messages: 所有消息
        window_size: 窗口大小（轮数）
    """
    # 保留系统消息
    system_msgs = [m for m in messages if isinstance(m, SystemMessage)]
    other_msgs = [m for m in messages if not isinstance(m, SystemMessage)]

    # 每轮对话包含一个 Human 和一个 AI 消息
    # 保留最近的 window_size 轮
    if len(other_msgs) > window_size * 2:
        other_msgs = other_msgs[-(window_size * 2):]

    return system_msgs + other_msgs
```

### 3. 会话管理

#### 生成有意义的会话ID

```python
import uuid
from datetime import datetime

def generate_session_id(user_id: str, conversation_type: str = "chat") -> str:
    """
    生成会话ID

    Args:
        user_id: 用户ID
        conversation_type: 对话类型（chat, support, etc.）
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]

    return f"{user_id}_{conversation_type}_{timestamp}_{unique_id}"

# 使用
session_id = generate_session_id("user_123", "support")
# 输出: user_123_support_20260129_143022_a1b2c3d4
```

#### 定期清理过期会话

```python
import time
from typing import Dict

class SessionManager:
    """会话管理器，支持自动清理"""

    def __init__(self, ttl: int = 3600):
        """
        Args:
            ttl: 会话过期时间（秒）
        """
        self.sessions: Dict[str, InMemoryChatMessageHistory] = {}
        self.last_access: Dict[str, float] = {}
        self.ttl = ttl

    def get_session(self, session_id: str) -> InMemoryChatMessageHistory:
        """获取或创建会话"""
        if session_id not in self.sessions:
            self.sessions[session_id] = InMemoryChatMessageHistory()

        # 更新最后访问时间
        self.last_access[session_id] = time.time()

        return self.sessions[session_id]

    def cleanup_expired(self):
        """清理过期会话"""
        current_time = time.time()
        expired = [
            sid for sid, last_time in self.last_access.items()
            if current_time - last_time > self.ttl
        ]

        for sid in expired:
            del self.sessions[sid]
            del self.last_access[sid]

        return len(expired)

    def get_active_sessions(self) -> list[str]:
        """获取所有活跃会话"""
        self.cleanup_expired()
        return list(self.sessions.keys())

# 使用
manager = SessionManager(ttl=1800)  # 30分钟过期

def get_session_history(session_id: str):
    return manager.get_session(session_id)

# 定期清理（可以用定时任务）
import threading

def periodic_cleanup():
    while True:
        time.sleep(300)  # 每5分钟清理一次
        count = manager.cleanup_expired()
        print(f"Cleaned up {count} expired sessions")

# 启动清理线程
cleanup_thread = threading.Thread(target=periodic_cleanup, daemon=True)
cleanup_thread.start()
```

### 4. 错误处理和重试

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
def safe_chat(user_input: str, session_id: str):
    """带重试机制的聊天函数"""
    try:
        response = chain_with_history.invoke(
            {"input": user_input},
            config={"configurable": {"session_id": session_id}}
        )
        return response.content

    except Exception as e:
        print(f"Error in chat: {e}")
        # 可以选择清除会话或返回错误消息
        raise

# 使用
try:
    result = safe_chat("你好", session_id="user_001")
    print(result)
except Exception as e:
    print(f"Chat failed after retries: {e}")
```

### 5. 性能优化

#### 使用异步版本

```python
import asyncio

async def async_chat(user_input: str, session_id: str):
    """异步聊天"""
    response = await chain_with_history.ainvoke(
        {"input": user_input},
        config={"configurable": {"session_id": session_id}}
    )
    return response.content

# 批量处理
async def batch_chat(inputs: list[tuple[str, str]]):
    """批量处理多个聊天请求"""
    tasks = [
        async_chat(user_input, session_id)
        for user_input, session_id in inputs
    ]
    return await asyncio.gather(*tasks)

# 使用
inputs = [
    ("你好", "user_001"),
    ("天气怎么样", "user_002"),
    ("讲个笑话", "user_003")
]
results = asyncio.run(batch_chat(inputs))
```

#### 使用连接池

```python
from psycopg_pool import ConnectionPool

# PostgreSQL 连接池
pool = ConnectionPool(
    conninfo="postgresql://user:password@localhost:5432/dbname",
    min_size=2,
    max_size=10,
    timeout=30
)

def get_session_history(session_id: str):
    return PostgresChatMessageHistory(
        session_id=session_id,
        connection=pool.getconn(),  # 从池中获取连接
        table_name="chat_history"
    )
```

#### 缓存常用响应

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def get_cached_response(user_input: str) -> str:
    """缓存常见问题的回复"""
    # 对于常见问题，直接返回缓存的回复
    common_responses = {
        "你好": "你好！有什么我可以帮助你的吗？",
        "谢谢": "不客气！很高兴能帮到你。",
    }
    return common_responses.get(user_input)

def chat_with_cache(user_input: str, session_id: str):
    """带缓存的聊天"""
    # 先检查缓存
    cached = get_cached_response(user_input)
    if cached:
        return cached

    # 否则调用 LLM
    return chat(user_input, session_id)
```

### 6. 监控和日志

```python
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def chat_with_logging(user_input: str, session_id: str):
    """带日志的聊天函数"""
    start_time = datetime.now()

    logger.info(f"Chat request - Session: {session_id}, Input: {user_input[:50]}...")

    try:
        response = chain_with_history.invoke(
            {"input": user_input},
            config={"configurable": {"session_id": session_id}}
        )

        duration = (datetime.now() - start_time).total_seconds()
        logger.info(f"Chat success - Session: {session_id}, Duration: {duration:.2f}s")

        return response.content

    except Exception as e:
        duration = (datetime.now() - start_time).total_seconds()
        logger.error(
            f"Chat failed - Session: {session_id}, "
            f"Duration: {duration:.2f}s, Error: {str(e)}"
        )
        raise

# 使用
result = chat_with_logging("你好", session_id="user_001")
```

### 7. 安全性

#### 会话隔离

```python
def validate_session_access(user_id: str, session_id: str) -> bool:
    """验证用户是否有权访问该会话"""
    # 检查 session_id 是否属于该用户
    return session_id.startswith(f"{user_id}_")

def secure_chat(user_input: str, user_id: str, session_id: str):
    """安全的聊天函数"""
    # 验证访问权限
    if not validate_session_access(user_id, session_id):
        raise PermissionError("Unauthorized access to session")

    return chat(user_input, session_id)
```

#### 输入验证

```python
def sanitize_input(user_input: str) -> str:
    """清理用户输入"""
    # 限制长度
    max_length = 1000
    if len(user_input) > max_length:
        user_input = user_input[:max_length]

    # 移除危险字符（根据需要调整）
    # user_input = user_input.replace("<script>", "")

    return user_input.strip()

def safe_chat_with_validation(user_input: str, session_id: str):
    """带输入验证的聊天"""
    # 清理输入
    user_input = sanitize_input(user_input)

    if not user_input:
        return "请输入有效的消息"

    return chat(user_input, session_id)
```

---

## 常见问题

### Q1: 如何在不同用户之间隔离对话？

使用唯一的 `session_id` 或 `thread_id`：

```python
# 方式1：每个用户一个会话
session_id = f"user_{user_id}"

# 方式2：每个对话一个会话（推荐）
session_id = f"user_{user_id}_conv_{conversation_id}"

# 方式3：包含时间戳
from datetime import datetime
session_id = f"user_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
```

### Q2: 如何实现对话摘要以节省 token？

```python
from langchain.chains.summarize import load_summarize_chain
from langchain_core.messages import SystemMessage

def summarize_old_messages(messages: list[BaseMessage], llm) -> str:
    """将旧消息总结为摘要"""
    if len(messages) < 10:
        return None

    # 提取需要总结的消息
    old_messages = messages[:-5]  # 保留最近5条

    # 构建总结提示
    text = "\n".join([f"{m.type}: {m.content}" for m in old_messages])

    summary_prompt = f"""请简要总结以下对话的关键信息：

{text}

总结："""

    summary = llm.invoke([HumanMessage(content=summary_prompt)])

    return summary.content

def chatbot_with_summary(state: State):
    """带摘要功能的聊天机器人"""
    messages = state["messages"]

    # 如果消息太多，进行总结
    if len(messages) > 20:
        summary = summarize_old_messages(messages[:-5], llm)

        # 用摘要替换旧消息
        messages = [
            SystemMessage(content=f"之前的对话摘要：{summary}")
        ] + messages[-5:]

    response = llm.invoke(messages)
    return {"messages": [response]}
```

### Q3: 如何导出和导入对话历史？

```python
import json
from langchain_core.messages import message_to_dict, messages_from_dict

# 导出
def export_history(session_id: str, filename: str):
    """导出会话历史到 JSON 文件"""
    history = get_session_history(session_id)

    # 转换为字典
    messages_dict = [message_to_dict(m) for m in history.messages]

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(messages_dict, f, ensure_ascii=False, indent=2)

    print(f"Exported {len(messages_dict)} messages to {filename}")

# 导入
def import_history(session_id: str, filename: str):
    """从 JSON 文件导入会话历史"""
    with open(filename, 'r', encoding='utf-8') as f:
        messages_dict = json.load(f)

    # 转换回消息对象
    messages = messages_from_dict(messages_dict)

    # 清空并重新添加
    history = get_session_history(session_id)
    history.clear()

    for msg in messages:
        history.add_message(msg)

    print(f"Imported {len(messages)} messages to session {session_id}")

# 使用
export_history("user_001", "chat_history_user_001.json")
import_history("user_002", "chat_history_user_001.json")
```

### Q4: 如何实现多轮对话的上下文压缩？

```python
from langchain_core.messages import BaseMessage, SystemMessage

def compress_context(
    messages: list[BaseMessage],
    max_tokens: int = 3000,
    llm=None
) -> list[BaseMessage]:
    """
    智能压缩上下文

    策略：
    1. 保留系统消息
    2. 保留最近的 N 条消息
    3. 总结中间的消息
    """
    from tiktoken import encoding_for_model

    enc = encoding_for_model("gpt-4")

    # 分离系统消息和其他消息
    system_msgs = [m for m in messages if isinstance(m, SystemMessage)]
    other_msgs = [m for m in messages if not isinstance(m, SystemMessage)]

    # 计算 token
    def count_tokens(msgs):
        return sum(len(enc.encode(m.content)) for m in msgs)

    total_tokens = count_tokens(other_msgs)

    # 如果不超过限制，直接返回
    if total_tokens <= max_tokens:
        return messages

    # 保留最近的消息
    recent_msgs = other_msgs[-6:]  # 最近3轮对话
    recent_tokens = count_tokens(recent_msgs)

    # 如果最近的消息就超过限制，只能裁剪
    if recent_tokens > max_tokens:
        while recent_tokens > max_tokens and recent_msgs:
            recent_msgs.pop(0)
            recent_tokens = count_tokens(recent_msgs)
        return system_msgs + recent_msgs

    # 总结中间的消息
    old_msgs = other_msgs[:-6]
    if old_msgs and llm:
        summary_text = "\n".join([f"{m.type}: {m.content}" for m in old_msgs])
        summary_prompt = f"请简要总结以下对话：\n{summary_text}"

        summary = llm.invoke([HumanMessage(content=summary_prompt)])
        summary_msg = SystemMessage(content=f"早期对话摘要：{summary.content}")

        return system_msgs + [summary_msg] + recent_msgs

    # 如果没有 LLM，只保留最近的消息
    return system_msgs + recent_msgs

# 在聊天函数中使用
def chatbot_with_compression(state: State):
    messages = state["messages"]

    # 压缩上下文
    messages = compress_context(messages, max_tokens=3000, llm=llm)

    response = llm.invoke(messages)
    return {"messages": [response]}
```

### Q5: 如何在 Flask/FastAPI 中使用？

#### Flask 示例

```python
from flask import Flask, request, jsonify, session
from flask_cors import CORS

app = Flask(__name__)
app.secret_key = "your-secret-key"
CORS(app)

# 全局会话管理器
session_manager = SessionManager(ttl=1800)

def get_session_history(session_id: str):
    return session_manager.get_session(session_id)

# 创建链
chain_with_history = RunnableWithMessageHistory(
    chain,
    get_session_history,
    input_messages_key="input",
    history_messages_key="history"
)

@app.route('/chat', methods=['POST'])
def chat():
    """聊天接口"""
    data = request.json
    user_input = data.get('message')
    session_id = data.get('session_id')

    if not user_input:
        return jsonify({'error': 'Message is required'}), 400

    if not session_id:
        # 生成新的 session_id
        import uuid
        session_id = str(uuid.uuid4())

    try:
        response = chain_with_history.invoke(
            {"input": user_input},
            config={"configurable": {"session_id": session_id}}
        )

        return jsonify({
            'response': response.content,
            'session_id': session_id
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/chat/stream', methods=['POST'])
def chat_stream():
    """流式聊天接口"""
    from flask import Response, stream_with_context

    data = request.json
    user_input = data.get('message')
    session_id = data.get('session_id')

    def generate():
        for chunk in chain_with_history.stream(
            {"input": user_input},
            config={"configurable": {"session_id": session_id}}
        ):
            yield f"data: {chunk.content}\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream'
    )

@app.route('/history/<session_id>', methods=['GET'])
def get_history(session_id):
    """获取会话历史"""
    try:
        history = get_session_history(session_id)
        messages = [
            {"type": m.type, "content": m.content}
            for m in history.messages
        ]
        return jsonify({'messages': messages})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/history/<session_id>', methods=['DELETE'])
def clear_history(session_id):
    """清除会话历史"""
    try:
        history = get_session_history(session_id)
        history.clear()
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
```

#### FastAPI 示例

```python
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uuid

app = FastAPI()

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局会话管理器
session_manager = SessionManager(ttl=1800)

def get_session_history(session_id: str):
    return session_manager.get_session(session_id)

# 创建链
chain_with_history = RunnableWithMessageHistory(
    chain,
    get_session_history,
    input_messages_key="input",
    history_messages_key="history"
)

# 请求模型
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """聊天接口"""
    # 生成或使用现有 session_id
    session_id = request.session_id or str(uuid.uuid4())

    try:
        response = await chain_with_history.ainvoke(
            {"input": request.message},
            config={"configurable": {"session_id": session_id}}
        )

        return ChatResponse(
            response=response.content,
            session_id=session_id
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/chat/stream")
async def chat_stream(message: str, session_id: str):
    """流式聊天接口"""
    from fastapi.responses import StreamingResponse

    async def generate():
        async for chunk in chain_with_history.astream(
            {"input": message},
            config={"configurable": {"session_id": session_id}}
        ):
            yield f"data: {chunk.content}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream"
    )

@app.get("/history/{session_id}")
async def get_history(session_id: str):
    """获取会话历史"""
    try:
        history = get_session_history(session_id)
        messages = [
            {"type": m.type, "content": m.content}
            for m in history.messages
        ]
        return {"messages": messages}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/history/{session_id}")
async def clear_history(session_id: str):
    """清除会话历史"""
    try:
        history = get_session_history(session_id)
        history.clear()
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sessions")
async def list_sessions():
    """列出所有活跃会话"""
    return {"sessions": session_manager.get_active_sessions()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### Q6: 如何处理并发请求？

```python
import asyncio
from asyncio import Semaphore

# 创建信号量限制并发数
semaphore = Semaphore(10)  # 最多10个并发请求

async def chat_with_concurrency_limit(user_input: str, session_id: str):
    """限制并发的聊天函数"""
    async with semaphore:
        response = await chain_with_history.ainvoke(
            {"input": user_input},
            config={"configurable": {"session_id": session_id}}
        )
        return response.content

# 使用
async def main():
    tasks = [
        chat_with_concurrency_limit(f"问题{i}", f"user_{i}")
        for i in range(100)
    ]
    results = await asyncio.gather(*tasks)
    return results
```

### Q7: 如何实现多语言支持？

```python
def create_multilingual_prompt(language: str = "zh"):
    """创建多语言提示"""
    system_messages = {
        "zh": "你是一个有帮助的中文助手。",
        "en": "You are a helpful English assistant.",
        "ja": "あなたは親切な日本語アシスタントです。",
    }

    return ChatPromptTemplate.from_messages([
        ("system", system_messages.get(language, system_messages["en"])),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{input}")
    ])

def chat_multilingual(user_input: str, session_id: str, language: str = "zh"):
    """多语言聊天"""
    prompt = create_multilingual_prompt(language)
    chain = prompt | llm

    chain_with_history = RunnableWithMessageHistory(
        chain,
        get_session_history,
        input_messages_key="input",
        history_messages_key="history"
    )

    response = chain_with_history.invoke(
        {"input": user_input},
        config={"configurable": {"session_id": session_id}}
    )

    return response.content
```

---

## 参考资源

### 官方文档
- [LangChain 官方文档 - Message History](https://python.langchain.com/docs/how_to/message_history/)
- [LangGraph 官方文档](https://langchain-ai.github.io/langgraph/)
- [LangGraph - Add Memory Tutorial](https://langchain-ai.github.io/langgraph/tutorials/get-started/3-add-memory/)
- [LangGraph - Persistence](https://langchain-ai.github.io/langgraph/concepts/persistence/)
- [Long-Term Memory in LangGraph](https://blog.langchain.dev/launching-long-term-memory-support-in-langgraph/)

### 相关资源
- [LangChain Expression Language (LCEL)](https://python.langchain.com/docs/expression_language/)
- [Migrating from ConversationalChain](https://python.langchain.com/docs/versions/migrating_chains/conversation_chain/)
- [Chat Message Histories](https://python.langchain.com/docs/integrations/memory/)

### 社区资源
- [LangChain GitHub](https://github.com/langchain-ai/langchain)
- [LangGraph GitHub](https://github.com/langchain-ai/langgraph)
- [LangChain Discord](https://discord.gg/langchain)

---

## 总结

### 快速选择指南

1. **新项目，需要复杂流程**
   ```python
   # 使用 LangGraph Checkpointer
   from langgraph.checkpoint.memory import MemorySaver
   app = workflow.compile(checkpointer=MemorySaver())
   ```

2. **简单对话，快速开发**
   ```python
   # 使用 RunnableWithMessageHistory
   chain_with_history = RunnableWithMessageHistory(
       chain, get_session_history,
       input_messages_key="input",
       history_messages_key="history"
   )
   ```

3. **生产环境**
   ```python
   # 使用 PostgreSQL 持久化
   from langgraph.checkpoint.postgres import PostgresSaver
   checkpointer = PostgresSaver.from_conn_string("postgresql://...")
   app = workflow.compile(checkpointer=checkpointer)
   ```

### 关键要点

1. ✅ **使用新的 API**：避免使用已弃用的 `ConversationBufferMemory` 等类
2. ✅ **限制历史长度**：防止 token 超限和成本过高
3. ✅ **使用持久化存储**：生产环境避免使用内存存储
4. ✅ **会话隔离**：使用唯一的 session_id/thread_id
5. ✅ **错误处理**：添加重试和异常处理机制
6. ✅ **性能优化**：使用异步、连接池、缓存等技术
7. ✅ **安全性**：验证会话访问权限，清理用户输入

---

**文档版本**: 2.0
**更新日期**: 2026-01-29
**适用版本**: langchain-core >= 1.0.0, langgraph >= 0.2.0
**测试版本**: langchain-core 1.2.7, langchain-community 0.4.1
