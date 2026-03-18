"""Track already-fetched article IDs for idempotency."""
import json
import logging
from pathlib import Path
from typing import Set

logger = logging.getLogger(__name__)

DEFAULT_TRACKER_PATH = Path("output/fetched_ids.json")


class FetchedTracker:
    """Persists a set of fetched article IDs to a JSON file."""

    def __init__(self, path: Path = DEFAULT_TRACKER_PATH):
        self._path = path
        self._ids: Set[str] = self._load()

    def _load(self) -> Set[str]:
        if self._path.exists():
            data = json.loads(self._path.read_text(encoding='utf-8'))
            ids = set(data.get('fetched_ids', []))
            logger.info("Loaded %d fetched IDs from %s", len(ids), self._path)
            return ids
        return set()

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        data = {'fetched_ids': sorted(self._ids)}
        self._path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding='utf-8',
        )

    def is_fetched(self, article_id: str) -> bool:
        return article_id in self._ids

    def mark_fetched(self, article_id: str) -> None:
        self._ids.add(article_id)
        self._save()

    @property
    def count(self) -> int:
        return len(self._ids)
