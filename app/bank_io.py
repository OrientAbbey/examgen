"""Import / export JSON de la banque (cahier 7.2, schéma 1.1)."""
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from jsonschema import Draft7Validator

from . import repo
from .classes_tree import CycleError, assert_acyclic
from .db import tx
from .errors import ApiError
from .models import AUCUNE

SCHEMA = json.loads((Path(__file__).parent / "schema" / "bank.schema.json").read_text(encoding="utf-8"))
_validator = Draft7Validator(SCHEMA)


def export_bank(conn) -> dict:
    items, off = [], 0
    while True:
        page = repo.list_exercices(conn, limit=500, offset=off)["items"]
        if not page:
            break
        items += page
        off += 500
    return {
        "schemaVersion": "1.1",
        "exportedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "matieres": [{"id": r["id"], "nom": r["nom"]} for r in conn.execute("SELECT id,nom FROM matieres ORDER BY nom")],
        "parties": [{"id": r["id"], "matiereId": r["matiere_id"], "nom": r["nom"], "ordre": r["ordre"]}
                    for r in conn.execute("SELECT * FROM parties ORDER BY matiere_id, ordre, nom")],
        "classes": [{"id": r["id"], "nom": r["nom"], "classePrecedenteId": r["classe_precedente_id"],
                     "aExamen": bool(r["a_examen"]), "specialiteObligatoire": bool(r["specialite_obligatoire"])}
                    for r in conn.execute("SELECT * FROM classes ORDER BY nom")],
        "specialites": [{"id": r["id"], "nom": r["nom"]} for r in conn.execute("SELECT id,nom FROM specialites ORDER BY nom")],
        "exercices": [{k: e[k] for k in ("id", "sujet", "corrige", "affectations", "classeIds", "specialiteIds",
                                         "session", "niveauIntrinseque", "tagExamen")} for e in items],
    }


def validate_bank(doc, existing_prev: dict | None = None) -> list:
    """Retourne la liste des erreurs (vide si valide). existing_prev : classes déjà en base (mode fusion)."""
    if not isinstance(doc, dict):
        return ["racine : un objet JSON est attendu"]
    errs = [f"{'/'.join(map(str, e.absolute_path)) or 'racine'} : {e.message}" for e in _validator.iter_errors(doc)]
    if errs:
        return errs[:50]
    mat = {m["id"] for m in doc["matieres"]}
    parties = {p["id"]: p["matiereId"] for p in doc["parties"]}
    cls = {c["id"] for c in doc["classes"]}
    spe = {s["id"] for s in doc["specialites"]}
    for name, items in (("matieres", doc["matieres"]), ("parties", doc["parties"]), ("classes", doc["classes"]),
                        ("specialites", doc["specialites"]), ("exercices", doc["exercices"])):
        ids = [i["id"] for i in items]
        if len(ids) != len(set(ids)):
            errs.append(f"{name} : identifiants dupliqués")
    for p in doc["parties"]:
        if p["matiereId"] not in mat:
            errs.append(f"partie {p['id']} : matiereId inconnu")
    prev = dict(existing_prev or {})
    for c in doc["classes"]:
        pid = c.get("classePrecedenteId")
        if pid is not None and pid not in cls:
            errs.append(f"classe {c['id']} : classePrecedenteId inconnu dans le fichier")
        prev[c["id"]] = pid
    try:
        assert_acyclic(prev)
    except CycleError:
        errs.append("classes : cycle détecté dans les classes précédentes")
    for e in doc["exercices"]:
        i = e["id"]
        if e.get("tagExamen") and e["session"] is None:
            errs.append(f"exercice {i} : tagExamen doit être false si session est null")
        ms = [a["matiereId"] for a in e["affectations"]]
        if len(ms) != len(set(ms)):
            errs.append(f"exercice {i} : plusieurs parties pour une même matière")
        for a in e["affectations"]:
            if a["matiereId"] not in mat:
                errs.append(f"exercice {i} : matiereId inconnu")
            if parties.get(a["partieId"]) != a["matiereId"]:
                errs.append(f"exercice {i} : partie {a['partieId']} absente ou hors de la matière indiquée")
        for c in e["classeIds"]:
            if c not in cls:
                errs.append(f"exercice {i} : classeId inconnu {c}")
        for s in e["specialiteIds"]:
            if s != AUCUNE and s not in spe:
                errs.append(f"exercice {i} : specialiteId inconnu {s}")
    return errs[:50]


def import_bank(conn, doc, mode: str) -> dict:
    if mode not in ("remplacer", "fusionner"):
        raise ApiError(422, "BAD_MODE", "mode ∈ {remplacer, fusionner}")
    existing = {} if mode == "remplacer" else {
        r["id"]: r["classe_precedente_id"] for r in conn.execute("SELECT id, classe_precedente_id FROM classes")}
    errs = validate_bank(doc, existing)
    if errs:
        raise ApiError(422, "INVALID_IMPORT", "Fichier invalide", errors=errs)
    now = repo.now_iso()
    try:
        with tx(conn):
            conn.execute("PRAGMA defer_foreign_keys=ON")
            if mode == "remplacer":
                for t in ("exercice_partie", "exercice_classe", "exercice_specialite", "exercices",
                          "parties", "classes", "specialites", "matieres"):
                    conn.execute(f"DELETE FROM {t}")
            for m in doc["matieres"]:
                conn.execute("INSERT INTO matieres(id,nom) VALUES(?,?) ON CONFLICT(id) DO UPDATE SET nom=excluded.nom",
                             (m["id"], m["nom"]))
            for s in doc["specialites"]:
                conn.execute("INSERT INTO specialites(id,nom) VALUES(?,?) ON CONFLICT(id) DO UPDATE SET nom=excluded.nom",
                             (s["id"], s["nom"]))
            for c in doc["classes"]:
                conn.execute(
                    "INSERT INTO classes(id,nom,classe_precedente_id,a_examen,specialite_obligatoire) VALUES(?,?,?,?,?) "
                    "ON CONFLICT(id) DO UPDATE SET nom=excluded.nom, classe_precedente_id=excluded.classe_precedente_id, "
                    "a_examen=excluded.a_examen, specialite_obligatoire=excluded.specialite_obligatoire",
                    (c["id"], c["nom"], c.get("classePrecedenteId"), int(c.get("aExamen", False)),
                     int(c.get("specialiteObligatoire", False))))
            for p in doc["parties"]:
                conn.execute("INSERT INTO parties(id,matiere_id,nom,ordre) VALUES(?,?,?,?) "
                             "ON CONFLICT(id) DO UPDATE SET matiere_id=excluded.matiere_id, nom=excluded.nom, ordre=excluded.ordre",
                             (p["id"], p["matiereId"], p["nom"], p.get("ordre", 0)))
            for e in doc["exercices"]:
                conn.execute(
                    "INSERT INTO exercices(id,sujet,corrige,session,niveau,tag_examen,updated_at) VALUES(?,?,?,?,?,?,?) "
                    "ON CONFLICT(id) DO UPDATE SET sujet=excluded.sujet, corrige=excluded.corrige, session=excluded.session, "
                    "niveau=excluded.niveau, tag_examen=excluded.tag_examen, updated_at=excluded.updated_at",
                    (e["id"], e["sujet"], e["corrige"], e["session"], e["niveauIntrinseque"],
                     int(e.get("tagExamen", False)), now))
                for t in ("exercice_partie", "exercice_classe", "exercice_specialite"):
                    conn.execute(f"DELETE FROM {t} WHERE exercice_id=?", (e["id"],))
                conn.executemany("INSERT INTO exercice_partie VALUES(?,?,?)",
                                 [(e["id"], a["matiereId"], a["partieId"]) for a in e["affectations"]])
                conn.executemany("INSERT INTO exercice_classe VALUES(?,?)",
                                 [(e["id"], c) for c in dict.fromkeys(e["classeIds"])])
                conn.executemany("INSERT INTO exercice_specialite VALUES(?,?)",
                                 [(e["id"], s) for s in dict.fromkeys(e["specialiteIds"])])
    except sqlite3.IntegrityError as ex:
        raise ApiError(422, "INVALID_IMPORT", "Conflit d'intégrité à l'import (ex. nom déjà utilisé)", errors=[str(ex)])
    return {k: len(doc[k]) for k in ("matieres", "parties", "classes", "specialites", "exercices")}
