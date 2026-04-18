FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# pikepdf may need qpdf system libs depending on wheel availability.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libqpdf-dev \
        qpdf \
    && rm -rf /var/lib/apt/lists/*

COPY editor/requirements.txt /tmp/requirements.txt
RUN pip install --upgrade pip \
    && pip install -r /tmp/requirements.txt gunicorn

COPY . /app

RUN useradd --create-home --uid 10001 appuser \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--threads", "4", "--timeout", "120", "editor.app:app"]
