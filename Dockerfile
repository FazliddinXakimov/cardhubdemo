FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HOST=0.0.0.0 \
    PORT=8000 \
    CARDLAB_DATA_DIR=/app/data

WORKDIR /app
RUN useradd --create-home --uid 10001 cardlab && mkdir /app/data && chown cardlab:cardlab /app/data
COPY --chown=cardlab:cardlab participant /app/participant
USER cardlab
EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=2)"
CMD ["python", "/app/participant/project/web.py"]
