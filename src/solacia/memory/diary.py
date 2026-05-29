"""
Solacia - Mood Diary Service

SQLite-backed mood diary with CRUD and emotion statistics.
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict
from solacia.config import settings


class DiaryService:
    """Mood diary persistence service."""

    def __init__(self, db_path: str = None):
        """
        Initialize diary service.

        Args:
            db_path: Path to SQLite database file.
        """
        self.db_path = db_path or settings.DB_PATH
        self._ensure_db_dir()
        self._init_db()

    def _ensure_db_dir(self):
        """Ensure the database directory exists."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

    def _init_db(self):
        """Initialize database tables."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS mood_diary (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    emotions TEXT NOT NULL,
                    summary TEXT,
                    message_count INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def create_entry(
        self,
        emotions: List[str],
        summary: str = None,
        message_count: int = 0,
        session_id: str = "default"
    ) -> dict:
        """
        Create a new diary entry.

        Args:
            emotions: List of emotion identifiers.
            summary: Conversation summary.
            message_count: Number of messages in the session.
            session_id: Session identifier (default: "default").

        Returns:
            Created diary entry as a dict.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                INSERT INTO mood_diary (session_id, timestamp, emotions, summary, message_count)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    datetime.now().isoformat(),
                    json.dumps(emotions),
                    summary,
                    message_count
                )
            )
            conn.commit()
            entry_id = cursor.lastrowid
            return {
                "id": entry_id,
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
                "emotions": emotions,
                "summary": summary,
                "message_count": message_count,
                "status": "created",
            }

    def get_entry(self, entry_id: int) -> Optional[Dict]:
        """
        Get a single diary entry by ID.

        Args:
            entry_id: Diary entry ID.

        Returns:
            Diary entry dict, or None if not found.
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM mood_diary WHERE id = ?",
                (entry_id,)
            )
            row = cursor.fetchone()
            if row:
                return self._row_to_dict(row)
            return None

    def get_entries(
        self,
        session_id: str = None,
        limit: int = 10,
        offset: int = 0
    ) -> List[Dict]:
        """
        Get a list of diary entries.

        Args:
            session_id: Filter by session ID (optional).
            limit: Max entries to return.
            offset: Number of entries to skip.

        Returns:
            List of diary entry dicts.
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            if session_id:
                cursor = conn.execute(
                    "SELECT * FROM mood_diary WHERE session_id = ? ORDER BY timestamp DESC LIMIT ? OFFSET ?",
                    (session_id, limit, offset)
                )
            else:
                cursor = conn.execute(
                    "SELECT * FROM mood_diary ORDER BY timestamp DESC LIMIT ? OFFSET ?",
                    (limit, offset)
                )

            rows = cursor.fetchall()
            return [self._row_to_dict(row) for row in rows]

    def get_emotion_stats(self, days: int = 7) -> Dict:
        """
        Get emotion statistics over a time period.

        Args:
            days: Number of days to look back.

        Returns:
            Dict mapping emotion identifiers to occurrence counts.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT emotions FROM mood_diary
                WHERE timestamp >= datetime('now', ?)
                """,
                (f'-{days} days',)
            )

            emotion_counts = {}
            for row in cursor.fetchall():
                emotions = json.loads(row[0])
                for emotion in emotions:
                    emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1

            return emotion_counts

    def _row_to_dict(self, row) -> Dict:
        """Convert a database row to a dict."""
        return {
            "id": row["id"],
            "session_id": row["session_id"],
            "timestamp": row["timestamp"],
            "emotions": json.loads(row["emotions"]),
            "summary": row["summary"],
            "message_count": row["message_count"],
            "created_at": row["created_at"]
        }
