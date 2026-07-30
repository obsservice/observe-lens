FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir .

EXPOSE 3084
CMD ["python", "-m", "observability_mcp_gateway.main"]
