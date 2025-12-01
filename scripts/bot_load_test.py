"""
Lightweight load test for the Telegram bot formatting/streaming pipeline.

This does not hit Telegram. It stresses the formatting/batching logic used in the
streaming callback to ensure vulnerability bursts are handled quickly.

Usage:
    poetry run python scripts/bot_load_test.py --events 1000 --concurrency 10 --mode batched
"""

import argparse
import asyncio
import time
from typing import List

SEVERITY_ICON = {"critical": "🔥", "high": "🔴", "medium": "🟠", "low": "🟢", "info": "ℹ️"}
MAX_MESSAGE_CHARS = 3500


def format_alert(sev: str, title: str, content: str) -> str:
    icon = SEVERITY_ICON.get(sev, "ℹ️")
    text = f"{icon} *{sev.upper()}* {title}\n```\n{content}\n```"
    if len(text) > MAX_MESSAGE_CHARS:
        text = text[:MAX_MESSAGE_CHARS] + "\n\n(truncated)"
    return text


async def worker(queue: asyncio.Queue, mode: str, batch_size: int) -> int:
    sent = 0
    batch: List[str] = []
    while True:
        item = await queue.get()
        if item is None:
            if batch:
                sent += len(batch)
            queue.task_done()
            break
        sev, title, content = item
        msg = format_alert(sev, title, content)
        if mode == "batched":
            batch.append(msg)
            if len(batch) >= batch_size:
                sent += len(batch)
                batch.clear()
        else:
            sent += 1
        queue.task_done()
    return sent


async def run_load(events: int, concurrency: int, mode: str, batch_size: int) -> None:
    queue: asyncio.Queue = asyncio.Queue()
    for i in range(events):
        sev = ["critical", "high", "medium", "low", "info"][i % 5]
        queue.put_nowait(
            (
                sev,
                f"title {i}",
                "A" * 4000,  # long content to trigger truncation path
            )
        )
    for _ in range(concurrency):
        queue.put_nowait(None)
    tasks = [asyncio.create_task(worker(queue, mode, batch_size)) for _ in range(concurrency)]
    start = time.perf_counter()
    await queue.join()
    elapsed = time.perf_counter() - start
    sent = sum(t.result() for t in tasks)
    rate = sent / elapsed if elapsed else sent
    print(f"Processed {events} events in {elapsed:.2f}s ({rate:.1f} msg/s) mode={mode} batch={batch_size}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--events", type=int, default=1000)
    parser.add_argument("--concurrency", type=int, default=10)
    parser.add_argument("--mode", choices=["full", "batched"], default="batched")
    parser.add_argument("--batch-size", type=int, default=50)
    args = parser.parse_args()
    asyncio.run(run_load(args.events, args.concurrency, args.mode, args.batch_size))


if __name__ == "__main__":
    main()
