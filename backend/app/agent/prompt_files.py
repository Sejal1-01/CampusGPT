import hashlib
from functools import cache
from pathlib import Path

PROMPTS_DIR = Path(__file__).with_name("prompts")


@cache
def load_prompt(name: str) -> str:
    return (PROMPTS_DIR / name).read_text(encoding="utf-8")


def render_prompt(name: str, **values: object) -> str:
    return load_prompt(name).format(**values)


def prompt_versions() -> dict[str, str]:
    return {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()[:12]
        for path in sorted(PROMPTS_DIR.iterdir())
        if path.suffix in {".md", ".txt"}
    }
