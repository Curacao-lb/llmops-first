import sys
import dotenv
from openai import OpenAI
from typing import Any

dotenv.load_dotenv()


class ConversationSummaryBufferMemory:
    """摘要缓冲混合记忆类（模拟 LangChain 0.x 版本）"""

    def __init__(
        self, summary: str = "", chat_history: list = None, max_token: int = 300
    ):
        """
        初始化摘要缓冲混合记忆
        :param summary: 初始摘要
        :param chat_history: 初始对话历史
        :param max_token: token 阈值，超过则生成摘要
        """
        self.summary = summary
        self.chat_history = [] if chat_history is None else chat_history
        self.max_token = max_token
        self._client = OpenAI(base_url="https://hk.xty.app/v1")

    @classmethod
    def get_num_tokens(cls, query: str) -> int:
        """计算传入的 query 的 token 数（简化版，用字符数代替）"""
        return len(query)

    def save_context(self, human_query: str, ai_content: str) -> None:
        """
        保存传入的新一次的对话信息
        :param human_query: 用户输入
        :param ai_content: AI 回复
        """
        # 1. 添加到历史记忆
        self.chat_history.append({"human": human_query, "ai": ai_content})

        # 2. 将历史记忆转换为文本
        buffer_string = self.get_buffer_string()

        # 3. 计算 token 数
        tokens = self.get_num_tokens(buffer_string)

        # 4. 如果超过阈值，生成摘要
        if tokens > self.max_token:
            first_chat = self.chat_history[0]
            print("\n[摘要生成中...]")
            self.summary_text(
                self.summary,
                f"Human: {first_chat.get('human')}\nAI: {first_chat.get('ai')}",
            )
            print(f"[新摘要生成成功]: {self.summary}\n")
            # 删除已摘要的对话
            del self.chat_history[0]

    def get_buffer_string(self) -> str:
        """将历史对话转换成字符串"""
        buffer: str = ""
        for chat in self.chat_history:
            buffer += f"Human: {chat.get('human')}\nAI: {chat.get('ai')}\n\n"
        return buffer.strip()

    def load_memory_variables(self) -> dict[str, Any]:
        """加载记忆变量为一个字典，便于格式化到 prompt"""
        buffer_string = self.get_buffer_string()
        if self.summary:
            return {
                "chat_history": f"历史对话摘要：{self.summary}\n\n最近对话：\n{buffer_string}\n"
            }
        else:
            return {"chat_history": f"最近对话：\n{buffer_string}\n"}

    def summary_text(self, origin_summary: str, new_line: str) -> str:
        """
        用于将旧的摘要和传入的对话生成新摘要
        :param origin_summary: 旧摘要
        :param new_line: 新对话
        :return: 新摘要
        """
        prompt = f"""你是一个强大的聊天机器人，请根据用户提供的谈话内容，总结摘要，并将其添加到先前提供的摘要中，返回一个新的摘要，除了新摘要其他任何数据都不要生成。

如果用户的对话信息里有一些关键的信息，比方说姓名、爱好、性别、重要事件等等，这些全部都要包括在生成的摘要中，摘要尽可能要还原用户的对话记录。

请不要将<example>标签里的数据当成实际的数据，这里的数据只是一个示例数据，告诉你该如何生成新摘要。

<example>
当前摘要：人类会问人工智能对人工智能的看法，人工智能认为人工智能是一股向善的力量。

新的对话：
Human: 为什么你认为人工智能是一股向善的力量？
AI: 因为人工智能会帮助人类充分发挥潜力。

新摘要：人类会问人工智能对人工智能的看法，人工智能认为人工智能是一股向善的力量，因为它将帮助人类充分发挥潜力。
</example>

=====================以下的数据是实际需要处理的数据=====================

当前摘要：{origin_summary if origin_summary else "无"}

新的对话：
{new_line}

请帮用户将上面的信息生成新摘要。"""

        completion = self._client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
        )
        self.summary = completion.choices[0].message.content
        return self.summary


# ==================== 主程序 ====================

# 1. 创建 OpenAI 客户端
client = OpenAI(base_url="https://hk.xty.app/v1")

# 2. 初始化记忆类（max_token=300，超过则生成摘要）
memory = ConversationSummaryBufferMemory("", [], 300)

print("=" * 60)
print("ConversationSummaryBufferMemory 演示（0.x 版本风格）")
print("当历史对话 token 数超过 300 时，会自动生成摘要")
print("输入 'q' 退出")
print("=" * 60)

# 3. 创建一个死循环用于人机对话
while True:
    # 获取人类的输入
    query = input("\nHuman: ")

    # 判断下是否输入的是 q，如果是则退出
    if query == "q":
        break

    # 格式化创建一个提示模板
    memory_variables = memory.load_memory_variables()
    answer_prompt = (
        "你是一个强大的聊天机器人，请根据对应的上下文和用户提问解决问题。\n\n"
        f"{memory_variables.get('chat_history')}\n\n"
        f"用户的提问是：{query}"
    )

    # 向 openai 接口发起请求获取 AI 生成的内容
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": answer_prompt}],
        stream=True,
    )

    # 通过 for 循环流式读取响应的内容
    print("AI: ", end="", flush=True)
    sys.stdout.flush()

    ai_content = ""
    for r in response:
        content = r.choices[0].delta.content
        if content is None:
            continue
        ai_content += content
        print(content, flush=True, end="")
        sys.stdout.flush()
    print("")

    # 将本轮对话保存到记忆中
    memory.save_context(query, ai_content)

    # 打印调试信息
    buffer_string = memory.get_buffer_string()
    current_tokens = memory.get_num_tokens(buffer_string)
    print(f"\n[DEBUG] 当前历史对话 token 数: {current_tokens}/{memory.max_token}")
    print(f"[DEBUG] 当前摘要: {memory.summary if memory.summary else '(无)'}")
    print(f"[DEBUG] 历史对话条数: {len(memory.chat_history)}")
