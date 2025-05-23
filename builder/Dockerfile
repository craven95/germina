FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    libffi-dev \
    libssl-dev \
  && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY builder.py /app/
COPY survey_template /app/survey_template

EXPOSE 5000

CMD ["uvicorn", "builder:app", "--host", "0.0.0.0", "--port", "5000"]
