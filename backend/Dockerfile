FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV QUANTAMIND_GATEWAY_HOST=0.0.0.0
ENV QUANTAMIND_GATEWAY_PORT=18789

WORKDIR /app

COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY backend ./backend
COPY quantamind ./quantamind
COPY quantamind_v2 ./quantamind_v2

EXPOSE 18789

CMD ["python", "-m", "backend.quantamind_api.app"]
