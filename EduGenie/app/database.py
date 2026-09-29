import hashlib
import sqlite3
from pathlib import Path
from threading import Lock

from .config import settings


DB_LOCK = Lock()


def get_conn():
    """
    Create and return a SQLite database connection.
    """

    path = Path(settings.database_path)

    # Create the data folder if it doesn't exist.
    path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(
        path,
        check_same_thread=False,
    )

    conn.row_factory = sqlite3.Row

    return conn


def init_db():
    """
    Create all required database tables.
    """

    with DB_LOCK:
        conn = get_conn()

        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS study_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                feature TEXT NOT NULL,
                input_text TEXT,
                output_text TEXT,
                score INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY(user_id)
                    REFERENCES users(id)
            );
            """
        )

        conn.commit()
        conn.close()


def hash_password(password: str) -> str:
    """
    Hash a password using SHA-256.

    This is acceptable for this educational/local project.
    Production applications should use Argon2 or bcrypt.
    """

    return hashlib.sha256(
        password.encode("utf-8")
    ).hexdigest()


def create_user(username: str, password: str):
    """
    Create a new user.

    Returns:
        user id if successful
        None if username already exists
    """

    with DB_LOCK:
        conn = get_conn()

        try:
            cursor = conn.execute(
                """
                INSERT INTO users(username, password_hash)
                VALUES (?, ?)
                """,
                (
                    username,
                    hash_password(password),
                ),
            )

            conn.commit()

            return cursor.lastrowid

        except sqlite3.IntegrityError:
            return None

        finally:
            conn.close()


def authenticate(username: str, password: str):
    """
    Check username and password.

    Returns the user dictionary if valid.
    """

    conn = get_conn()

    row = conn.execute(
        """
        SELECT id, username
        FROM users
        WHERE username = ?
        AND password_hash = ?
        """,
        (
            username,
            hash_password(password),
        ),
    ).fetchone()

    conn.close()

    if row:
        return dict(row)

    return None


def add_log(
    user_id: int,
    feature: str,
    input_text: str,
    output_text: str,
    score=None,
):
    """
    Save an AI activity to study history.
    """

    with DB_LOCK:
        conn = get_conn()

        conn.execute(
            """
            INSERT INTO study_logs(
                user_id,
                feature,
                input_text,
                output_text,
                score
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                user_id,
                feature,
                input_text,
                output_text,
                score,
            ),
        )

        conn.commit()
        conn.close()


def get_logs(
    user_id: int,
    limit: int = 20,
):
    """
    Get recent study activity.
    """

    conn = get_conn()

    rows = conn.execute(
        """
        SELECT
            id,
            feature,
            input_text,
            output_text,
            score,
            created_at
        FROM study_logs
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT ?
        """,
        (
            user_id,
            limit,
        ),
    ).fetchall()

    conn.close()

    return [dict(row) for row in rows]