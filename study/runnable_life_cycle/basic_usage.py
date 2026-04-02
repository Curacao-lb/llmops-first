import time

from langchain_core.runnables import RunnableLambda, RunnableConfig
from langchain_core.tracers.schemas import Run


def on_start(run_obj: Run, config: RunnableConfig) -> None:
    print("on-start")
    print("run_obj", run_obj)
    print("config", config)
    print("---------")


def on_end(run_obj: Run, config: RunnableConfig) -> None:
    print("on_end")
    print("run_obj", run_obj)
    print("config", config)
    print("---------")


def on_error(run_obj: Run, config: RunnableConfig) -> None:
    print("on_error")
    print("run_obj", run_obj)
    print("config", config)
    print("---------")


# 1.创建RunnableLambda与链
runnable = RunnableLambda(lambda x: time.sleep(x)).with_alisteners(
    on_start=on_start, on_end=on_end, on_error=on_error
)
chain = runnable

# 2.调用并执行链
chain.invoke(2, config={"configurable": {"name": "robin"}})

# 程序会在休眠2秒之后退出
