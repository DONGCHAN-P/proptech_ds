# 맞춤 찾기 웹 — deploy/bundle.py 가 만든 deploy/build/ 를 빌드 컨텍스트로 쓴다.
FROM python:3.11-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 APP_ENV=production

COPY web/requirements.txt web/requirements.txt
RUN pip install --no-cache-dir -r web/requirements.txt

COPY . .

EXPOSE 8080
# Fly 프록시 뒤에서 https 를 제대로 알아보도록 forwarded 헤더를 믿는다
CMD ["uvicorn", "web.main:app", "--host", "0.0.0.0", "--port", "8080", "--proxy-headers", "--forwarded-allow-ips", "*"]
