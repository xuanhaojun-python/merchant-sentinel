PY ?= .venv/bin/python

.PHONY: dev backend frontend build run test-platform test-unit install-frontend

install-frontend:
	cd sentinel/frontend && npm install

# 开发：后端 :8082（热重载）+ 前端 :5173（代理到 8082）
dev:
	$(MAKE) -j2 backend frontend

backend:
	$(PY) -m uvicorn sentinel.backend.main:app --host 127.0.0.1 --port 8082 --reload --reload-dir sentinel/backend

frontend:
	cd sentinel/frontend && npm run dev

build:
	cd sentinel/frontend && npm run build

# 日常使用：构建前端后由后端统一提供 http://localhost:8082
run: build
	$(PY) -m sentinel

test-platform:
	$(PY) -m pytest sentinel/tests -p no:cacheprovider -q -o addopts=""

# 执行层工具单元测试（不连接 SIT）
test-unit:
	$(PY) -m pytest unit_tests -p no:cacheprovider -q -o addopts=""
