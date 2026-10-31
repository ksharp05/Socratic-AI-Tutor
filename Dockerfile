# Socratic Tutor images (R6). One file, two targets:
#   docker build --target api -t socratic-tutor-api .
#   docker build --target ui  -t socratic-tutor-ui  .
# docker-compose.yml builds both. No .env, keys, NCERT PDFs, dataset builds or evaluation data enter
# an image (see .dockerignore); keys reach the API only at run time through env_file.

FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1
RUN useradd --create-home --uid 10001 tutor
WORKDIR /app

# ---------------------------------------------------------------- api: FastAPI + the tutor
FROM base AS api
COPY pyproject.toml README.md ./
COPY src ./src
COPY config ./config
COPY content ./content
# Editable install keeps config.ROOT at /app, where config/ and content/ live.
RUN pip install -e ".[api]" \
 && mkdir -p /app/var && chown tutor:tutor /app/var
ENV TUTOR_VAR_DIR=/app/var \
    TUTOR_LLM=stub
USER tutor
VOLUME ["/app/var"]
EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=5s --start-period=40s --retries=5 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=4).status == 200 else 1)"
CMD ["uvicorn", "tutor_api.main:app", "--host", "0.0.0.0", "--port", "8000"]

# ---------------------------------------------------------------- ui: Streamlit, talks only to the API
FROM base AS ui
RUN pip install "streamlit==1.66.1" "requests==2.34.2"
COPY ui ./ui
USER tutor
ENV TUTOR_API_URL=http://api:8000
EXPOSE 8501
HEALTHCHECK --interval=15s --timeout=5s --start-period=30s --retries=5 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8501/_stcore/health', timeout=4).status == 200 else 1)"
CMD ["streamlit", "run", "ui/app.py", "--server.address=0.0.0.0", "--server.port=8501", "--server.headless=true", "--browser.gatherUsageStats=false"]
