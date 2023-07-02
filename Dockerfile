FROM python:3.10-slim

RUN pip install --upgrade pip \
 && pip install --no-cache-dir polars
