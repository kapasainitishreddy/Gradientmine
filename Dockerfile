FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 GM_DATA_DIR=/data GM_MODE=local PORT=8000
WORKDIR /app
RUN useradd --uid 10001 --create-home gradientmine && mkdir -p /data && chown gradientmine:gradientmine /data
COPY pyproject.toml README.md LICENSE ./
COPY gradientmine ./gradientmine
COPY web ./web
RUN python -m pip install --upgrade pip==26.2.1 && python -m pip install torch==2.14.1 --index-url https://download.pytorch.org/whl/cpu && python -m pip install '.[chain]'
USER 10001:10001
VOLUME ["/data"]
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 CMD python -c "import os,urllib.request; urllib.request.urlopen('http://127.0.0.1:'+os.environ.get('PORT','8000')+'/health',timeout=4)"
CMD ["python", "-m", "gradientmine.hosted"]
