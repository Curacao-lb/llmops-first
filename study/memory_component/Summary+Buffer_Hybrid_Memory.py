import sys
import dotenv
from openai import OpenAI
from typing import Any

dotenv.load_dotenv()


class ConversationSummaryBufferMemory:
    """摘要缓冲混合记忆类"""

    # 1. max_token用于判断是否需要生成新的摘要
    # 2. summary用于存储摘要的信息
    # 3. chat_history 用于存储历史对话
    # 4. get_num_tokens，用于计算传入文本的token数
    # 5. save_context函数用于存储新的交流对话
    # 6. get_buffer_stream，用于将历史对话转换成字符串
    # 7. load_memory_variables，用于加载记忆变量信息
    # 8. summary_text, 用于将旧的摘要和传入的对话生成新摘要。
    def __init__(
        self, summary: str = "", chat_history: list = None, max_token: int = 300
    ):
        self.summary = summary
        self.chat_history = [] if chat_history is None else chat_history
        self.max_token = max_token
        self._client = OpenAI(base_url="https://hk.xty.app/v1")

    @classmethod
    def get_num_tokens(cls, query: str) -> int:
        """计算传入的query的token数"""
        return len(query)

    def save_context(self, human_query: str, ai_content: str) -> None:
        """保存传入的新一次的对话信息"""
        # 历史记忆中去添加对应的信息
        self.chat_history.append({"human": human_query, "ai": ai_content})
        # 将历史记忆转换为文本
        buffer_string = self.get_buffer_string()

        tokens = self.get_num_tokens(buffer_string)

        if tokens > self.max_token:
            first_chat = self.chat_history[0]
            print("新摘要生成中")
            self.summary_text(
                self.summary,
                f"Human:{first_chat.get("human")}\nAI:{first_chat.get("ai")}",
            )
            print("新摘要生成成功", self.summary)
            del self.chat_history[0]

    def get_buffer_string(self) -> str:
        """将历史对话转换成字符串"""
        buffer: str = ""
        for chat in self.chat_history:
            buffer += f"Human:{chat.get('human')}\nAI:{chat.get('ai')}\n\n"
        return buffer.strip()

    def load_memory_variables(self) -> dict[str, Any]:
        """加载记忆变量为一个字典，便于格式化到prompt"""
        buffer_string = self.get_buffer_string()
        return {"chat_history": f"摘要:{self.summary}\n\n历史信息:{buffer_string}\n"}

    def summary_text(self, origin_summary: str, new_line: str) -> str:
        """用于将旧的摘要和传入的对话生成新摘要"""
        prompt = f"""你是一个强大的聊天机器人，请根据用户提供的谈话内容，总结摘要，并将其添加到先前提供的摘要中，返回一个新的摘要，除了新摘要其他任何数据都不要生成，如果用户的对话信息里有一些关键的信息，比方说姓名、爱好、性别、重要事件等等，这些全部都要包括在生成的摘要中，摘要尽可能要还原用户的对话记录。

        请不要将<example>标签里的数据当成实际的数据，这里的数据只是一个示例数据，告诉你该如何生成新摘要。

        <example>
        当前摘要：人类会问人工智能对人工智能的看法，人工智能认为人工智能是一股向善的力量。

        新的对话：
        Human：为什么你认为人工智能是一股向善的力量？
        AI：因为人工智能会帮助人类充分发挥潜力。

        新摘要：人类会问人工智能对人工智能的看法，人工智能认为人工智能是一股向善的力量，因为它将帮助人类充分发挥潜力。
        </example>

        =====================以下的数据是实际需要处理的数据=====================

        当前摘要：{origin_summary}

        新的对话：
        {new_line}

        请帮用户将上面的信息生成新摘要。"""

        completion = self._client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
        )
        self.summary = completion.choices[0].message.content
        return self.summary


# 1.创建OpenAI客户端
client = OpenAI(base_url="https://hk.xty.app/v1")
# 1.5 初始化记忆类
memory = ConversationSummaryBufferMemory("", [], 300)

# 2.创建一个死循环用于人机对话
while True:
    # 3.获取人类的输入
    query = input("Human: ")

    # 4.判断下是否输入的是q，如果是则退出
    if query == "q":
        break

    # 4.5 格式化创建一个提示模板。将人类传递的数据格式化到模板中，生成对应真正的提示词，再将提示词传递给大语言模型。
    memory_variables = memory.load_memory_variables()
    answer_prompt = (
        "你是一个强大的聊天机器人，请根据对应的上下文和用户提问解决问题。\n\n"
        f"{memory_variables.get("chat_history")}\n\n"
        f"用户的提问是：{query}"
    )
    # 5.向openai接口发起请求获取AI生成的内容
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        # 传入 answer_prompt，这样的提问就带有历史提示信息了
        messages=[{"role": "user", "content": answer_prompt}],
        stream=True,
    )

    # 6.通过for循环流式读取响应的内容
    print("AI：", flush=True, end="")
    sys.stdout.flush()  # 强制刷新缓冲区

    # 每一次生成之后，将人类的query还有AI生成的内容添加回记忆中，生成新的摘要，并且添加到历史记忆中
    ai_content = ""
    for r in response:
        content = r.choices[0].delta.content
        if content is None:
            continue  # 改用 continue 而不是 break
        ai_content += content  # 修复：应该是 += content 而不是 += ai_content
        print(content, flush=True, end="")
        sys.stdout.flush()  # 每次输出后强制刷新
    print("")  # 换行
    memory.save_context(query, ai_content)

    # 打印当前消耗的token数
    buffer_string = memory.get_buffer_string()
    current_tokens = memory.get_num_tokens(buffer_string)
    print(f"[DEBUG] 当前历史对话token数: {current_tokens}/{memory.max_token}")
    print(f"[DEBUG] 当前摘要: {memory.summary if memory.summary else '(无)'}")
    print(f"[DEBUG] 历史对话条数: {len(memory.chat_history)}\n")
