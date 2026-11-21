import json
import logging

from app.config import REPO_ROOT
from app.main import app

OUTPUT = REPO_ROOT / "docs" / "api" / "openapi.json"

if __name__ == "__main__":
    OUTPUT.write_text(json.dumps(app.openapi(), indent=2) + "\n", encoding="utf-8")
    logging.getLogger(__name__).warning("wrote %s", OUTPUT)
