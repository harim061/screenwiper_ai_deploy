# Python 베이스 이미지
FROM python:3.10

# 작업 디렉토리 설정
WORKDIR /app

# 필요한 패키지 설치
COPY ./requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

# 애플리케이션 코드 복사
COPY ./screenwiper /app/screenwiper

# 애플리케이션 실행
CMD ["uvicorn", "screenwiper.main:app", "--host", "0.0.0.0", "--port", "8000"]

