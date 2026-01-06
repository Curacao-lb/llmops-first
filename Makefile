.PHONY: dev test install clean

# 开发服务器
dev:
	python run.py

# 运行测试
test:
	pytest

# 安装依赖
install:
	pip install -r requirements.txt

# 清理缓存
clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
