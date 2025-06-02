FROM python:3.11-slim
WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

ARG Q_SCHEMA
ARG Q_UI_SCHEMA
ARG Q_ID
ARG Q_TITLE

RUN mkdir -p /app/data \
 && echo "$Q_SCHEMA"  > /app/schema.json \
 && echo "$Q_UI_SCHEMA" > /app/ui_schema.json

ENV Q_ID=${Q_ID}
ENV Q_TITLE=${Q_TITLE}

COPY app.py ./
COPY templates ./templates
COPY static ./static

EXPOSE 5000
CMD ["python", "app.py"]
