.PHONY: dev test install install-dev clean format lint lint-fix typecheck check \
        deps-compile deps-upgrade deps-sync

# 开发服务器
dev:
	python run.py

# 运行测试
test:
	pytest

# 安装运行时依赖
install:
	pip install -r requirements.txt

# 安装完整开发环境(运行时依赖 + pytest/ruff/pyright/pip-tools)
install-dev: install
	pip install -r requirements-dev.txt

# 依赖管理(pip-tools): 改完 requirements.in 后重新生成锁文件
# 注意: unstructured 的依赖树较大，首次编译可能需要数分钟
deps-compile:
	pip-compile --no-strip-extras --no-emit-index-url requirements.in -o requirements.txt
	pip-compile --no-strip-extras --no-emit-index-url requirements-dev.in -o requirements-dev.txt

# 在约束范围内升级所有依赖到最新版本
deps-upgrade:
	pip-compile --no-strip-extras --no-emit-index-url --upgrade requirements.in -o requirements.txt
	pip-compile --no-strip-extras --no-emit-index-url --upgrade requirements-dev.in -o requirements-dev.txt

# 让当前环境与锁文件完全一致(会卸载锁文件中没有的包)
deps-sync:
	pip-sync requirements.txt requirements-dev.txt

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
