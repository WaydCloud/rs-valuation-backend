# 1. 베이스 이미지 설정
FROM python:3.10-slim

# 2. 시스템 패키지 업데이트 및 Java 설치
RUN apt-get update && apt-get install -y default-jdk

# 3. 작업 디렉토리 설정
WORKDIR /app

# 4. requirements.txt 파일 복사 및 Python 패키지 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. 애플리케이션 코드 복사
COPY . .

# 6. 컨테이너가 시작될 때 실행할 명령어 (포트는 환경 변수 $PORT 사용)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "$PORT"]
