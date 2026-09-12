"""Export the FastAPI OpenAPI schema without starting application lifespan handlers."""

import json
from pathlib import Path

from observelens_auth.main import app

output_path = Path(__file__).resolve().parents[1] / "docs" / "openapi.json"
output_path.write_text(
    json.dumps(app.openapi(), ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)
print(f"Exported OpenAPI schema to {output_path}")
