"""Accès données de l'administration : CRUD + intégrité référentielle (cahier 3.1 / 3.2)."""
import json
import sqlite3
import uuid
from datetime import datetime, timezone

from .classes_tree import CycleError, assert_acyclic
from .db import tx
from .errors import ApiError
from .models import AUCUNE, ClasseIn, ExerciceIn, PartieIn


def new_id() -> str:
    return str(uuid.uuid4())


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


def _dup(e: sqlite3.IntegrityError) -> ApiError:
    return ApiError(409, "DUPLICATE_NAME" if "UNIQUE" in str(e) else "INTEGRITY", str(e))


def _one(conn, sql, args=()):
    return conn.execute(sql, args).fetchone()


def _need(conn, table: str, id_: str, code: str):
    row = _one(conn, f"SELECT * FROM {table} WHERE id=?", (id_,))
    if row is None:
        raise ApiError(404, code, f"{table}: introuvable")
    return row


# ───────────────────────── Matières ─────────────────────────
def list_matieres(conn):
    return [dict(r) for r in conn.execute(
        """SELECT m.id, m.nom,
             (SELECT COUNT(*) FROM parties p WHERE p.matiere_id=m.id) AS nbParties,
             (SELECT COUNT(*) FROM exercice_partie ep WHERE ep.matiere_id=m.id) AS nbExercices
           FROM matieres m ORDER BY m.nom""")]


def create_matiere(conn, nom):
    id_ = new_id()
    try:
        with tx(conn):
            conn.execute("INSERT INTO matieres(id,nom) VALUES(?,?)", (id_, nom))
    except sqlite3.IntegrityError as e:
        raise _dup(e)
    return {"id": id_, "nom": nom}


def rename_matiere(conn, id_, nom):
    _need(conn, "matieres", id_, "NOT_FOUND")
    try:
        with tx(conn):
            conn.execute("UPDATE matieres SET nom=? WHERE id=?", (nom, id_))
    except sqlite3.IntegrityError as e:
        raise _dup(e)
    return {"id": id_, "nom": nom}


def delete_matiere(conn, id_, reassign_to=None, reassign_partie_id=None):
    _need(conn, "matieres", id_, "NOT_FOUND")
    refs = [r["exercice_id"] for r in conn.execute(
        "SELECT exercice_id FROM exercice_partie WHERE matiere_id=?", (id_,))]
    if refs and not reassign_to:
        raise ApiError(409, "REFERENCED", "Matière référencée par des exercices", count=len(refs))
    with tx(conn):
        if refs:
            if reassign_to == id_:
                raise ApiError(422, "BAD_REASSIGN", "Cible identique")
            _need(conn, "matieres", reassign_to, "BAD_REASSIGN")
            p = _one(conn, "SELECT id FROM parties WHERE id=? AND matiere_id=?",
                     (reassign_partie_id, reassign_to))
            if p is None:
                raise ApiError(422, "BAD_REASSIGN", "reassignPartieId doit appartenir à la matière cible")
            for ex in refs:
                if _one(conn, "SELECT 1 FROM exercice_partie WHERE exercice_id=? AND matiere_id=?",
                        (ex, reassign_to)):
                    conn.execute("DELETE FROM exercice_partie WHERE exercice_id=? AND matiere_id=?", (ex, id_))
                else:
                    conn.execute(
                        "UPDATE exercice_partie SET matiere_id=?, partie_id=? WHERE exercice_id=? AND matiere_id=?",
                        (reassign_to, reassign_partie_id, ex, id_))
        conn.execute("DELETE FROM parties WHERE matiere_id=?", (id_,))
        conn.execute("DELETE FROM matieres WHERE id=?", (id_,))


# ───────────────────────── Parties ─────────────────────────
def list_parties(conn, matiere_id=None):
    sql = """SELECT p.id, p.matiere_id AS matiereId, p.nom, p.ordre,
               (SELECT COUNT(*) FROM exercice_partie ep WHERE ep.partie_id=p.id) AS nbExercices
             FROM parties p"""
    args = ()
    if matiere_id:
        sql += " WHERE p.matiere_id=?"
        args = (matiere_id,)
    return [dict(r) for r in conn.execute(sql + " ORDER BY p.matiere_id, p.ordre, p.nom", args)]


def create_partie(conn, d: PartieIn):
    _need(conn, "matieres", d.matiereId, "UNKNOWN_MATIERE")
    id_ = new_id()
    try:
        with tx(conn):
            conn.execute("INSERT INTO parties(id,matiere_id,nom,ordre) VALUES(?,?,?,?)",
                         (id_, d.matiereId, d.nom, d.ordre))
    except sqlite3.IntegrityError as e:
        raise _dup(e)
    return {"id": id_, "matiereId": d.matiereId, "nom": d.nom, "ordre": d.ordre}


def update_partie(conn, id_, d: PartieIn):
    row = _need(conn, "parties", id_, "NOT_FOUND")
    if row["matiere_id"] != d.matiereId:
        raise ApiError(422, "IMMUTABLE", "Une partie ne peut pas changer de matière")
    try:
        with tx(conn):
            conn.execute("UPDATE parties SET nom=?, ordre=? WHERE id=?", (d.nom, d.ordre, id_))
    except sqlite3.IntegrityError as e:
        raise _dup(e)
    return {"id": id_, "matiereId": d.matiereId, "nom": d.nom, "ordre": d.ordre}


def delete_partie(conn, id_, reassign_to=None):
    row = _need(conn, "parties", id_, "NOT_FOUND")
    n = _one(conn, "SELECT COUNT(*) c FROM exercice_partie WHERE partie_id=?", (id_,))["c"]
    if n and not reassign_to:
        # inclut le cas « dernière partie d'une matière » : sans autre partie, aucune cible possible
        raise ApiError(409, "REFERENCED", "Partie référencée par des exercices", count=n)
    with tx(conn):
        if n:
            if reassign_to == id_ or _one(conn, "SELECT 1 FROM parties WHERE id=? AND matiere_id=?",
                                          (reassign_to, row["matiere_id"])) is None:
                raise ApiError(422, "BAD_REASSIGN", "La cible doit être une autre partie de la même matière")
            conn.execute("UPDATE exercice_partie SET partie_id=? WHERE partie_id=?", (reassign_to, id_))
        conn.execute("DELETE FROM parties WHERE id=?", (id_,))


# ───────────────────────── Classes ─────────────────────────
def _prev_map(conn, override=None, drop=None):
    m = {r["id"]: r["classe_precedente_id"] for r in conn.execute("SELECT id, classe_precedente_id FROM classes")}
    if drop:
        m.pop(drop, None)
    if override:
        m.update(override)
    return m


def _check_cycle(m):
    try:
        assert_acyclic(m)
    except CycleError:
        raise ApiError(422, "CYCLE", "Cycle détecté dans les classes précédentes")


def _classe_dict(conn, r, prev=None):
    from .classes_tree import ancestors
    prev = prev if prev is not None else _prev_map(conn)
    names = {x["id"]: x["nom"] for x in conn.execute("SELECT id, nom FROM classes")}
    return {"id": r["id"], "nom": r["nom"], "classePrecedenteId": r["classe_precedente_id"],
            "aExamen": bool(r["a_examen"]), "specialiteObligatoire": bool(r["specialite_obligatoire"]),
            "arborescence": [names[a] for a in ancestors(prev, r["id"])]}


def list_classes(conn):
    prev = _prev_map(conn)
    return [_classe_dict(conn, r, prev) for r in conn.execute("SELECT * FROM classes ORDER BY nom")]


def create_classe(conn, d: ClasseIn):
    if d.classePrecedenteId:
        _need(conn, "classes", d.classePrecedenteId, "UNKNOWN_CLASSE")
    id_ = new_id()
    _check_cycle(_prev_map(conn, {id_: d.classePrecedenteId}))
    try:
        with tx(conn):
            conn.execute("INSERT INTO classes(id,nom,classe_precedente_id,a_examen,specialite_obligatoire) VALUES(?,?,?,?,?)",
                         (id_, d.nom, d.classePrecedenteId, int(d.aExamen), int(d.specialiteObligatoire)))
    except sqlite3.IntegrityError as e:
        raise _dup(e)
    return _classe_dict(conn, _need(conn, "classes", id_, "NOT_FOUND"))


def update_classe(conn, id_, d: ClasseIn):
    _need(conn, "classes", id_, "NOT_FOUND")
    if d.classePrecedenteId:
        _need(conn, "classes", d.classePrecedenteId, "UNKNOWN_CLASSE")
    _check_cycle(_prev_map(conn, {id_: d.classePrecedenteId}))
    try:
        with tx(conn):
            conn.execute("UPDATE classes SET nom=?, classe_precedente_id=?, a_examen=?, specialite_obligatoire=? WHERE id=?",
                         (d.nom, d.classePrecedenteId, int(d.aExamen), int(d.specialiteObligatoire), id_))
    except sqlite3.IntegrityError as e:
        raise _dup(e)
    return _classe_dict(conn, _need(conn, "classes", id_, "NOT_FOUND"))


def delete_classe(conn, id_, reassign_to=None):
    _need(conn, "classes", id_, "NOT_FOUND")
    n_ex = _one(conn, "SELECT COUNT(*) c FROM exercice_classe WHERE classe_id=?", (id_,))["c"]
    n_ch = _one(conn, "SELECT COUNT(*) c FROM classes WHERE classe_precedente_id=?", (id_,))["c"]
    if (n_ex or n_ch) and not reassign_to:
        raise ApiError(409, "REFERENCED", "Classe référencée", count=n_ex + n_ch)
    with tx(conn):
        if n_ex or n_ch:
            if reassign_to == id_:
                raise ApiError(422, "BAD_REASSIGN", "Cible identique")
            _need(conn, "classes", reassign_to, "BAD_REASSIGN")
            conn.execute("INSERT OR IGNORE INTO exercice_classe(exercice_id, classe_id) "
                         "SELECT exercice_id, ? FROM exercice_classe WHERE classe_id=?", (reassign_to, id_))
            conn.execute("DELETE FROM exercice_classe WHERE classe_id=?", (id_,))
            # Classes dépendantes → cible ; si la cible est elle-même une enfant de la classe supprimée,
            # elle est raccordée à l'ancêtre de la classe supprimée (évite un auto-cycle).
            grand = _one(conn, "SELECT classe_precedente_id p FROM classes WHERE id=?", (id_,))["p"]
            conn.execute("UPDATE classes SET classe_precedente_id=? WHERE classe_precedente_id=? AND id<>?",
                         (reassign_to, id_, reassign_to))
            conn.execute("UPDATE classes SET classe_precedente_id=? WHERE id=? AND classe_precedente_id=?",
                         (grand, reassign_to, id_))
            _check_cycle(_prev_map(conn, drop=id_))
        conn.execute("DELETE FROM classes WHERE id=?", (id_,))


# ───────────────────────── Spécialités ─────────────────────────
def list_specialites(conn):
    return [dict(r) | {"nbExercices": _one(conn, "SELECT COUNT(*) c FROM exercice_specialite WHERE specialite_id=?",
                                           (r["id"],))["c"]}
            for r in conn.execute("SELECT id, nom FROM specialites ORDER BY nom")]


def create_specialite(conn, nom):
    id_ = new_id()
    try:
        with tx(conn):
            conn.execute("INSERT INTO specialites(id,nom) VALUES(?,?)", (id_, nom))
    except sqlite3.IntegrityError as e:
        raise _dup(e)
    return {"id": id_, "nom": nom}


def rename_specialite(conn, id_, nom):
    _need(conn, "specialites", id_, "NOT_FOUND")
    try:
        with tx(conn):
            conn.execute("UPDATE specialites SET nom=? WHERE id=?", (nom, id_))
    except sqlite3.IntegrityError as e:
        raise _dup(e)
    return {"id": id_, "nom": nom}


def delete_specialite(conn, id_, reassign_to=None):
    _need(conn, "specialites", id_, "NOT_FOUND")
    n = _one(conn, "SELECT COUNT(*) c FROM exercice_specialite WHERE specialite_id=?", (id_,))["c"]
    if n and not reassign_to:
        raise ApiError(409, "REFERENCED", "Spécialité référencée", count=n)
    with tx(conn):
        if n:
            if reassign_to == id_:
                raise ApiError(422, "BAD_REASSIGN", "Cible identique")
            _need(conn, "specialites", reassign_to, "BAD_REASSIGN")
            conn.execute("INSERT OR IGNORE INTO exercice_specialite(exercice_id, specialite_id) "
                         "SELECT exercice_id, ? FROM exercice_specialite WHERE specialite_id=?", (reassign_to, id_))
            conn.execute("DELETE FROM exercice_specialite WHERE specialite_id=?", (id_,))
        conn.execute("DELETE FROM specialites WHERE id=?", (id_,))


# ───────────────────────── Exercices ─────────────────────────
def _validate_exercice(conn, d: ExerciceIn):
    for a in d.affectations:
        _need(conn, "matieres", a.matiereId, "UNKNOWN_MATIERE")
        if _one(conn, "SELECT 1 FROM parties WHERE id=? AND matiere_id=?", (a.partieId, a.matiereId)) is None:
            raise ApiError(422, "BAD_PARTIE", "La partie n'appartient pas à la matière indiquée")
    for c in d.classeIds:
        _need(conn, "classes", c, "UNKNOWN_CLASSE")
    for s in d.specialiteIds:
        if s != AUCUNE:
            _need(conn, "specialites", s, "UNKNOWN_SPECIALITE")


def _write_relations(conn, id_, d: ExerciceIn):
    for t in ("exercice_partie", "exercice_classe", "exercice_specialite"):
        conn.execute(f"DELETE FROM {t} WHERE exercice_id=?", (id_,))
    conn.executemany("INSERT INTO exercice_partie VALUES(?,?,?)", [(id_, a.matiereId, a.partieId) for a in d.affectations])
    conn.executemany("INSERT INTO exercice_classe VALUES(?,?)", [(id_, c) for c in dict.fromkeys(d.classeIds)])
    conn.executemany("INSERT INTO exercice_specialite VALUES(?,?)", [(id_, s) for s in dict.fromkeys(d.specialiteIds)])


def create_exercice(conn, d: ExerciceIn):
    _validate_exercice(conn, d)
    id_ = new_id()
    with tx(conn):
        conn.execute("INSERT INTO exercices(id,sujet,corrige,session,niveau,tag_examen,updated_at) VALUES(?,?,?,?,?,?,?)",
                     (id_, d.sujet, d.corrige, d.session, d.niveauIntrinseque, int(d.tagExamen), now_iso()))
        _write_relations(conn, id_, d)
    return get_exercice(conn, id_)


def update_exercice(conn, id_, d: ExerciceIn):
    _need(conn, "exercices", id_, "NOT_FOUND")
    _validate_exercice(conn, d)
    with tx(conn):
        conn.execute("UPDATE exercices SET sujet=?,corrige=?,session=?,niveau=?,tag_examen=?,updated_at=? WHERE id=?",
                     (d.sujet, d.corrige, d.session, d.niveauIntrinseque, int(d.tagExamen), now_iso(), id_))
        _write_relations(conn, id_, d)
    return get_exercice(conn, id_)


def delete_exercice(conn, id_):
    _need(conn, "exercices", id_, "NOT_FOUND")
    with tx(conn):
        conn.execute("DELETE FROM exercices WHERE id=?", (id_,))


def _hydrate(conn, rows):
    ids = [r["id"] for r in rows]
    if not ids:
        return []
    ph = ",".join("?" * len(ids))
    aff, cl, sp = {}, {}, {}
    for r in conn.execute(f"SELECT * FROM exercice_partie WHERE exercice_id IN ({ph})", ids):
        aff.setdefault(r["exercice_id"], []).append({"matiereId": r["matiere_id"], "partieId": r["partie_id"]})
    for r in conn.execute(f"SELECT * FROM exercice_classe WHERE exercice_id IN ({ph})", ids):
        cl.setdefault(r["exercice_id"], []).append(r["classe_id"])
    for r in conn.execute(f"SELECT * FROM exercice_specialite WHERE exercice_id IN ({ph})", ids):
        sp.setdefault(r["exercice_id"], []).append(r["specialite_id"])
    return [{"id": r["id"], "sujet": r["sujet"], "corrige": r["corrige"],
             "affectations": sorted(aff.get(r["id"], []), key=lambda a: a["matiereId"]),
             "classeIds": sorted(cl.get(r["id"], [])), "specialiteIds": sorted(sp.get(r["id"], [])),
             "session": r["session"], "niveauIntrinseque": r["niveau"], "tagExamen": bool(r["tag_examen"])}
            for r in rows]


def get_exercice(conn, id_):
    row = _need(conn, "exercices", id_, "NOT_FOUND")
    return _hydrate(conn, [row])[0]


def list_exercices(conn, q=None, matiere_id=None, partie_id=None, classe_id=None, session=None,
                   limit=100, offset=0):
    where, args = [], []
    if q:
        where.append("(e.sujet LIKE ? OR e.corrige LIKE ?)")
        args += [f"%{q}%"] * 2
    if matiere_id:
        where.append("EXISTS(SELECT 1 FROM exercice_partie x WHERE x.exercice_id=e.id AND x.matiere_id=?)")
        args.append(matiere_id)
    if partie_id:
        where.append("EXISTS(SELECT 1 FROM exercice_partie x WHERE x.exercice_id=e.id AND x.partie_id=?)")
        args.append(partie_id)
    if classe_id:
        where.append("EXISTS(SELECT 1 FROM exercice_classe x WHERE x.exercice_id=e.id AND x.classe_id=?)")
        args.append(classe_id)
    if session == "vide":
        where.append("e.session IS NULL")
    elif session:
        where.append("e.session=?")
        args.append(int(session))
    w = (" WHERE " + " AND ".join(where)) if where else ""
    total = _one(conn, f"SELECT COUNT(*) c FROM exercices e{w}", args)["c"]
    rows = conn.execute(f"SELECT e.* FROM exercices e{w} ORDER BY e.updated_at DESC LIMIT ? OFFSET ?",
                        [*args, min(limit, 500), offset]).fetchall()
    return {"total": total, "items": _hydrate(conn, rows)}


# ───────────────────────── Réglages / Journal ─────────────────────────
def get_reglages(conn):
    r = _one(conn, "SELECT valeur FROM reglages WHERE cle='retentionJours'")
    return {"retentionJours": int(r["valeur"]) if r and r["valeur"] is not None else None}


def set_reglages(conn, retention):
    with tx(conn):
        conn.execute("INSERT INTO reglages(cle,valeur) VALUES('retentionJours',?) "
                     "ON CONFLICT(cle) DO UPDATE SET valeur=excluded.valeur",
                     (None if retention is None else str(retention),))
    return get_reglages(conn)


def add_journal(conn, user_id, generation_id, type_, params, details):
    """À appeler dans une transaction ouverte ou seul (autocommit)."""
    conn.execute("INSERT INTO journal(ts,user_id,generation_id,type,params,details) VALUES(?,?,?,?,?,?)",
                 (now_iso(), user_id, generation_id, type_, json.dumps(params, ensure_ascii=False),
                  json.dumps(details, ensure_ascii=False)))


def list_journal(conn, type_=None, limit=100, offset=0):
    where, args = ("WHERE type=?", [type_]) if type_ else ("", [])
    total = _one(conn, f"SELECT COUNT(*) c FROM journal {where}", args)["c"]
    rows = conn.execute(f"SELECT * FROM journal {where} ORDER BY id DESC LIMIT ? OFFSET ?",
                        [*args, min(limit, 500), offset]).fetchall()
    return {"total": total, "items": [
        {"id": r["id"], "timestamp": r["ts"], "userId": r["user_id"], "generationId": r["generation_id"],
         "type": r["type"], "params": json.loads(r["params"]), "details": json.loads(r["details"])}
        for r in rows]}
