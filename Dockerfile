FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1 \
    EXAMGEN_ENV=production EXAMGEN_DB=/data/examgen.db HOST=0.0.0.0 PORT=8000
WORKDIR /srv
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY app ./app
COPY bootstrap ./bootstrap
RUN useradd --system --uid 10001 examgen && mkdir -p /data && chown examgen /data
USER examgen
VOLUME /data
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s \
  CMD python -c "import os,urllib.request;urllib.request.urlopen('http://127.0.0.1:%s/healthz' % os.environ['PORT'])" || exit 1
CMD ["python", "-m", "app"]
