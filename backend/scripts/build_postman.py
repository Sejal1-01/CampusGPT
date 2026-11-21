import json
import logging
import re
from typing import Any

from app.config import REPO_ROOT
from app.main import app

API_DIR = REPO_ROOT / "docs" / "api"
COLLECTION_PATH = API_DIR / "CampusGPT.postman_collection.json"
ENVIRONMENT_PATH = API_DIR / "local.postman_environment.json"
FOLDERS = {
    "Auth": "Auth",
    "Chat": "Chat",
    "Quiz": "Quiz",
    "Files": "Files",
    "Results": "Results",
    "Access": "Access",
    "Health": "Health",
}
EXAMPLE_BODIES: dict[str, Any] = {
    "POST /api/auth/login": {"username": "{{studentUser}}", "password": "{{demoPassword}}"},
    "POST /api/chat": {"message": "What's my attendance in DBMS and how many more can I skip?"},
    "POST /api/quiz/{quiz_id}/submit": {"answers": [0, 2, None, 1, 3]},
    "POST /api/access/groups": {"name": "Timetable Committee", "description": "Builds timetables"},
    "POST /api/access/groups/{name}/members": {"username": "faculty1"},
    "POST /api/access/grants": {
        "kind": "user",
        "target": "faculty1",
        "domain": "hostel",
        "scope": "college",
    },
    "POST /api/access/grants/revoke": {
        "kind": "user",
        "target": "faculty1",
        "domain": "hostel",
        "scope": "college",
    },
    "POST /api/access/users/{username}/roles": {"role": "advisor"},
    "POST /api/access/users": {
        "username": "warden1",
        "display_name": "Hostel Warden",
        "password": "{{newUserPassword}}",
    },
    "POST /api/access/users/{username}/password": {"password": "{{newUserPassword}}"},
}
PATH_VALUES = {
    "quiz_id": "{{quizId}}",
    "result_id": "{{resultId}}",
    "set_id": "{{flashcardSetId}}",
    "name": "Timetable Committee",
    "username": "faculty1",
    "role": "advisor",
}
ERROR_EXAMPLES = {
    "400": ("Bad request", "invalid_request", "Invalid message: Field required"),
    "401": ("Not logged in", "unauthenticated", "Your session has expired. Please log in again."),
    "403": ("Forbidden", "forbidden", "Only the platform admin can manage access."),
    "404": ("Not found", "not_found", "That result has expired. Ask the question again."),
    "409": ("Busy", "busy", "Still answering your previous question."),
    "503": (
        "Database down",
        "unavailable",
        "The portal database is down. Please try again shortly.",
    ),
}


def _error_codes(method: str, path: str) -> list[str]:
    codes = (
        ["401"] if path not in ("/api/auth/login", "/api/health", "/api/auth/demo-accounts") else []
    )
    if method in ("POST", "PUT") or path == "/api/auth/login":
        codes.insert(0, "400")
    if path.startswith("/api/access"):
        codes.append("403")
    if "{" in path and not path.startswith("/api/access"):
        codes.append("404")
    if path == "/api/chat":
        codes += ["409", "503"]
    return codes


def _url(path: str) -> dict[str, Any]:
    filled = re.sub(r"\{(\w+)\}", lambda match: PATH_VALUES.get(match.group(1), "x"), path)
    raw = "{{baseUrl}}" + filled
    return {
        "raw": raw,
        "host": ["{{baseUrl}}"],
        "path": [part for part in filled.split("/") if part],
    }


def _request(method: str, path: str, operation: dict[str, Any]) -> dict[str, Any]:
    request: dict[str, Any] = {
        "method": method,
        "url": _url(path),
        "description": operation.get("description") or operation.get("summary", ""),
        "header": [],
    }
    body = EXAMPLE_BODIES.get(f"{method} {path}")
    if body is not None:
        request["header"].append({"key": "Content-Type", "value": "application/json"})
        request["body"] = {"mode": "raw", "raw": json.dumps(body, indent=2)}
    if path == "/api/files/pdf":
        request["body"] = {
            "mode": "formdata",
            "formdata": [{"key": "file", "type": "file", "src": "notes.pdf"}],
        }
    return request


def _tests(method: str, path: str) -> list[str]:
    lines = [
        "pm.test('status is 2xx', () => pm.expect(pm.response.code).to.be.within(200, 299));",
    ]
    if path == "/api/chat":
        lines.append(
            "pm.test('is an SSE stream', () => pm.expect(pm.response.headers.get('Content-Type')).to.include('text/event-stream'));"
        )
    elif not path.endswith("/csv"):
        lines.append("pm.test('returns JSON', () => pm.response.to.be.json);")
    if path == "/api/auth/login":
        lines.append(
            "pm.test('has username and roles', () => { const body = pm.response.json(); pm.expect(body).to.have.property('username'); pm.expect(body.roles).to.be.an('array'); });"
        )
    return lines


def _examples(method: str, path: str, request: dict[str, Any]) -> list[dict[str, Any]]:
    success = {
        "name": "Success",
        "originalRequest": request,
        "code": 200,
        "status": "OK",
        "header": [
            {
                "key": "Content-Type",
                "value": "text/event-stream" if path == "/api/chat" else "application/json",
            }
        ],
        "body": 'data: {"type":"status","text":"Checking your question"}\n\ndata: {"type":"done","latency_ms":2310}\n\n'
        if path == "/api/chat"
        else json.dumps({"ok": True}),
    }
    examples = [success]
    for code in _error_codes(method, path):
        name, error_code, message = ERROR_EXAMPLES[code]
        examples.append(
            {
                "name": name,
                "originalRequest": request,
                "code": int(code),
                "status": name,
                "header": [{"key": "Content-Type", "value": "application/json"}],
                "body": json.dumps({"error": {"code": error_code, "message": message}}),
            }
        )
    return examples


def _item(method: str, path: str, operation: dict[str, Any]) -> dict[str, Any]:
    request = _request(method, path, operation)
    return {
        "name": f"{method} {path}",
        "request": request,
        "event": [
            {"listen": "test", "script": {"type": "text/javascript", "exec": _tests(method, path)}}
        ],
        "response": _examples(method, path, request),
    }


def build_collection() -> dict[str, Any]:
    folders: dict[str, list[dict[str, Any]]] = {name: [] for name in FOLDERS}
    for path, methods in app.openapi()["paths"].items():
        for method, operation in methods.items():
            folder = FOLDERS.get((operation.get("tags") or ["Health"])[0], "Health")
            folders[folder].append(_item(method.upper(), path, operation))
    return {
        "info": {
            "name": "CampusGPT API",
            "description": "Every CampusGPT endpoint. Run 'Login' first; the session cookie is reused automatically.",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
        },
        "item": [{"name": name, "item": items} for name, items in folders.items() if items],
    }


def build_environment() -> dict[str, Any]:
    names = [
        "studentUser:student1",
        "facultyUser:faculty1",
        "hodUser:hod_cse",
        "deanUser:dean",
        "adminUser:admin",
        "platformAdminUser:platform_admin",
        "baseUrl:http://localhost:8000",
        "demoPassword:",
        "platformAdminPassword:",
        "newUserPassword:",
        "quizId:",
        "resultId:",
        "flashcardSetId:",
    ]
    values = [
        {
            "key": key,
            "value": value,
            "enabled": True,
            "type": "secret" if "Password" in key else "default",
        }
        for key, value in (item.split(":", 1) for item in names)
    ]
    return {"name": "CampusGPT local", "values": values, "_postman_variable_scope": "environment"}


if __name__ == "__main__":
    COLLECTION_PATH.write_text(
        json.dumps(build_collection(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    ENVIRONMENT_PATH.write_text(json.dumps(build_environment(), indent=2) + "\n", encoding="utf-8")
    logging.getLogger(__name__).warning(
        "wrote %s and %s", COLLECTION_PATH.name, ENVIRONMENT_PATH.name
    )
