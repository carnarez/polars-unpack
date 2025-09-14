FROM python:slim

RUN pip install --root-user-action=ignore --upgrade pip uv \
 && uv pip install --no-cache-dir --system polars
