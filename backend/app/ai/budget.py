"""A wall-clock deadline for narrative generation, and concurrency underneath it.

Why this exists, in one paragraph. `app/ai/openrouter.py` sizes its calls with `httpx` timeouts, and
`httpx` has no total-request setting: its `read` timeout bounds the gap *between* socket reads, not
the whole response. Anything that keeps the socket warm therefore keeps resetting the clock, and the
gateway does exactly that while a model generates. Measured on 2026-08-21, calls nominally budgeted
at 3.5 seconds took about six, and `POST /recommendations/backup-candidates` — up to three of them
in a row — reached 16.91s against the 12 seconds AC-14 allows an AI explanation operation. That is
`OPEN-11`. A configured timeout that the transport does not honour is not a budget, so the budget is
enforced here instead, by something that can stop waiting.

Two things are done together because either alone is insufficient:

* **Concurrency.** The candidate narratives are independent — three descriptions of three different
  people — so running them in sequence turns one call's latency into three. Running them together
  makes the endpoint cost roughly one call instead of `limit` of them.
* **A deadline.** Concurrency alone still trusts the transport to return. The deadline stops waiting
  at a fixed wall-clock point and uses the deterministic template for whatever has not arrived.

The fallback is not a degradation of correctness. Every narrative here is prose over facts the rules
already decided, and `app/ai/deterministic.py` holds a validated sentence for each one. Answering in
time with the template beats answering late with the model, which is the same judgement
`openrouter.py` already makes for a timeout or a rejected generation — this module only adds the
case where the model is merely *slow* rather than wrong.

**What a missed deadline does not do.** It does not cancel the underlying HTTP call. A thread already
inside a blocking `post` cannot be interrupted, so it runs to completion and its answer is discarded.
Those threads are bounded by the phase timeouts in `openrouter.py`, which is what those timeouts are
still good for, and the work is wasted rather than leaked. Cancelling for real would need an async
transport throughout, which is a larger change than the problem justifies.
"""

from __future__ import annotations

import logging
import time
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from concurrent.futures import TimeoutError as FuturesTimeout
from typing import Callable, Sequence, TypeVar

logger = logging.getLogger(__name__)

Item = TypeVar("Item")
Result = TypeVar("Result")


def narrate_in_parallel(
    items: Sequence[Item],
    narrate: Callable[[Item], Result],
    fallback: Callable[[Item], Result],
    deadline_seconds: float,
    max_workers: int,
) -> list[Result]:
    """Apply `narrate` to every item at once, bounded by one shared wall-clock deadline.

    Returns results in the order the items were given. For any item whose narration raises, or has
    not finished when the deadline passes, `fallback(item)` is used instead.

    `deadline_seconds` covers the whole set, not each item: the point is to bound what the endpoint
    costs, and one deadline per item would multiply by the number of items, which is the bug being
    fixed. A non-positive deadline means "do not call the model at all", which makes the budget
    configurable down to off.

    `fallback` must be cheap and must not fail — it is the deterministic template, and it is called
    on the calling thread after the deadline has already been spent.
    """
    if not items:
        return []

    # One item is not worth a thread hop, and this is the common case for anything that narrates a
    # single subject. The deadline still applies, via the transport's own timeouts.
    if len(items) == 1:
        return [_narrate_one(items[0], narrate, fallback)]

    if deadline_seconds <= 0:
        return [fallback(item) for item in items]

    started = time.monotonic()
    pool = ThreadPoolExecutor(max_workers=max(1, min(max_workers, len(items))))
    try:
        futures = [pool.submit(narrate, item) for item in items]

        # Wait on the set once with the remaining budget rather than per future, so a slow first
        # item cannot spend the whole deadline while later ones are already done.
        pending = set(futures)
        while pending:
            remaining = deadline_seconds - (time.monotonic() - started)
            if remaining <= 0:
                break
            done, pending = wait(pending, timeout=remaining, return_when=FIRST_COMPLETED)
            if not done:
                break

        results: list[Result] = []
        overdue = 0
        for item, future in zip(items, futures):
            if not future.done():
                overdue += 1
                results.append(fallback(item))
                continue
            try:
                results.append(future.result())
            except Exception as exc:  # noqa: BLE001 — the template is the answer to any failure
                logger.warning("narrative failed (%s); using the deterministic template", exc)
                results.append(fallback(item))

        if overdue:
            logger.warning(
                "%d of %d narratives missed the %.1fs budget; using the deterministic template "
                "for those",
                overdue,
                len(items),
                deadline_seconds,
            )
        return results
    finally:
        # `wait=False` is the point: blocking here until abandoned calls finish would give back
        # exactly the latency the deadline just saved. `cancel_futures` retires anything still
        # queued; anything already running finishes unobserved.
        pool.shutdown(wait=False, cancel_futures=True)


def _narrate_one(
    item: Item, narrate: Callable[[Item], Result], fallback: Callable[[Item], Result]
) -> Result:
    try:
        return narrate(item)
    except Exception as exc:  # noqa: BLE001 — same reason as above
        logger.warning("narrative failed (%s); using the deterministic template", exc)
        return fallback(item)


def with_deadline(
    work: Callable[[], Result],
    fallback: Callable[[], Result],
    deadline_seconds: float,
) -> Result:
    """One call, bounded by a real wall-clock deadline.

    The single-narrative counterpart to `narrate_in_parallel`. Needed because a lone call cannot be
    bounded by running it alongside others: `narrate_in_parallel` deliberately takes a direct path for
    one item, which leaves the transport's own timeouts as the only limit — and those do not bound
    anything, for the reason described at the top of this module.

    Measured, which is why this exists: with the deadline applied to the candidate narratives only,
    `POST /mitigation-plans` came back at **12.6 seconds** against AC-14's 12, live under
    `AI_PROVIDER=openrouter`. One call, comfortably past a nominal 7-second budget, exactly as the
    read-timeout hole predicts. A per-call budget the transport ignores is not a budget wherever it is
    applied, so the plan needs the same treatment the candidates got.

    Same limitation, stated again because it matters: missing the deadline does not cancel the HTTP
    call. The thread finishes unobserved and its answer is discarded, bounded by the phase timeouts.
    """
    if deadline_seconds <= 0:
        return fallback()

    pool = ThreadPoolExecutor(max_workers=1)
    try:
        future = pool.submit(work)
        try:
            return future.result(timeout=deadline_seconds)
        except FuturesTimeout:
            logger.warning(
                "narrative missed the %.1fs budget; using the deterministic template",
                deadline_seconds,
            )
            return fallback()
        except Exception as exc:  # noqa: BLE001 — the template is the answer to any failure
            logger.warning("narrative failed (%s); using the deterministic template", exc)
            return fallback()
    finally:
        # Never wait. Blocking here would hand back the latency the deadline just saved.
        pool.shutdown(wait=False, cancel_futures=True)
