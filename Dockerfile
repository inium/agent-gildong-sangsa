FROM ghcr.io/astral-sh/uv:latest AS uv

FROM python:3.14.7 AS local

COPY --from=uv /uv /uvx /bin/

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /workspace

# 실제 소스 코드는 compose의 volume으로 마운트합니다.
VOLUME ["/workspace"]

EXPOSE 8000

CMD ["python", "--version"]
