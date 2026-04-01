from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
import json
import os
# 持久化记忆文件路径
MEMORY_FILE = "chat_memory.json"

model = ChatOpenAI(
    model="gpt-5.2",
    temperature=0.7,
    timeout=30,
    max_tokens=1000,
    max_retries=6,
    api_key='ailab_W/h3qmrgTdsks8ngpKr++gZ4h49d7KxQDm/6ewJQeM1R9qyvCD8Gi4DgZnTPB6UcUNCtsTw4JUgUoAOAVxzWbvgU1qog1c0JqY68zu1wDZFwTqEDEsdobFQ=',
    base_url='https://lab.iwhalecloud.com/gpt-proxy/v1',
)

# 定义结构化输出的 schema
qa_schema = {
    "title": "QuestionAnswer",
    "type": "object",
    "description": "Question and answer pair.",
    "properties": {
        "question": {"type": "string", "description": "The user's question"},
        "answer": {"type": "string", "description": "The assistant's answer to the question"}
    },
    "required": ["question", "answer"]
}

# 创建结构化输出模型
structured_model = model.with_structured_output(qa_schema)

# 系统消息
system_msg = SystemMessage(content="你是一个有20年开发经验的程序员，请认真回答用户的问题。你的手机号是12345678901，邮箱是yang@gmail.com，名字叫杨帆。")

# 对话历史列表
conversation_history = []

# 记忆配置
MAX_HISTORY_PAIRS = 10  # 最多保留最近10轮对话（压缩策略）

# 加载持久化的记忆
def load_memory():
    """从文件加载历史记忆"""
    global conversation_history
    file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), MEMORY_FILE)
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                conversation_history = data.get('history', [])
                print(f"已加载 {len(conversation_history)} 轮历史对话 (from {file_path})")
        except Exception as e:
            print(f"加载记忆失败: {e}")
            conversation_history = []
    else:
        print(f"未找到历史记忆文件，将创建新的记忆")

# 保存记忆到文件
def save_memory():
    """将记忆保存到文件"""
    try:
        # 获取绝对路径
        file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), MEMORY_FILE)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump({'history': conversation_history}, f, ensure_ascii=False, indent=2)
        print(f"（记忆已保存到: {file_path}）")
    except Exception as e:
        print(f"保存记忆失败: {e}")

# 压缩记忆（保留最近的N轮对话）
def compress_memory():
    """保留最近的对话，删除更早的对话"""
    global conversation_history
    if len(conversation_history) > MAX_HISTORY_PAIRS:
        # 只保留最近的对话
        removed_count = len(conversation_history) - MAX_HISTORY_PAIRS
        conversation_history = conversation_history[-MAX_HISTORY_PAIRS:]
        print(f"（已自动压缩记忆，删除了 {removed_count} 轮旧对话）")

# 构建消息列表
def build_messages(user_input):
    """根据历史记忆构建完整的消息列表"""
    messages = [system_msg]

    # 添加历史对话
    for qa in conversation_history:
        messages.append(HumanMessage(content=qa['question']))
        messages.append(AIMessage(content=qa['answer']))

    # 添加当前用户输入
    messages.append(HumanMessage(content=user_input))

    return messages

# 启动时加载记忆
load_memory()

print("聊天机器人已启动（输入 'exit' 或 'quit' 退出，输入 'clear' 清除记忆）")
print(f"当前记忆策略：保留最近 {MAX_HISTORY_PAIRS} 轮对话")
print("=" * 50)

# 循环对话
while True:
    # 用户输入
    user_input = input("\n你: ")

    # 退出条件
    if user_input.lower() in ['exit', 'quit', '退出']:
        save_memory()  # 退出前保存记忆
        print("记忆已保存，再见！")
        break

    # 清除记忆
    if user_input.lower() == 'clear':
        conversation_history = []
        file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), MEMORY_FILE)
        if os.path.exists(file_path):
            os.remove(file_path)
        print("记忆已清除！")
        continue

    # 构建消息列表
    messages = build_messages(user_input)

    # 获取结构化输出结果
    result = structured_model.invoke(messages)

    # 显示结果
    print("\n助手回复（结构化输出）:")
    print(f"  问题: {result['question']}")
    print(f"  回答: {result['answer']}")

    # 保存到对话历史
    conversation_history.append({
        'question': user_input,
        'answer': result['answer']
    })

    # 压缩记忆
    compress_memory()

    # 保存到文件
    save_memory()