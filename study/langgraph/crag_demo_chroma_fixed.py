"""
【CRAG (Corrective Retrieval Augmented Generation) - 纠正性检索增强生成】
使用 Chroma 作为向量数据库（轻量级，功能完整）
已修复：Chroma 导入和 TavilySearch 返回格式问题
"""

from typing import TypedDict, Any
import json

import dotenv
from langchain_tavily import TavilySearch
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langgraph.graph import StateGraph

# 使用新的 langchain-chroma 包，如果没有则使用旧的
try:
    from langchain_chroma import Chroma

    print("✅ 使用 langchain-chroma")
except ImportError:
    print("⚠️ 使用 langchain-community.vectorstores.Chroma")
    from langchain_community.vectorstores import Chroma

dotenv.load_dotenv()


# ==================== 1. 数据模型定义 ====================


class GradeDocument(BaseModel):
    """文档评分Pydantic模型"""

    binary_score: str = Field(description="文档与问题是否关联，请回答yes或者no")


class TavilySearchArgsSchema(BaseModel):
    """Tavily搜索工具的参数Schema"""

    query: str = Field(description="执行Tavily搜索的查询语句")


class GraphState(TypedDict):
    """图状态类型定义"""

    question: str
    generation: str
    web_search: str
    documents: list[Document]


# ==================== 2. 工具函数 ====================


def format_docs(docs: list[Document]) -> str:
    """将文档列表格式化为字符串"""
    return "\n\n".join([doc.page_content for doc in docs])


# ==================== 3. 核心组件初始化 ====================

# 3.1 创建大语言模型
llm = ChatOpenAI(model="gpt-4o-mini")

# 3.2 创建 Embeddings
embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small",
    check_embedding_ctx_length=False,
)

# 3.3 初始化 Chroma 向量数据库
print("\n初始化 Chroma 向量数据库...")
try:
    vector_store = Chroma(
        collection_name="crag_documents",
        embedding_function=embeddings,
        persist_directory="./chroma_db",
    )

    # 检查集合是否为空
    if vector_store._collection.count() == 0:
        print("⚠️ Chroma 集合为空，创建示例文档...")
        sample_docs = [
            Document(
                page_content="LLMOps 是大语言模型运维的缩写，涵盖模型训练、部署、监控等全生命周期管理。"
            ),
            Document(
                page_content="RAG（检索增强生成）是一种结合检索和生成的技术，能够提高LLM的准确性。"
            ),
            Document(
                page_content="向量数据库用于存储和检索高维向量，是RAG系统的核心组件。"
            ),
            Document(
                page_content="Chroma 是一个轻量级的向量数据库，支持本地和云端部署。"
            ),
        ]
        vector_store.add_documents(sample_docs)
        print("✅ 已添加示例文档到 Chroma")
    else:
        print(
            f"✅ 已加载 Chroma 数据库，包含 {vector_store._collection.count()} 个文档"
        )

except Exception as e:
    print(f"⚠️ 初始化 Chroma 失败: {e}")
    print("💡 创建新的 Chroma 数据库...")

    sample_docs = [
        Document(
            page_content="LLMOps 是大语言模型运维的缩写，涵盖模型训练、部署、监控等全生命周期管理。"
        ),
        Document(
            page_content="RAG（检索增强生成）是一种结合检索和生成的技术，能够提高LLM的准确性。"
        ),
        Document(
            page_content="向量数据库用于存储和检索高维向量，是RAG系统的核心组件。"
        ),
        Document(page_content="Chroma 是一个轻量级的向量数据库，支持本地和云端部署。"),
    ]

    vector_store = Chroma.from_documents(
        documents=sample_docs,
        embedding=embeddings,
        collection_name="crag_documents",
        persist_directory="./chroma_db",
    )
    print("✅ 已创建新的 Chroma 数据库")

# 3.4 创建检索器
retriever = vector_store.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 4},
)

# 3.5 构建检索评估器（CRAG核心：评估文档相关性）
system = """你是一名评估检索到的文档与用户问题相关性的评估员。
如果文档包含与问题相关的关键字或语义，请将其评级为相关。
给出一个是否相关得分为yes或者no，以表明文档是否与问题相关。"""
grade_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system),
        ("human", "检索文档: \n\n{document}\n\n用户问题: {question}"),
    ]
)
retrieval_grader = grade_prompt | llm.with_structured_output(GradeDocument)

# 3.6 构建RAG生成链
template = """你是一个问答任务的助理。使用以下检索到的上下文来回答问题。如果不知道就说不知道，不要胡编乱造，并保持答案简洁。

问题: {question}
上下文: {context}
答案: """
prompt = ChatPromptTemplate.from_template(template)
rag_chain = prompt | llm.bind(temperature=0) | StrOutputParser()

# 3.7 构建问题重写器
rewrite_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "你是一个将输入问题转换为优化的更好版本的问题重写器并用于网络搜索。请查看输入并尝试推理潜在的语义意图/含义。",
        ),
        ("human", "这里是初始化问题:\n\n{question}\n\n请尝试提出一个改进问题。"),
    ]
)
question_rewriter = rewrite_prompt | llm.bind(temperature=0) | StrOutputParser()

# 3.8 初始化网络搜索工具
tavily_search = TavilySearch(
    name="tavily_search",
    description="一个用于实时互联网信息搜索的工具。当你需要查询新闻、实时事件、互联网资料、最新信息或普通网页内容时，可以使用该工具。该工具的输入是搜索查询语句。",
    args_schema=TavilySearchArgsSchema,
    max_results=5,
    topic="general",
)


# ==================== 4. LangGraph节点函数定义 ====================


def retrieve(state: GraphState) -> Any:
    """【检索节点】根据用户问题从向量数据库检索相关文档"""
    print("---检索节点---")
    question = state["question"]
    documents = retriever.invoke(question)
    return {"documents": documents, "question": question}


def generate(state: GraphState) -> Any:
    """【生成节点】使用RAG链生成最终答案"""
    print("---LLM生成节点---")
    question = state["question"]
    documents = state["documents"]
    generation = rag_chain.invoke(
        {"context": format_docs(documents), "question": question}
    )
    return {"question": question, "documents": documents, "generation": generation}


def grade_documents(state: GraphState) -> Any:
    """【文档评分节点】CRAG核心组件 - 评估文档相关性"""
    print("---检查文档与问题关联性节点---")
    question = state["question"]
    documents = state["documents"]

    filtered_docs = []
    web_search = "no"
    for doc in documents:
        score: GradeDocument = retrieval_grader.invoke(
            {
                "question": question,
                "document": doc.page_content,
            }
        )
        grade = score.binary_score
        if grade.lower() == "yes":
            print("---文档存在关联---")
            filtered_docs.append(doc)
        else:
            print("---文档不存在关联---")
            web_search = "yes"
            continue

    result = {**state, "documents": filtered_docs, "web_search": web_search}
    print(
        f"评分结果：保留 {len(filtered_docs)}/{len(documents)} 个文档，需要网络搜索: {web_search}"
    )
    return result


def transform_query(state: GraphState) -> Any:
    """【查询重写节点】将用户问题优化为更适合网络搜索的版本"""
    print("---重写查询节点---")
    question = state["question"]
    better_question = question_rewriter.invoke({"question": question})
    return {**state, "question": better_question}


def web_search(state: GraphState) -> Any:
    """【网络搜索节点】当向量库检索结果不佳时，通过网络搜索补充知识"""
    print("---网络检索节点---")
    question = state["question"]
    documents = state["documents"]

    # ✅ 修复：TavilySearch 返回的是字典，需要转换为字符串
    search_result = tavily_search.invoke({"query": question})

    # 处理返回结果：可能是字典或字符串
    if isinstance(search_result, dict):
        search_content = json.dumps(search_result, ensure_ascii=False, indent=2)
    else:
        search_content = str(search_result)

    documents.append(
        Document(
            page_content=search_content,
        )
    )

    return {**state, "documents": documents}


def decide_to_generate(state: GraphState) -> Any:
    """【路由决策节点】根据文档评分结果决定下一步走向"""
    print("---路由选择节点---")
    web_search = state["web_search"]
    if web_search.lower() == "yes":
        print("---执行Web搜索节点---")
        return "transform_query"
    else:
        print("---执行LLM生成节点---")
        return "generate"


# ==================== 5. 构建LangGraph工作流 ====================

workflow = StateGraph(GraphState)

workflow.add_node("retrieve", retrieve)
workflow.add_node("grade_documents", grade_documents)
workflow.add_node("generate", generate)
workflow.add_node("transform_query", transform_query)
workflow.add_node("web_search_node", web_search)

workflow.set_entry_point("retrieve")
workflow.add_edge("retrieve", "grade_documents")
workflow.add_conditional_edges("grade_documents", decide_to_generate)
workflow.add_edge("transform_query", "web_search_node")
workflow.add_edge("web_search_node", "generate")
workflow.set_finish_point("generate")

app = workflow.compile()


# ==================== 6. 执行示例 ====================
if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("启动 CRAG 演示（使用 Chroma）")
    print("=" * 60)

    # 测试问题
    result = app.invoke({"question": "能介绍下什么是LLMOps么?"})

    print("\n" + "=" * 60)
    print("最终答案：")
    print("=" * 60)
    print(result.get("generation", "无答案"))

    # 可选：添加新文档到 Chroma
    print("\n" + "=" * 60)
    print("添加新文档到 Chroma...")
    print("=" * 60)
    new_docs = [
        Document(
            page_content="Chroma 支持元数据过滤，可以根据文档的元数据进行精细化检索。"
        ),
        Document(page_content="向量数据库的性能取决于索引算法和硬件配置。"),
    ]
    vector_store.add_documents(new_docs)
    print(f"✅ 已添加新文档，数据库现在包含 {vector_store._collection.count()} 个文档")
