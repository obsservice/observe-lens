FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir .

EXPOSE 3081
CMD ["uvicorn", "observelens_service.main:app", "--host", "0.0.0.0", "--port", "3081"]
