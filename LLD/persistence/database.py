"""SQLite helper layer of the application (moved from ``LLD.db``)."""

from __future__ import annotations

import json
import pathlib
import sqlite3
from contextlib import contextmanager
from typing import Any, Dict

# Use absolute import to avoid circulars
from LLD.core.models import ClassDesign

# -----------------------------------------------------------------------------
# SQLite connection helpers
# -----------------------------------------------------------------------------

DB_PATH = pathlib.Path(__file__).resolve().parent.parent / "lld_data.db"


@contextmanager
def _get_conn():
    """Yield a SQLite connection with foreign-keys ON and row factory dict."""

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
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
    code            TEXT NOT NULL DEFAULT '',
    UNIQUE(name, problem_id),
    FOREIGN KEY(problem_id) REFERENCES problems(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS code_implementations (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    class_id      INTEGER NOT NULL UNIQUE,
    code          TEXT NOT NULL,
    analysis      TEXT NOT NULL,
    updated_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(class_id) REFERENCES classes(id) ON DELETE CASCADE
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

CREATE TABLE IF NOT EXISTS overall_design_evaluations (
    problem_id      INTEGER PRIMARY KEY,  -- one row per problem
    overall_score   REAL NOT NULL,
    feedback        TEXT NOT NULL,
    missing_classes TEXT NOT NULL,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(problem_id) REFERENCES problems(id) ON DELETE CASCADE
);
"""

MIGRATIONS: list[str] = [
    # Add 'code' column to existing 'classes' table if it doesn't exist
    "ALTER TABLE classes ADD COLUMN code TEXT NOT NULL DEFAULT ''",
    # Ensure code_implementations table exists
    "CREATE TABLE IF NOT EXISTS code_implementations (\n        id            INTEGER PRIMARY KEY AUTOINCREMENT,\n        class_id      INTEGER NOT NULL UNIQUE,\n        code          TEXT NOT NULL,\n        analysis      TEXT NOT NULL,\n        updated_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,\n        FOREIGN KEY(class_id) REFERENCES classes(id) ON DELETE CASCADE\n    );",
    # Ensure implementation_evaluations table exists
    "CREATE TABLE IF NOT EXISTS implementation_evaluations (\n        id            INTEGER PRIMARY KEY AUTOINCREMENT,\n        class_id      INTEGER NOT NULL UNIQUE,\n        overall_score REAL NOT NULL,\n        feedback      TEXT NOT NULL,\n        suggestions   TEXT NOT NULL,\n        design_patterns TEXT NOT NULL,\n        updated_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,\n        FOREIGN KEY(class_id) REFERENCES classes(id) ON DELETE CASCADE\n    );",
    # Ensure overall_design_evaluations table exists
    "CREATE TABLE IF NOT EXISTS overall_design_evaluations (\n        problem_id      INTEGER PRIMARY KEY,\n        overall_score   REAL NOT NULL,\n        feedback        TEXT NOT NULL,\n        missing_classes TEXT NOT NULL,\n        updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,\n        FOREIGN KEY(problem_id) REFERENCES problems(id) ON DELETE CASCADE\n    );",
]


def _apply_migrations(conn: sqlite3.Connection) -> None:  # noqa: D401
    """Attempt to run best-effort migrations, ignoring failures for already-applied ones."""

    for stmt in MIGRATIONS:
        try:
            conn.execute(stmt)
        except sqlite3.OperationalError:
            # Likely the column/table already exists – safe to ignore.
            continue

# Modify init_db to call migrations

def init_db() -> None:
    """Create tables on first run and run migrations."""

    with _get_conn() as conn:
        conn.executescript(INIT_SCRIPT)
        _apply_migrations(conn)


# -----------------------------------------------------------------------------
# Problem helpers
# -----------------------------------------------------------------------------

def save_problem(name: str, requirements: str) -> None:  # noqa: D401
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


def save_class_design(problem_name: str, class_design: ClassDesign) -> None:  # noqa: D401
    with _get_conn() as conn:
        pid = _problem_id(conn, problem_name)
        serialized = {
            "responsibilities": json.dumps(class_design.responsibilities),
            "attributes": json.dumps(class_design.attributes),
            "methods": json.dumps(class_design.methods),
            "relationships": json.dumps(class_design.relationships),
        }
        conn.execute(
            "INSERT INTO classes (problem_id, name, responsibilities, attributes, methods, relationships, code) "
            "VALUES (?, ?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(name, problem_id) DO UPDATE SET "
            "responsibilities = excluded.responsibilities, "
            "attributes = excluded.attributes, "
            "methods = excluded.methods, "
            "relationships = excluded.relationships, "
            "code = excluded.code;",
            (
                pid,
                class_design.name.strip(),
                serialized["responsibilities"],
                serialized["attributes"],
                serialized["methods"],
                serialized["relationships"],
                class_design.code,
            ),
        )


def delete_class_design(problem_name: str, class_name: str) -> None:
    with _get_conn() as conn:
        pid = _problem_id(conn, problem_name)
        conn.execute(
            "DELETE FROM classes WHERE problem_id = ? AND name = ?;", (pid, class_name.strip())
        )


def fetch_class_designs(problem_name: str) -> Dict[str, ClassDesign]:
    with _get_conn() as conn:
        pid = _problem_id(conn, problem_name)
        rows = conn.execute(
            "SELECT name, responsibilities, attributes, methods, relationships, code FROM classes WHERE problem_id = ? ORDER BY name;",
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
        designs[row["name"]].code = row["code"]
    return designs


# -----------------------------------------------------------------------------
# Evaluation helpers
# -----------------------------------------------------------------------------

def _class_id(conn: sqlite3.Connection, problem_name: str, class_name: str) -> int:
    pid = _problem_id(conn, problem_name)
    row = conn.execute(
        "SELECT id FROM classes WHERE problem_id = ? AND name = ?;",
        (pid, class_name.strip()),
    ).fetchone()
    if not row:
        raise ValueError(
            f"Class '{class_name}' for problem '{problem_name}' does not exist."
        )
    return int(row["id"])


def save_evaluation(problem_name: str, class_name: str, evaluation: Dict[str, Any]) -> None:  # noqa: D401
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
                json.dumps(evaluation.get("feedback", [])),
                json.dumps(evaluation.get("suggestions", [])),
                json.dumps(evaluation.get("design_patterns", [])),
            ),
        )


def fetch_evaluations(problem_name: str) -> Dict[str, Dict[str, Any]]:
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
            "feedback": json.loads(row["feedback"]),
            "suggestions": json.loads(row["suggestions"]),
            "design_patterns": json.loads(row["design_patterns"]),
        }
    return evaluations


# -----------------------------------------------------------------------------
# Code implementation helpers
# -----------------------------------------------------------------------------

def save_code_implementation(
    problem_name: str,
    class_name: str,
    code: str,
    analysis: Dict[str, Any] | str = "",
) -> None:  # noqa: D401
    """Persist a code implementation and its analysis for a given class/problem."""

    analysis_json = (
        json.dumps(analysis) if not isinstance(analysis, str) else analysis
    )
    with _get_conn() as conn:
        cid = _class_id(conn, problem_name, class_name)
        conn.execute(
            "INSERT INTO code_implementations (class_id, code, analysis) "
            "VALUES (?, ?, ?) "
            "ON CONFLICT(class_id) DO UPDATE SET code = excluded.code, "
            "analysis = excluded.analysis, updated_at = CURRENT_TIMESTAMP;",
            (cid, code, analysis_json),
        )


def fetch_code_implementations(problem_name: str) -> Dict[str, Dict[str, Any]]:
    """Return a mapping of class name to its saved code & analysis."""

    with _get_conn() as conn:
        pid = _problem_id(conn, problem_name)
        rows = conn.execute(
            "SELECT c.name AS class_name, ci.code, ci.analysis "
            "FROM code_implementations ci JOIN classes c ON ci.class_id = c.id "
            "WHERE c.problem_id = ?;",
            (pid,),
        ).fetchall()
    return {
        row["class_name"]: {
            "code": row["code"],
            "analysis": json.loads(row["analysis"]) if row["analysis"] else {},
        }
        for row in rows
    }


# -----------------------------------------------------------------------------
# Implementation evaluation helpers
# -----------------------------------------------------------------------------

def save_implementation_evaluation(
    problem_name: str,
    class_name: str,
    evaluation: Dict[str, Any],
) -> None:  # noqa: D401
    """Persist evaluation for a class code implementation."""

    with _get_conn() as conn:
        cid = _class_id(conn, problem_name, class_name)
        conn.execute(
            "INSERT INTO implementation_evaluations (class_id, overall_score, feedback, suggestions, design_patterns) "
            "VALUES (?, ?, ?, ?, ?) "
            "ON CONFLICT(class_id) DO UPDATE SET overall_score = excluded.overall_score, "
            "feedback = excluded.feedback, suggestions = excluded.suggestions, "
            "design_patterns = excluded.design_patterns, updated_at = CURRENT_TIMESTAMP;",
            (
                cid,
                evaluation.get("overall_score", 0),
                json.dumps(evaluation.get("feedback", [])),
                json.dumps(evaluation.get("suggestions", [])),
                json.dumps(evaluation.get("design_patterns", [])),
            ),
        )


def fetch_implementation_evaluations(problem_name: str) -> Dict[str, Dict[str, Any]]:
    """Fetch evaluations of implementations for a given problem."""

    with _get_conn() as conn:
        pid = _problem_id(conn, problem_name)
        rows = conn.execute(
            "SELECT c.name as class_name, ie.overall_score, ie.feedback, ie.suggestions, ie.design_patterns "
            "FROM implementation_evaluations ie JOIN classes c ON ie.class_id = c.id "
            "WHERE c.problem_id = ?;",
            (pid,),
        ).fetchall()
    return {
        row["class_name"]: {
            "overall_score": row["overall_score"],
            "feedback": json.loads(row["feedback"]),
            "suggestions": json.loads(row["suggestions"]),
            "design_patterns": json.loads(row["design_patterns"]),
        }
        for row in rows
    }


# -----------------------------------------------------------------------------
# Overall design evaluation helpers
# -----------------------------------------------------------------------------

def save_overall_design_evaluation(
    problem_name: str,
    evaluation: Dict[str, Any],
) -> None:  # noqa: D401
    """Persist an overall design evaluation for a given problem."""

    with _get_conn() as conn:
        pid = _problem_id(conn, problem_name)
        conn.execute(
            "INSERT INTO overall_design_evaluations (problem_id, overall_score, feedback, missing_classes) "
            "VALUES (?, ?, ?, ?) "
            "ON CONFLICT(problem_id) DO UPDATE SET overall_score = excluded.overall_score, "
            "feedback = excluded.feedback, missing_classes = excluded.missing_classes, "
            "updated_at = CURRENT_TIMESTAMP;",
            (
                pid,
                evaluation.get("overall_score", 0),
                json.dumps(evaluation.get("feedback", [])),
                json.dumps(evaluation.get("missing_classes", [])),
            ),
        )


def fetch_overall_design_evaluation(problem_name: str) -> Dict[str, Any] | None:
    """Fetch overall design evaluation for a problem, if present."""

    with _get_conn() as conn:
        pid = _problem_id(conn, problem_name)
        row = conn.execute(
            "SELECT overall_score, feedback, missing_classes FROM overall_design_evaluations WHERE problem_id = ?;",
            (pid,),
        ).fetchone()
    if not row:
        return None
    return {
        "overall_score": row["overall_score"],
        "feedback": json.loads(row["feedback"]),
        "missing_classes": json.loads(row["missing_classes"]),
    }


# Export public symbols -------------------------------------------------------

__all__ = [
    "init_db",
    "save_problem",
    "delete_problem",
    "fetch_problems",
    "save_class_design",
    "delete_class_design",
    "fetch_class_designs",
    "save_evaluation",
    "fetch_evaluations",
    "save_code_implementation",
    "fetch_code_implementations",
    "save_implementation_evaluation",
    "fetch_implementation_evaluations",
    "save_overall_design_evaluation",
    "fetch_overall_design_evaluation",
]
