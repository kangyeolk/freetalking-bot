# Makefile for 일본어 회화 앱

.PHONY: help install dev prod clean test

help:
	@echo "일본어 회화 학습 앱 - 명령어"
	@echo "========================="
	@echo "make install  - 패키지 설치"
	@echo "make dev      - 개발 모드 실행 (자동 리로드)"
	@echo "make prod     - 프로덕션 모드 실행"
	@echo "make clean    - 캐시 정리"
	@echo "make test     - 테스트 실행"

install:
	@if command -v uv >/dev/null 2>&1; then \
		echo "📦 uv로 패키지 설치 중..."; \
		uv pip install -r requirements.txt; \
	else \
		echo "📦 pip으로 패키지 설치 중..."; \
		pip install -r requirements.txt; \
	fi
	@echo "✅ 패키지 설치 완료"

install-uv:
	uv pip install -r requirements.txt
	@echo "✅ uv로 패키지 설치 완료"

sync:
	uv pip sync requirements.txt
	@echo "✅ 패키지 동기화 완료"

dev:
	@./run_dev.sh

prod:
	@./run_prod.sh

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .streamlit/cache
	rm -rf logs/*.log
	@echo "✅ 캐시 정리 완료"

test:
	pytest tests/ -v

# 개발 환경 설정 (uv 사용)
setup:
	@if command -v uv >/dev/null 2>&1; then \
		echo "🚀 uv로 가상환경 생성 중..."; \
		uv venv --python 3.11; \
		echo "✅ 가상환경 생성 완료 (.venv)"; \
		echo "다음 명령어를 실행하세요:"; \
		echo "  source .venv/bin/activate"; \
	else \
		echo "🐍 일반 Python venv 생성 중..."; \
		python3 -m venv venv; \
		echo "✅ 가상환경 생성 완료 (venv)"; \
		echo "다음 명령어를 실행하세요:"; \
		echo "  source venv/bin/activate"; \
	fi
	@echo "그 다음 'make install' 실행"

# uv 설치
install-tools:
	curl -LsSf https://astral.sh/uv/install.sh | sh
	@echo "✅ uv 설치 완료"
	@echo "터미널을 재시작하거나 다음 명령어 실행:"
	@echo "  source ~/.bashrc 또는 source ~/.zshrc"