import sqlite3
import json
import pathlib
from contextlib import contextmanager
from typing import Dict, List, Tuple

from .models import ClassDesign

# -----------------------------------------------------------------------------
# SQLite connection helpers
# -----------------------------------------------------------------------------
DB_PATH = pathlib.Path(__file__).resolve().parent / "lld_data.db"

@contextmanager
def _get_conn():
    """Context-manager that yields a SQLite connection with foreign-keys ON."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # access columns by name
    conn.execute("PRAGMA foreign_keys = ON;")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

# -----------------------------------------------------------------------------
# Schema management
# -----------------------------------------------------------------------------
INIT_SCRIPT = """
CREATE TABLE IF NOT EXISTS problems (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    name         TEXT UNIQUE NOT NULL,
    requirements TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS classes (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    problem_id     INTEGER NOT NULL,
    name           TEXT NOT NULL,
    responsibilities TEXT NOT NULL,
    attributes      TEXT NOT NULL,
    methods         TEXT NOT NULL,
    relationships   TEXT NOT NULL,
    UNIQUE(name, problem_id),
    FOREIGN KEY(problem_id) REFERENCES problems(id) ON DELETE CASCADE
);
"""

def init_db() -> None:
    """Initialize the database (create tables on first run)."""
    with _get_conn() as conn:
        conn.executescript(INIT_SCRIPT)

# -----------------------------------------------------------------------------
# Problem helpers
# -----------------------------------------------------------------------------

def save_problem(name: str, requirements: str) -> None:
    """Insert or update a problem statement."""
    with _get_conn() as conn:
        conn.execute(
            "INSERT INTO problems (name, requirements) VALUES (?, ?) "
            "ON CONFLICT(name) DO UPDATE SET requirements = excluded.requirements;",
            (name.strip(), requirements.strip()),
        )

def delete_problem(name: str) -> None:
    with _get_conn() as conn:
        conn.execute("DELETE FROM problems WHERE name = ?;", (name.strip(),))

def fetch_problems() -> Dict[str, str]:
    """Return a mapping of problem name -> requirements."""
    with _get_conn() as conn:
        rows = conn.execute("SELECT name, requirements FROM problems ORDER BY name;").fetchall()
    return {row["name"]: row["requirements"] for row in rows}

# -----------------------------------------------------------------------------
# Class design helpers
# -----------------------------------------------------------------------------

def _problem_id(conn: sqlite3.Connection, name: str) -> int:
    row = conn.execute("SELECT id FROM problems WHERE name = ?;", (name.strip(),)).fetchone()
    if not row:
        raise ValueError(f"Problem '{name}' does not exist.")
    return int(row["id"])

def save_class_design(problem_name: str, class_design: ClassDesign) -> None:
    """Insert or update a class design linked to a problem."""
    with _get_conn() as conn:
        pid = _problem_id(conn, problem_name)
        serialized = {
            "responsibilities": json.dumps(class_design.responsibilities),
            "attributes": json.dumps(class_design.attributes),
            "methods": json.dumps(class_design.methods),
            "relationships": json.dumps(class_design.relationships),
        }
        conn.execute(
            "INSERT INTO classes (problem_id, name, responsibilities, attributes, methods, relationships) "
            "VALUES (?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(name, problem_id) DO UPDATE SET "
            "responsibilities = excluded.responsibilities, "
            "attributes = excluded.attributes, "
            "methods = excluded.methods, "
            "relationships = excluded.relationships;",
            (
                pid,
                class_design.name.strip(),
                serialized["responsibilities"],
                serialized["attributes"],
                serialized["methods"],
                serialized["relationships"],
            ),
        )

def delete_class_design(problem_name: str, class_name: str) -> None:
    with _get_conn() as conn:
        pid = _problem_id(conn, problem_name)
        conn.execute("DELETE FROM classes WHERE problem_id = ? AND name = ?;", (pid, class_name.strip()))

def fetch_class_designs(problem_name: str) -> Dict[str, ClassDesign]:
    """Load all class designs for a given problem and return as a mapping."""
    with _get_conn() as conn:
        pid = _problem_id(conn, problem_name)
        rows = conn.execute(
            "SELECT name, responsibilities, attributes, methods, relationships FROM classes WHERE problem_id = ? ORDER BY name;",
            (pid,),
        ).fetchall()
    designs: Dict[str, ClassDesign] = {}
    for row in rows:
        designs[row["name"]] = ClassDesign(
            name=row["name"],
            responsibilities=json.loads(row["responsibilities"]),
            attributes=json.loads(row["attributes"]),
            methods=json.loads(row["methods"]),
            relationships=json.loads(row["relationships"]),
        )
    return designs
