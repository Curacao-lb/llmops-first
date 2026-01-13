.PHONY: dev test install clean format

# 开发服务器
dev:
	python run.py

# 运行测试
test:
	pytest

# 安装依赖
install:
	pip install -r requirements.txt

# 格式化代码
format:
	black .

# 清理缓存
clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
