import argparse
import asyncio
import json
import logging
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.agent.prompt_files import prompt_versions
from app.config import get_settings
from evals import suites
from evals.common import percentile

RESULTS_DIR = Path(__file__).with_name("results")
SUITES = {
    "sql": suites.sql_suite,
    "isolation": suites.isolation_suite,
    "guardrails": suites.guardrail_suite,
    "routing": suites.routing_suite,
    "charts": suites.chart_suite,
    "quiz": suites.quiz_suite,
    "tagging": suites.tagging_suite,
}
PRICE_PER_MILLION_TOKENS = {
    "gemini-2.5-flash": (0.30, 2.50),
    "gemini-2.5-flash-lite": (0.10, 0.40),
    "gemini-3-flash-preview": (0.50, 3.00),
}
logger = logging.getLogger("evals")


def _traces(results: dict[str, Any]) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            if "trace" in node and isinstance(node["trace"], dict):
                found.append(node["trace"])
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    walk(results)
    return found


def performance(results: dict[str, Any]) -> dict[str, Any]:
    traces = [item for item in _traces(results) if not item.get("guardrail")]
    data = [
        item
        for item in traces
        if "describe_view" in item["tools"] or "query_portal_data" in item["tools"]
    ]
    model_id = get_settings().model_id_main
    input_price, output_price = PRICE_PER_MILLION_TOKENS.get(model_id, (0.0, 0.0))
    tokens_in = sum(item["input_tokens"] for item in traces)
    tokens_out = sum(item["output_tokens"] for item in traces)
    cost = (tokens_in * input_price + tokens_out * output_price) / 1_000_000
    return {
        "requests": len(traces),
        "ttft_p50_ms": percentile(
            [item["first_token_ms"] for item in traces if item["first_token_ms"]], 0.5
        ),
        "ttft_p95_ms": percentile(
            [item["first_token_ms"] for item in traces if item["first_token_ms"]], 0.95
        ),
        "total_p50_ms": percentile([item["total_ms"] for item in traces], 0.5),
        "total_p95_ms": percentile([item["total_ms"] for item in traces], 0.95),
        "data_total_p95_ms": percentile([item["total_ms"] for item in data], 0.95),
        "avg_input_tokens": round(tokens_in / len(traces)) if traces else 0,
        "avg_output_tokens": round(tokens_out / len(traces)) if traces else 0,
        "paid_tier_usd_per_question": round(cost / len(traces), 6) if traces else 0,
    }


def summary_markdown(run: dict[str, Any]) -> str:
    lines = [
        f"# Eval run {run['started_at']}",
        f"Provider: {run['provider']} · main model: {run['model_main']} · fast model: {run['model_fast']}",
        "",
        "| Suite | Metric | Value |",
        "|---|---|---|",
    ]
    for suite, payload in run["suites"].items():
        for metric, value in payload["metrics"].items():
            lines.append(f"| {suite} | {metric} | {value} |")
    for metric, value in run["performance"].items():
        lines.append(f"| performance | {metric} | {value} |")
    return "\n".join(lines) + "\n"


async def main(selected: list[str], limit: int | None) -> Path:
    settings = get_settings()
    run: dict[str, Any] = {
        "started_at": datetime.now(UTC).strftime("%Y-%m-%dT%H-%M-%SZ"),
        "provider": settings.model_provider,
        "model_main": settings.model_id_main,
        "model_fast": settings.model_id_fast,
        "judge_model": settings.model_id_fast,
        "prompt_versions": prompt_versions(),
        "limit": limit,
        "suites": {},
        "performance": {},
    }
    RESULTS_DIR.mkdir(exist_ok=True)
    path = RESULTS_DIR / f"{run['started_at']}.json"
    for name in selected:
        logger.info("running suite %s", name)
        try:
            run["suites"][name] = await SUITES[name](limit)
        except Exception:
            logger.exception("suite %s crashed; earlier suites are kept", name)
            continue
        logger.info("%s: %s", name, run["suites"][name]["metrics"])
        run["performance"] = performance(run["suites"])
        path.write_text(
            json.dumps(run, indent=2, ensure_ascii=False, default=str), encoding="utf-8"
        )
        path.with_suffix(".md").write_text(summary_markdown(run), encoding="utf-8")
    sys.stdout.write(summary_markdown(run))
    return path


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    parser = argparse.ArgumentParser(
        description="Run CampusGPT evaluation suites against the real backend."
    )
    parser.add_argument(
        "--suite", choices=sorted(SUITES), action="append", help="Run only this suite (repeatable)"
    )
    parser.add_argument(
        "--limit", type=int, default=None, help="Use only the first N cases per suite"
    )
    arguments = parser.parse_args()
    asyncio.run(main(arguments.suite or list(SUITES), arguments.limit))
