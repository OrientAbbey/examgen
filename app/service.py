"""Orchestration de la génération : chargement de la banque, tirage, historique, journal, purge."""
import json
import random
import uuid
from datetime import datetime, timedelta, timezone

from . import generator as gen
from . import repo
from .classes_tree import ancestors
from .db import tx
from .errors import ApiError
from .models import GenerateIn

SESSION_LABELS = {"EXAMEN": "Examen", "EXAMEN_BLANC": "Examen blanc"}


def _load_bank(conn, matiere_id):
    cl, sp = {}, {}
    for r in conn.execute("SELECT exercice_id, classe_id FROM exercice_classe WHERE exercice_id IN "
                          "(SELECT exercice_id FROM exercice_partie WHERE matiere_id=?)", (matiere_id,)):
        cl.setdefault(r["exercice_id"], []).append(r["classe_id"])
    for r in conn.execute("SELECT exercice_id, specialite_id FROM exercice_specialite WHERE exercice_id IN "
                          "(SELECT exercice_id FROM exercice_partie WHERE matiere_id=?)", (matiere_id,)):
        sp.setdefault(r["exercice_id"], []).append(r["specialite_id"])
    rows = [{"id": r["id"], "partie_id": r["partie_id"], "session": r["session"], "niveau": r["niveau"],
             "tag": bool(r["tag_examen"]), "classe_ids": cl.get(r["id"], []), "specialite_ids": sp.get(r["id"], [])}
            for r in conn.execute("SELECT e.id, e.session, e.niveau, e.tag_examen, ep.partie_id FROM exercices e "
                                  "JOIN exercice_partie ep ON ep.exercice_id=e.id WHERE ep.matiere_id=?", (matiere_id,))]
    return gen.bank_frame(rows)


def generate_exam(conn, user_id: str, data: GenerateIn, rng=None) -> dict:
    matiere = conn.execute("SELECT * FROM matieres WHERE id=?", (data.matiereId,)).fetchone()
    classe = conn.execute("SELECT * FROM classes WHERE id=?", (data.classeId,)).fetchone()
    if matiere is None or classe is None:
        raise ApiError(422, "UNKNOWN_PARAM", "Matière ou classe inconnue")
    specialite = None
    if data.specialiteId:
        specialite = conn.execute("SELECT * FROM specialites WHERE id=?", (data.specialiteId,)).fetchone()
        if specialite is None:
            raise ApiError(422, "UNKNOWN_PARAM", "Spécialité inconnue")
    if classe["specialite_obligatoire"] and specialite is None:
        raise ApiError(422, "SPECIALITE_REQUISE", "Spécialité obligatoire pour cette classe")
    try:
        seq, exam_mode = gen.parse_session(data.session)
    except ValueError:
        raise ApiError(422, "BAD_SESSION", "Séquence/session invalide")

    prev = {r["id"]: r["classe_precedente_id"] for r in conn.execute("SELECT id, classe_precedente_id FROM classes")}
    demande = gen.Demande(difficulte=data.difficulte, seq=seq, exam_mode=exam_mode,
                          specialite_id=data.specialiteId, a_examen=bool(classe["a_examen"]))
    depths = gen.rank_depths(classe["id"], ancestors(prev, classe["id"]), demande.a_examen, data.difficulte)
    cands = gen.build_candidates(_load_bank(conn, matiere["id"]), depths, demande)
    history = {r["cle"] for r in conn.execute("SELECT cle FROM generations WHERE user_id=?", (user_id,))}
    result = gen.generate(cands, demande, history, rng)
    out = result.outcome

    # Ordre d'affichage : ordre des parties, puis ordre de tirage (même ordre pour sujet et corrigé, 4.j).
    parties = {r["id"]: (r["ordre"], r["nom"]) for r in
               conn.execute("SELECT id, ordre, nom FROM parties WHERE matiere_id=?", (matiere["id"],))}
    pmap = {c.id: c.partie_id for c in cands}
    ordered = sorted(enumerate(out.ids), key=lambda t: (parties[pmap[t[1]]][0], t[0]))
    contenu = []
    for _, eid in ordered:
        ex = conn.execute("SELECT sujet, corrige FROM exercices WHERE id=?", (eid,)).fetchone()
        contenu.append({"id": eid, "partie": parties[pmap[eid]][1], "sujet": ex["sujet"], "corrige": ex["corrige"]})

    gid = str(uuid.uuid4())
    sess_label = (f"Séquence {seq}" if seq else SESSION_LABELS.get(data.session, "Sans séquence"))
    params = {"matiere": matiere["nom"], "classe": classe["nom"],
              "specialite": specialite["nom"] if specialite else None,
              "sequence": sess_label, "difficulte": data.difficulte}
    with tx(conn):
        conn.execute("INSERT INTO generations(id,user_id,created_at,cle,params,contenu) VALUES(?,?,?,?,?,?)",
                     (gid, user_id, repo.now_iso(), gen.make_key(out.ids),
                      json.dumps(params, ensure_ascii=False), json.dumps(contenu, ensure_ascii=False)))
        repo.add_journal(conn, user_id, gid, "GENERATION", params,
                         {"nDemande": out.n_demande, "nObtenu": len(out.ids), "exerciceIds": [c["id"] for c in contenu],
                          "tentatives": result.tentatives, "parties": out.parties_p})
        if out.relax:
            repo.add_journal(conn, user_id, gid, "RULE_50_RELAXED", params, out.relax)
        if result.saturee:
            repo.add_journal(conn, user_id, gid, "UNIQUENESS_SATURATED", params, {"tentatives": result.tentatives})
        if out.incomplete:
            repo.add_journal(conn, user_id, gid, "INCOMPLETE_EXAM", params,
                             {"nDemande": out.n_demande, "nObtenu": len(out.ids), "phase": out.stopped_at})
    return {"id": gid, "params": params, "contenu": contenu}


def get_generation(conn, gid):
    r = conn.execute("SELECT * FROM generations WHERE id=?", (gid,)).fetchone()
    if r is None:
        return None
    return {"id": r["id"], "params": json.loads(r["params"]), "contenu": json.loads(r["contenu"])}


def purge_history(conn, now=None) -> int:
    """7.3 : purge par ancienneté, jamais la dernière génération d'un utilisateur. Journalisée."""
    days = repo.get_reglages(conn)["retentionJours"]
    if days is None:
        return 0
    cutoff = ((now or datetime.now(timezone.utc)) - timedelta(days=days)).isoformat(timespec="microseconds")
    with tx(conn):
        n = conn.execute(
            """DELETE FROM generations WHERE created_at < ? AND rowid NOT IN (
                 SELECT rowid FROM (SELECT rowid, ROW_NUMBER() OVER (
                   PARTITION BY user_id ORDER BY created_at DESC, rowid DESC) rn FROM generations) WHERE rn=1)""",
            (cutoff,)).rowcount
        if n:
            repo.add_journal(conn, "system", None, "INFO_HISTORY_PURGED", {"retentionJours": days}, {"supprimes": n})
    return n
