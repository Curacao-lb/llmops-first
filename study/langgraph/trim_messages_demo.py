import dotenv
from langchain_core.messages import HumanMessage, AIMessage, trim_messages
from langchain_openai import ChatOpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter

dotenv.load_dotenv()

messages = [
    HumanMessage(content="你好，我想了解一下人工智能的发展历史。你能给我讲讲吗？"),
    AIMessage(
        content=[
            {
                "type": "text",
                "text": "当然可以！人工智能的发展经历了几个重要阶段。从20世纪50年代的图灵测试开始，AI 就成为了一个重要的研究领域。在60-70年代，专家系统的出现标志着 AI 的第一个高潮。",
            },
            {
                "type": "text",
                "text": "随后的几十年里，机器学习和深度学习技术的发展推动了 AI 的进步。特别是在最近十年，随着大数据和计算能力的提升，深度学习在图像识别、自然语言处理等领域取得了突破性进展。",
            },
        ]
    ),
    HumanMessage(content="那么现在 AI 技术的主要应用领域有哪些呢？"),
    AIMessage(
        content="现在 AI 技术已经广泛应用于多个领域。在医疗健康方面，AI 可以帮助诊断疾病和开发新药。在金融领域，AI 用于风险评估和交易决策。在教育方面，AI 可以提供个性化学习体验。此外，自动驾驶、智能家居、推荐系统等也都是 AI 的重要应用。"
    ),
]

llm = ChatOpenAI(model="gpt-4o-mini")

update_messages = trim_messages(
    messages,
    max_tokens=80,
    token_counter=llm,
    strategy="first",
    allow_partial=True,
    text_splitter=RecursiveCharacterTextSplitter(),
)

print(update_messages)
