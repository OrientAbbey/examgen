import sqlite3
from contextlib import contextmanager

SCHEMA = """
CREATE TABLE IF NOT EXISTS matieres(
  id TEXT PRIMARY KEY, nom TEXT NOT NULL UNIQUE);
CREATE TABLE IF NOT EXISTS parties(
  id TEXT PRIMARY KEY,
  matiere_id TEXT NOT NULL REFERENCES matieres(id),
  nom TEXT NOT NULL, ordre INTEGER NOT NULL DEFAULT 0,
  UNIQUE(matiere_id, nom), UNIQUE(id, matiere_id));
CREATE TABLE IF NOT EXISTS classes(
  id TEXT PRIMARY KEY, nom TEXT NOT NULL UNIQUE,
  classe_precedente_id TEXT REFERENCES classes(id),
  a_examen INTEGER NOT NULL DEFAULT 0,
  specialite_obligatoire INTEGER NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS specialites(
  id TEXT PRIMARY KEY, nom TEXT NOT NULL UNIQUE);
CREATE TABLE IF NOT EXISTS exercices(
  id TEXT PRIMARY KEY, sujet TEXT NOT NULL, corrige TEXT NOT NULL,
  session INTEGER CHECK(session IS NULL OR session BETWEEN 1 AND 6),
  niveau TEXT NOT NULL CHECK(niveau IN ('Facile','Moyen','Difficile')),
  tag_examen INTEGER NOT NULL DEFAULT 0,
  updated_at TEXT NOT NULL,
  CHECK(session IS NOT NULL OR tag_examen = 0));
CREATE TABLE IF NOT EXISTS exercice_partie(
  exercice_id TEXT NOT NULL REFERENCES exercices(id) ON DELETE CASCADE,
  matiere_id TEXT NOT NULL, partie_id TEXT NOT NULL,
  PRIMARY KEY(exercice_id, matiere_id),
  FOREIGN KEY(partie_id, matiere_id) REFERENCES parties(id, matiere_id));
CREATE TABLE IF NOT EXISTS exercice_classe(
  exercice_id TEXT NOT NULL REFERENCES exercices(id) ON DELETE CASCADE,
  classe_id TEXT NOT NULL REFERENCES classes(id),
  PRIMARY KEY(exercice_id, classe_id));
CREATE TABLE IF NOT EXISTS exercice_specialite(
  exercice_id TEXT NOT NULL REFERENCES exercices(id) ON DELETE CASCADE,
  specialite_id TEXT NOT NULL,
  PRIMARY KEY(exercice_id, specialite_id));
CREATE TABLE IF NOT EXISTS generations(
  id TEXT PRIMARY KEY, user_id TEXT NOT NULL, created_at TEXT NOT NULL,
  cle TEXT NOT NULL,
  params TEXT NOT NULL, contenu TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS ix_gen_user ON generations(user_id, created_at);
CREATE TABLE IF NOT EXISTS journal(
  id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT NOT NULL, user_id TEXT NOT NULL,
  generation_id TEXT, type TEXT NOT NULL, params TEXT NOT NULL, details TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS ix_journal_type ON journal(type, id);
CREATE TABLE IF NOT EXISTS reglages(cle TEXT PRIMARY KEY, valeur TEXT);
"""


def connect(path: str) -> sqlite3.Connection:
    # isolation_level=None : autocommit ; les transactions passent par tx()
    conn = sqlite3.connect(path, check_same_thread=False, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    if path != ":memory:":
        conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)


@contextmanager
def tx(conn: sqlite3.Connection):
    conn.execute("BEGIN IMMEDIATE")
    try:
        yield
        conn.execute("COMMIT")
    except BaseException:
        conn.execute("ROLLBACK")
        raise
