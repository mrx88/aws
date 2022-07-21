FROM python:3.10-slim-bullseye

WORKDIR /app/
COPY requirements.txt /app/

RUN apt update \
  && apt install build-essential -y --force-yes \
  && apt install libpq-dev python3-dev -y --force-yes \
  && pip install --upgrade pip \
  && pip install -r /app/requirements.txt

RUN adduser appuser
USER appuser

COPY migrate.py .

ENTRYPOINT ["/app/migrate.py"]