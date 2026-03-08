"""
s3_poller.py
~~~~~~~~~~~~
Background cron worker that polls S3 every 30 seconds, detects newly uploaded
documents that have no description yet, and uses Gemini AI to auto-generate one.

Queue behaviour
---------------
A single asyncio.Queue (FIFO) plus an "in‑flight" set prevent the same s3_key
from being enqueued twice even if multiple poll cycles overlap.

Only the `description` column is updated — every other column in the documents
table is left untouched.
"""
import asyncio
import logging
from datetime import datetime, timezone

from app.db.base import SessionLocal
from app.models.document import Document
from app.services.s3_service import list_files_in_s3, download_bytes_from_s3
from app.services.text_extractor import extract_text_from_bytes
from app.services.description_service import generate_description

logger = logging.getLogger(__name__)

POLL_INTERVAL_SECONDS = 30
S3_PREFIX = "beef-documents/"

# ── Shared queue state ────────────────────────────────────────────────────────
_queue: asyncio.Queue = None          # populated by start_poller()
_in_flight: set = set()               # keys currently queued or being processed
_in_flight_lock: asyncio.Lock = None  # protects _in_flight


# ── Queue consumer ────────────────────────────────────────────────────────────
async def _process_queue() -> None:
    """
    Long‑running coroutine that consumes s3_key items from the queue one by
    one, generates an AI description, and writes it to the DB.
    """
    global _in_flight, _in_flight_lock

    while True:
        s3_key: str = await _queue.get()
        try:
            logger.info("[S3 Poller] Processing queued file: %s", s3_key)

            # 1. Download raw bytes from S3
            try:
                raw_bytes = download_bytes_from_s3(s3_key)
            except Exception as exc:
                logger.error("[S3 Poller] Failed to download s3://%s — %s", s3_key, exc)
                continue  # skip; will be retried next poll cycle

            # 2. Extract plain text from binary (PDF / DOCX / text)
            try:
                content = extract_text_from_bytes(raw_bytes, s3_key)
            except Exception as exc:
                logger.error("[S3 Poller] Text extraction failed for %s — %s", s3_key, exc)
                continue

            if not content.strip():
                logger.warning(
                    "[S3 Poller] No text could be extracted from %s — skipping description.",
                    s3_key,
                )
                continue

            # 3. Generate AI description from extracted text
            try:
                description = generate_description(s3_key, content)
            except Exception as exc:
                logger.error("[S3 Poller] Description generation failed for %s — %s", s3_key, exc)
                continue

            # 4. Write description ONLY to the matching document row
            db = SessionLocal()
            try:
                doc = db.query(Document).filter(Document.s3_key == s3_key).first()
                if doc is None:
                    logger.warning("[S3 Poller] No DB row found for s3_key=%s", s3_key)
                    continue

                # Update only the description field
                doc.description = description
                db.commit()
                logger.info(
                    "[S3 Poller] ✅ Description saved for document id=%s (%s)",
                    doc.id,
                    doc.document_name,
                )
            except Exception as exc:
                db.rollback()
                logger.error("[S3 Poller] DB update failed for %s — %s", s3_key, exc)
            finally:
                db.close()

        finally:
            # Always release the key so it can be re-queued if needed
            async with _in_flight_lock:
                _in_flight.discard(s3_key)
            _queue.task_done()


# ── Poller (one iteration) ────────────────────────────────────────────────────
async def _poll_once() -> None:
    """
    List all S3 objects, find those whose s3_key has no description in the DB,
    and enqueue them (deduplication via _in_flight set).
    """
    global _in_flight, _in_flight_lock

    logger.debug("[S3 Poller] Polling S3 prefix=%s …", S3_PREFIX)

    # 1. Get all S3 keys under the prefix
    try:
        s3_objects = list_files_in_s3(prefix=S3_PREFIX)
    except Exception as exc:
        logger.error("[S3 Poller] S3 list failed: %s", exc)
        return

    if not s3_objects:
        logger.debug("[S3 Poller] No objects found in S3 under prefix=%s", S3_PREFIX)
        return

    s3_keys_in_bucket = {obj["key"] for obj in s3_objects}

    # 2. Query the DB for documents that have a matching s3_key AND no description
    db = SessionLocal()
    try:
        docs_needing_desc = (
            db.query(Document)
            .filter(
                Document.s3_key.in_(s3_keys_in_bucket),
                Document.description.is_(None),
            )
            .all()
        )
    except Exception as exc:
        logger.error("[S3 Poller] DB query failed: %s", exc)
        return
    finally:
        db.close()

    if not docs_needing_desc:
        logger.debug("[S3 Poller] All matched documents already have descriptions.")
        return

    logger.info(
        "[S3 Poller] Found %d document(s) needing description generation.",
        len(docs_needing_desc),
    )

    # 3. Enqueue new keys (skip duplicates already in-flight)
    async with _in_flight_lock:
        for doc in docs_needing_desc:
            if doc.s3_key not in _in_flight:
                _in_flight.add(doc.s3_key)
                await _queue.put(doc.s3_key)
                logger.info("[S3 Poller] Enqueued: %s", doc.s3_key)
            else:
                logger.debug("[S3 Poller] Already in-flight, skipping: %s", doc.s3_key)


# ── Entry point ───────────────────────────────────────────────────────────────
async def start_poller() -> None:
    """
    Initialise the queue and start the background poll loop.
    Call this once from the FastAPI lifespan startup handler.
    """
    global _queue, _in_flight, _in_flight_lock

    _queue = asyncio.Queue()
    _in_flight = set()
    _in_flight_lock = asyncio.Lock()

    logger.info(
        "[S3 Poller] Starting — poll interval=%ds, prefix=%s",
        POLL_INTERVAL_SECONDS,
        S3_PREFIX,
    )

    # Start the consumer coroutine
    asyncio.create_task(_process_queue())

    # Main poll loop
    while True:
        try:
            await _poll_once()
        except Exception as exc:
            logger.error("[S3 Poller] Unexpected error in poll loop: %s", exc)

        await asyncio.sleep(POLL_INTERVAL_SECONDS)
