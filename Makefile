.PHONY: dev test install clean format lint lint-fix typecheck check

# 开发服务器
dev:
	python run.py

# 运行测试
test:
	pytest

# 安装依赖
install:
	pip install -r requirements.txt

# 格式化代码(Ruff,等价于 black)
format:
	ruff format .

# 代码检查(Ruff,替代 pylint/flake8)
lint:
	ruff check .

# 自动修复可修复的 lint 问题
lint-fix:
	ruff check --fix .

# 类型检查(Pyright)
typecheck:
	pyright

# 一键:格式化 + 检查 + 类型检查
check: format lint typecheck

# 清理缓存
clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
