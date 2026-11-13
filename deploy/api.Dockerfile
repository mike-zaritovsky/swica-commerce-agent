# The SWICA agent API: FastAPI on uvicorn, one worker (sessions and memory live in the
# process). Build from the repository root: docker build -f deploy/api.Dockerfile .
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# The three packages install editable from their directories, so they are copied first.
COPY requirements.txt ./
COPY commerce-common ./commerce-common
COPY shopping-agent ./shopping-agent
RUN pip install -r requirements.txt

COPY examples/demo_common ./examples/demo_common
COPY examples/shopify_demo/__init__.py ./examples/shopify_demo/__init__.py
COPY examples/shopify_demo/api ./examples/shopify_demo/api
COPY examples/shopify_demo/data ./examples/shopify_demo/data

# The memory seeder writes a marker file into data/.
RUN useradd --create-home --uid 10001 app && chown -R app /app/examples/shopify_demo/data
USER app

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health', timeout=4)"

CMD ["uvicorn", "shopify_demo.api.main:app", "--app-dir", "examples", \
     "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--proxy-headers"]
