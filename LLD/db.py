import sqlite3
import json
import pathlib
from contextlib import contextmanager
from typing import Dict, List, Tuple, Any

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

CREATE TABLE IF NOT EXISTS evaluations (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    class_id      INTEGER NOT NULL,
    overall_score REAL NOT NULL,
    feedback      TEXT NOT NULL,
    suggestions   TEXT NOT NULL,
    design_patterns TEXT NOT NULL,
    updated_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(class_id),
    FOREIGN KEY(class_id) REFERENCES classes(id) ON DELETE CASCADE
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

# -----------------------------------------------------------------------------
# Evaluation helpers
# -----------------------------------------------------------------------------

def _class_id(conn: sqlite3.Connection, problem_name: str, class_name: str) -> int:
    """Return the row id of a class for a given problem. Raises if not found."""
    pid = _problem_id(conn, problem_name)
    row = conn.execute(
        "SELECT id FROM classes WHERE problem_id = ? AND name = ?;",
        (pid, class_name.strip()),
    ).fetchone()
    if not row:
        raise ValueError(f"Class '{class_name}' for problem '{problem_name}' does not exist.")
    return int(row["id"])

def save_evaluation(problem_name: str, class_name: str, evaluation: Dict[str, Any]) -> None:
    """Insert or update an evaluation for a particular class design."""
    import json as _json

    with _get_conn() as conn:
        cid = _class_id(conn, problem_name, class_name)
        conn.execute(
            "INSERT INTO evaluations (class_id, overall_score, feedback, suggestions, design_patterns) "
            "VALUES (?, ?, ?, ?, ?) "
            "ON CONFLICT(class_id) DO UPDATE SET overall_score = excluded.overall_score, "
            "feedback = excluded.feedback, suggestions = excluded.suggestions, "
            "design_patterns = excluded.design_patterns, updated_at = CURRENT_TIMESTAMP;",
            (
                cid,
                evaluation.get("overall_score", 0),
                _json.dumps(evaluation.get("feedback", [])),
                _json.dumps(evaluation.get("suggestions", [])),
                _json.dumps(evaluation.get("design_patterns", [])),
            ),
        )

def fetch_evaluations(problem_name: str) -> Dict[str, Dict[str, Any]]:
    """Return mapping class_name -> evaluation dict for a problem."""
    import json as _json

    with _get_conn() as conn:
        pid = _problem_id(conn, problem_name)
        rows = conn.execute(
            "SELECT c.name as class_name, e.overall_score, e.feedback, e.suggestions, e.design_patterns "
            "FROM evaluations e JOIN classes c ON e.class_id = c.id "
            "WHERE c.problem_id = ?;",
            (pid,),
        ).fetchall()
    evaluations: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        evaluations[row["class_name"]] = {
            "overall_score": row["overall_score"],
            "feedback": _json.loads(row["feedback"]),
            "suggestions": _json.loads(row["suggestions"]),
            "design_patterns": _json.loads(row["design_patterns"]),
        }
    return evaluations
