FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir .

COPY alembic.ini ./
COPY alembic ./alembic

EXPOSE 9081
CMD ["uvicorn", "observelens_auth.main:app", "--host", "0.0.0.0", "--port", "9081"]
