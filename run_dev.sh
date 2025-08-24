#!/bin/bash

# 개발 모드 실행 스크립트

echo "🚀 일본어 회화 앱 개발 모드 시작..."

# 환경변수 로드
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
    echo "✅ 환경변수 로드 완료"
else
    echo "⚠️  .env 파일이 없습니다. .env.example을 복사해주세요."
    exit 1
fi

# API 키 확인
if [ -z "$OPENAI_API_KEY" ]; then
    echo "❌ OPENAI_API_KEY가 설정되지 않았습니다."
    exit 1
fi

# 가상환경 활성화 확인 (.venv 또는 venv)
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  가상환경이 활성화되지 않았습니다."
    echo "다음 명령어를 실행하세요:"
    echo "  source .venv/bin/activate (uv 사용시)"
    echo "  또는"
    echo "  source venv/bin/activate (일반 venv)"
    exit 1
fi

# 포트 설정 (.env의 APP_PORT 사용, 없으면 8501)
PORT=${APP_PORT:-8501}

# 디버그 모드 활성화
export STREAMLIT_SERVER_PORT=$PORT
export STREAMLIT_SERVER_HEADLESS=false
export STREAMLIT_SERVER_RUN_ON_SAVE=true
export STREAMLIT_SERVER_FILE_WATCHER_TYPE=auto
export STREAMLIT_LOGGER_LEVEL=debug
export STREAMLIT_CLIENT_TOOLBAR_MODE=developer

echo "📡 포트: $PORT"
echo "🔧 디버그 모드: ON"
echo "🔄 자동 리로드: ON"
echo "-----------------------------------"
echo "앱 주소: http://localhost:$PORT"
echo "-----------------------------------"
echo "종료하려면 Ctrl+C를 누르세요"
echo ""

# Streamlit 실행
streamlit run main.py \
    --server.port=$PORT \
    --server.address=localhost \
    --server.runOnSave=true \
    --server.fileWatcherType=auto \
    --logger.level=debug \
    --client.toolbarMode=developer \
    --theme.base=light