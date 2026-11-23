FROM python:3.12-slim

WORKDIR /app

# Cliente Kerberos (GSSAPI) para autenticar no Kafka
RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
       gcc libkrb5-dev krb5-user \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY producer.py .

CMD ["python", "producer.py"]

