FROM python:3.10-slim

ENV COVERAGE_FILE=/tmp/coverage

RUN pip install --upgrade pip \
 && pip install --no-cache-dir polars pytest pytest-cov
