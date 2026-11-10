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


# ───────────────────────── Assistant IA : contextes tirés de la base ─────────────────────────
def catalogue_public(conn) -> dict:
    return {"matieres": [{"id": r["id"], "nom": r["nom"]} for r in conn.execute("SELECT id, nom FROM matieres ORDER BY nom")],
            "classes": [{"id": r["id"], "nom": r["nom"], "specialiteObligatoire": bool(r["specialite_obligatoire"])} for r in conn.execute("SELECT * FROM classes ORDER BY nom")],
            "specialites": [{"id": r["id"], "nom": r["nom"]} for r in conn.execute("SELECT id, nom FROM specialites ORDER BY nom")]}


def contexte_generation(conn, d) -> dict:
    m = conn.execute("SELECT * FROM matieres WHERE id=?", (d.matiereId,)).fetchone()
    if m is None:
        raise ApiError(422, "UNKNOWN_PARAM", "Matière inconnue")
    partie = None
    if d.partieId:
        partie = conn.execute("SELECT * FROM parties WHERE id=? AND matiere_id=?", (d.partieId, m["id"])).fetchone()
        if partie is None:
            raise ApiError(422, "UNKNOWN_PARAM", "Partie inconnue pour cette matière")
    classes = []
    for cid in d.classeIds:
        r = conn.execute("SELECT nom FROM classes WHERE id=?", (cid,)).fetchone()
        if r is None:
            raise ApiError(422, "UNKNOWN_PARAM", "Classe inconnue")
        classes.append(r["nom"])
    spec = None
    if d.specialiteId and d.specialiteId != "SPECIAL:Aucune":
        r = conn.execute("SELECT nom FROM specialites WHERE id=?", (d.specialiteId,)).fetchone()
        spec = r["nom"] if r else None
    # exercice existant de la banque comme référence de style (même partie, de préférence même classe)
    ex = None
    for filtre, args in ((" AND ep.partie_id=?", [partie["id"]] if partie else None), ("", [])):
        if args is None:
            continue
        ex = conn.execute("SELECT e.sujet FROM exercices e JOIN exercice_partie ep ON ep.exercice_id=e.id WHERE ep.matiere_id=?" + filtre + " ORDER BY RANDOM() LIMIT 1",
                          [m["id"], *args]).fetchone()
        if ex:
            break
    return {"matiere": m["nom"], "partie": partie["nom"] if partie else None, "classes": classes, "specialite": spec, "session": d.session, "niveau": d.niveau,
            "consigne": d.consigne.strip(), "nbQuestions": d.nbQuestions, "exemple": ex["sujet"] if ex else None}


def catalogue_metadonnees(conn, matiere_id=None) -> dict:
    sql = "SELECT p.id, p.nom, m.nom AS matiere FROM parties p JOIN matieres m ON m.id=p.matiere_id" + (" WHERE m.id=?" if matiere_id else "") + " ORDER BY m.nom, p.ordre"
    return {"parties": [{"id": r["id"], "nom": r["nom"], "matiere": r["matiere"]} for r in conn.execute(sql, [matiere_id] if matiere_id else [])],
            "classes": [{"id": r["id"], "nom": r["nom"]} for r in conn.execute("SELECT id, nom FROM classes ORDER BY nom")]}


SEUIL_COUVERTURE = 3


def couverture(conn, matiere_id: str) -> dict:
    """Nombre d'exercices par classe × partie × séquence (+ session vide) ; les cases sous le seuil sont des lacunes à combler."""
    m = conn.execute("SELECT * FROM matieres WHERE id=?", (matiere_id,)).fetchone()
    if m is None:
        raise ApiError(404, "NOT_FOUND", "Matière introuvable")
    comptes = {}
    for r in conn.execute("""SELECT ec.classe_id, ep.partie_id, e.session, COUNT(*) n FROM exercices e
                             JOIN exercice_partie ep ON ep.exercice_id=e.id AND ep.matiere_id=?
                             JOIN exercice_classe ec ON ec.exercice_id=e.id GROUP BY ec.classe_id, ep.partie_id, e.session""", (matiere_id,)):
        comptes[(r["classe_id"], r["partie_id"], r["session"])] = r["n"]
    parties = list(conn.execute("SELECT id, nom FROM parties WHERE matiere_id=? ORDER BY ordre, nom", (matiere_id,)))
    out, lacunes = [], []
    for c in conn.execute("SELECT id, nom FROM classes ORDER BY nom"):
        lignes = []
        for p in parties:
            seqs = {str(s): comptes.get((c["id"], p["id"], s), 0) for s in range(1, 7)}
            lignes.append({"partieId": p["id"], "partie": p["nom"], "sequences": seqs, "vide": comptes.get((c["id"], p["id"], None), 0)})
            lacunes += [{"classeId": c["id"], "classe": c["nom"], "partieId": p["id"], "partie": p["nom"], "session": int(s), "n": n} for s, n in seqs.items() if n < SEUIL_COUVERTURE]
        out.append({"classeId": c["id"], "classe": c["nom"], "parties": lignes})
    return {"matiere": m["nom"], "seuil": SEUIL_COUVERTURE, "classes": out, "lacunes": lacunes[:300]}
