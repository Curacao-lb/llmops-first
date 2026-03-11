"""旧版 memory_debug 实现（手动管理历史）"""

import os
import uuid
from flask import request
from openai import APIError, APITimeoutError, APIConnectionError

from internal.schema.app_schema import CompletionReq
from pkg.response import success_json, validate_error_json, fail_json
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser


def memory_debug_legacy(self, app_id: uuid.UUID):
    """
    旧版带记忆聊天接口（手动管理历史）

    注意：该函数依赖调用者对象包含：
    - get_session_history(session_id)
    - message_trimmer
    - memory_storage_path
    """
    req = CompletionReq()
    if not req.validate():
        return validate_error_json(req.errors)

    query = request.json.get("query")
    session_id = request.json.get("session_id", "default_session")

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "你是OpenAI开发的聊天机器人，请根据对应的上下文回复用户问题",
            ),
            MessagesPlaceholder("history"),
            ("human", "{query}"),
        ]
    )

    llm = ChatOpenAI(
        model="gpt-3.5-turbo",
        timeout=60.0,
    )
    parser = StrOutputParser()

    history = self.get_session_history(session_id)
    messages = history.messages
    trimmed_messages = self.message_trimmer.invoke(messages)
    chain = prompt | llm | parser

    try:
        content = chain.invoke({"query": query, "history": trimmed_messages})

        history.add_user_message(query)
        history.add_ai_message(content)

        return success_json(
            {
                "content": content,
                "debug_info": {
                    "session_id": session_id,
                    "storage_path": os.path.join(
                        self.memory_storage_path, f"chat_history_{session_id}.json"
                    ),
                    "total_messages": len(history.messages),
                    "trimmed_messages": len(trimmed_messages),
                    "window_size": 6,
                    "storage_type": "file",
                    "note": "对话历史已保存到文件，服务重启后不会丢失",
                },
            }
        )

    except APITimeoutError:
        return fail_json({"message": "请求超时，请稍后重试"})
    except APIConnectionError:
        return fail_json({"message": "无法连接到AI服务，请检查网络或稍后重试"})
    except APIError as e:
        return fail_json({"message": f"AI服务异常: {str(e)}"})
