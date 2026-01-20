#!/use/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   :2026/1/20 16:13
@Author :yange2615@gmail.com
@File   :stady
"""
import os
from typing import Any
from uuid import UUID

from langchain_core.outputs import GenerationChunk, ChatGenerationChunk
from pydantic import BaseModel,Field


import dotenv
from langchain_qwq import ChatQwen
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.callbacks import StdOutCallbackHandler, BaseCallbackHandler


# 将env加载到环境变量中
dotenv.load_dotenv()

class LLMopsCallbackHandler(BaseCallbackHandler):
    def on_llm_start(self, serialized, prompts, **kwargs):
        print("LLM开始处理请求...")

    def on_llm_end(self, response, **kwargs):
        print("LLM处理请求结束。")

    def on_llm_error(self, error, **kwargs):
        print(f"LLM处理请求时出错: {error}")
    def on_llm_new_token(
        self,
        token: str,
        *,
        chunk: GenerationChunk | ChatGenerationChunk | None = None,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> Any:
        print('on_llm_new_token',token)

class Joke(BaseModel):
    joke: str = Field(description="回答用户的冷笑话")
    punchline: str= Field(description="冷笑话的笑点")

prompt = ChatPromptTemplate.from_template("""
            你是一个超级搞笑的脱口秀演员，请认真回答用户的问题。
            {format_instructions}
            用户问题: {query}
        """)

llm = ChatQwen(
    model="qwen-plus",
    max_tokens=3_000,
    timeout=None,
    max_retries=2,
    api_key=os.environ.get('DASHSCOPE_API_KEY'),
    base_url=os.environ.get('DASHSCOPE_BASE_URL'),
    callbacks=[StdOutCallbackHandler(),LLMopsCallbackHandler()]
)

chain = prompt | llm
parser = JsonOutputParser(pydantic_object=Joke)
response = chain.invoke({
    "query": "讲一个冷笑话",
    "format_instructions": parser.get_format_instructions()
})