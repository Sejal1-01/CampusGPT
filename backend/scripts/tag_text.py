import argparse
import asyncio
import logging
from typing import Any

import mysql.connector

from app.agent.structured import ModelUnavailableError
from app.config import TAGGING_BATCH_SIZE, TAGGING_CONCURRENCY, get_settings
from app.services.tagging import Kind, TagResult, tag_batch

logger = logging.getLogger("tag_text")
SOURCES: dict[Kind, dict[str, str]] = {
    "feedback": {
        "table": "feedback",
        "text": "comment",
        "tags": "feedback_tags",
        "themes": "feedback_themes",
        "key": "feedback_id",
    },
    "complaint": {
        "table": "complaints",
        "text": "text",
        "tags": "complaint_tags",
        "themes": "complaint_themes",
        "key": "complaint_id",
    },
}


def _connect() -> Any:
    settings = get_settings()
    return mysql.connector.connect(
        host=settings.mysql_host,
        port=settings.mysql_port,
        user="root",
        password=settings.root_password,
        database=settings.mysql_db,
        autocommit=True,
    )


def _untagged(conn: Any, kind: Kind, retag: bool, limit: int | None) -> list[tuple[int, str]]:
    source = SOURCES[kind]
    sql = f"SELECT t.id, t.{source['text']} FROM {source['table']} t"
    if not retag:
        sql += f" LEFT JOIN {source['tags']} g ON g.{source['key']} = t.id WHERE g.{source['key']} IS NULL"
    sql += " ORDER BY t.id" + (f" LIMIT {int(limit)}" if limit else "")
    cursor = conn.cursor()
    cursor.execute(sql)
    rows = [(int(row[0]), str(row[1])) for row in cursor.fetchall()]
    cursor.close()
    return rows


def _save(conn: Any, kind: Kind, item_id: int, tags: TagResult) -> None:
    source = SOURCES[kind]
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM {source['themes']} WHERE {source['key']} = %s", (item_id,))
    cursor.execute(
        f"REPLACE INTO {source['tags']} ({source['key']}, sentiment, summary) VALUES (%s, %s, %s)",
        (item_id, tags.sentiment, tags.summary),
    )
    cursor.executemany(
        f"INSERT INTO {source['themes']} ({source['key']}, theme) VALUES (%s, %s)",
        [(item_id, theme) for theme in tags.themes],
    )
    cursor.close()


async def _tag_all(conn: Any, kind: Kind, rows: list[tuple[int, str]]) -> tuple[int, int]:
    semaphore = asyncio.Semaphore(TAGGING_CONCURRENCY)
    batches = [
        rows[index : index + TAGGING_BATCH_SIZE]
        for index in range(0, len(rows), TAGGING_BATCH_SIZE)
    ]
    counts = {"done": 0, "failed": 0}

    async def one(batch: list[tuple[int, str]]) -> None:
        async with semaphore:
            try:
                results = await tag_batch(kind, [text for _item_id, text in batch])
            except ModelUnavailableError as error:
                logger.warning("%s batch of %s not tagged: %s", kind, len(batch), str(error)[:120])
                counts["failed"] += len(batch)
                return
        for (item_id, _text), tags in zip(batch, results, strict=True):
            if tags is None:
                counts["failed"] += 1
                continue
            _save(conn, kind, item_id, tags)
            counts["done"] += 1
        logger.info(
            "%s: %s tagged, %s failed of %s", kind, counts["done"], counts["failed"], len(rows)
        )

    await asyncio.gather(*(one(batch) for batch in batches))
    return counts["done"], counts["failed"]


async def main(kinds: list[Kind], retag: bool, limit: int | None) -> None:
    conn = _connect()
    for kind in kinds:
        rows = _untagged(conn, kind, retag, limit)
        logger.info("%s: %s rows to tag", kind, len(rows))
        done, failed = await _tag_all(conn, kind, rows)
        logger.info(
            "%s: finished, %s tagged, %s failed (re-run to retry failures)", kind, done, failed
        )
    conn.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    parser = argparse.ArgumentParser(description="Tag feedback and complaints with the fast model.")
    parser.add_argument("--only", choices=["feedback", "complaint"])
    parser.add_argument("--retag", action="store_true", help="Re-tag rows that already have tags")
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()
    selected: list[Kind] = [args.only] if args.only else ["feedback", "complaint"]
    asyncio.run(main(selected, args.retag, args.limit))
