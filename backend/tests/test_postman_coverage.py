import json

from app.main import app
from scripts.build_postman import COLLECTION_PATH, ENVIRONMENT_PATH


def collection_routes() -> set[str]:
    collection = json.loads(COLLECTION_PATH.read_text(encoding="utf-8"))
    return {item["name"] for folder in collection["item"] for item in folder["item"]}


def openapi_routes() -> set[str]:
    return {
        f"{method.upper()} {path}"
        for path, methods in app.openapi()["paths"].items()
        for method in methods
    }


def test_every_route_is_in_the_postman_collection() -> None:
    missing = openapi_routes() - collection_routes()
    assert not missing, f"Missing from Postman collection: {sorted(missing)}"


def test_no_secrets_saved_in_collection_or_environment() -> None:
    environment = json.loads(ENVIRONMENT_PATH.read_text(encoding="utf-8"))
    for value in environment["values"]:
        if "Password" in value["key"]:
            assert value["value"] == ""
    assert "demo123" not in COLLECTION_PATH.read_text(encoding="utf-8")
