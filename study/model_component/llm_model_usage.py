import dotenv
from langchain_core.prompts import ChatPromptTemplate
from datetime import datetime
from langchain_openai import ChatOpenAI

dotenv.load_dotenv()


# 1.编排prompt
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "你是我开发的聊天机器人，请回答用户问题，现在的时间是{now}"),
        ("user", "{question}"),
    ]
).partial(now=datetime.now())

# 2.创建大语言模型
llm = ChatOpenAI(model="gpt-3.5-turbo")

ai_message = llm.invoke(
    prompt.invoke({"question": "请问现在是几点，请将一个中式冷笑话"})
)

# 3.输出
print(ai_message.content)
print(ai_message.type)  # ai

"""
{'token_usage':
 {'completion_tokens': 167, 'prompt_tokens': 67, 'total_tokens': 234, 'completion_tokens_details': None, 'prompt_tokens_details': None}, 
 'model_provider': 'openai',
  'model_name': 'gpt-3.5-turbo-0613',
  'system_fingerprint': 'fp_b28b39ffa8', 
  'id': 'chatcmpl-TYZVWbEJmovxd9pigzaxCovuwTjwq', 
  'finish_reason': 'stop', 'logprobs': None}
"""
print(ai_message.response_metadata)
