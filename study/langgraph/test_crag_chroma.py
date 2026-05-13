#!/usr/bin/env python
"""
测试 crag_demo_chroma.py 的修复
"""
import sys
import json

print("=" * 60)
print("测试 Chroma CRAG 演示")
print("=" * 60)

# 测试 1: 检查导入
print("\n[测试 1] 检查导入...")
try:
    from langchain_chroma import Chroma

    print("✅ 使用 langchain-chroma")
except ImportError:
    print("⚠️ 使用 langchain-community.vectorstores.Chroma")
    from langchain_community.vectorstores import Chroma

# 测试 2: 检查 TavilySearch 返回格式
print("\n[测试 2] 检查 TavilySearch 返回格式...")
try:
    from langchain_tavily import TavilySearch
    from pydantic import BaseModel, Field

    class TavilySearchArgsSchema(BaseModel):
        query: str = Field(description="执行Tavily搜索的查询语句")

    tavily_search = TavilySearch(
        name="tavily_search",
        description="一个用于实时互联网信息搜索的工具。",
        args_schema=TavilySearchArgsSchema,
        max_results=2,
        topic="general",
    )

    # 测试搜索
    result = tavily_search.invoke({"query": "Python"})
    print(f"✅ TavilySearch 返回类型: {type(result).__name__}")

    # 测试转换
    if isinstance(result, dict):
        content = json.dumps(result, ensure_ascii=False, indent=2)
        print(f"✅ 字典转换成功，长度: {len(content)} 字符")
    else:
        content = str(result)
        print(f"✅ 字符串转换成功，长度: {len(content)} 字符")

except Exception as e:
    print(f"❌ 错误: {e}")
    sys.exit(1)

# 测试 3: 检查 Document 创建
print("\n[测试 3] 检查 Document 创建...")
try:
    from langchain_core.documents import Document

    doc = Document(page_content="测试内容")
    print(f"✅ Document 创建成功: {doc.page_content}")
except Exception as e:
    print(f"❌ 错误: {e}")
    sys.exit(1)

# 测试 4: 运行完整的 CRAG 演示
print("\n[测试 4] 运行完整的 CRAG 演示...")
print("-" * 60)

try:
    from crag_demo_chroma import app

    result = app.invoke({"question": "什么是向量数据库?"})

    print("-" * 60)
    print("\n✅ CRAG 演示执行成功！")
    print(f"\n最终答案:\n{result.get('generation', '无答案')}")

except Exception as e:
    print(f"❌ 错误: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("✅ 所有测试通过！")
print("=" * 60)
