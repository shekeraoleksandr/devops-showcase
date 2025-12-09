FROM --platform=$BUILDPLATFORM python:3.11.0-alpine AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apk update \
    && apk add --no-cache \
        g++ \
        linux-headers \
        gcc \
        musl-dev \
    && rm -rf /var/cache/apk/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

FROM python:3.11.0-alpine AS runtime

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV ENABLE_PROFILER=1

RUN apk update \
    && apk add --no-cache \
        libstdc++ \
    && rm -rf /var/cache/apk/*

COPY --from=builder /opt/venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /email_server

COPY . .

EXPOSE 8080

ENTRYPOINT ["python", "email_server.py"]