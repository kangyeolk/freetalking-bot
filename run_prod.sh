#!/bin/bash

# 프로덕션 모드 실행 스크립트

echo "🚀 일본어 회화 앱 프로덕션 모드 시작..."

# 환경변수 로드
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
    echo "✅ 환경변수 로드 완료"
else
    echo "⚠️  .env 파일이 없습니다."
    exit 1
fi

# 포트 설정 (.env의 APP_PORT 사용, 없으면 8501)
PORT=${APP_PORT:-8501}

# 프로덕션 설정
export STREAMLIT_SERVER_PORT=$PORT
export STREAMLIT_SERVER_HEADLESS=true
export STREAMLIT_SERVER_RUN_ON_SAVE=false
export STREAMLIT_LOGGER_LEVEL=info

echo "📡 포트: $PORT"
echo "🏭 프로덕션 모드: ON"
echo "-----------------------------------"
echo "앱 주소: http://localhost:$PORT"
echo "-----------------------------------"

# Streamlit 실행
streamlit run main.py \
    --server.port=$PORT \
    --server.address=0.0.0.0 \
    --server.headless=true \
    --logger.level=info