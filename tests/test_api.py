import json
import sqlite3

from .conftest import H, post


def gen(w, **kw):
    body = {"matiereId": w["m"]["id"], "classeId": w["ter"]["id"], "specialiteId": w["sp"]["id"],
            "session": "3", "difficulte": "Moyen", **kw}
    return w["c"].post("/api/generate", json=body)


def test_admin_protege(env):
    c, _ = env
    assert c.get("/api/admin/matieres").status_code == 401
    assert c.get("/api/admin/matieres", headers={"X-Admin-Token": "mauvais"}).status_code == 401


def test_generation_epreuve_corrige_meme_numerotation(world):
    r = gen(world)
    assert r.status_code == 200
    j = r.json()
    assert set(j) == {"id", "exercices", "urls"}          # silence : aucune info sur l'état de l'épreuve
    assert [e["numero"] for e in j["exercices"]] == [1, 2, 3, 4]
    c = world["c"]
    sujet, corr = c.get(j["urls"]["epreuve"]), c.get(j["urls"]["corrige"])
    assert sujet.status_code == corr.status_code == 200
    assert sujet.text.count('class="exo"') == corr.text.count('class="exo"') == 4
    for i in range(60):   # sujet n'expose jamais un corrigé
        assert f"Corrigé {i}<" not in sujet.text
    assert "print.js" in c.get(j["urls"]["imprimer"]).text
    assert c.get("/epreuve/inconnu").status_code == 404


def test_specialite_obligatoire_et_params_invalides(world):
    r = gen(world, specialiteId=None)
    assert r.status_code == 422 and r.json()["code"] == "SPECIALITE_REQUISE"
    assert gen(world, session="9").status_code == 422
    assert gen(world, classeId="x").status_code == 422


def test_unicite_par_utilisateur(world):
    seen = set()
    for _ in range(8):
        j = gen(world, session="", difficulte="Facile").json()
        key = tuple(sorted(e["sujetHtml"] for e in j["exercices"]))
        assert key not in seen
        seen.add(key)


def test_saturation_silencieuse_et_journal(env):
    c, _ = env
    m = post(c, "/matieres", {"nom": "Mini"})
    p = post(c, "/parties", {"matiereId": m["id"], "nom": "Seule"})
    cl = post(c, "/classes", {"nom": "Solo"})
    for i in range(2):
        post(c, "/exercices", {"sujet": f"s{i}", "corrige": f"c{i}", "affectations": [{"matiereId": m["id"], "partieId": p["id"]}],
                               "classeIds": [cl["id"]], "specialiteIds": ["SPECIAL:Aucune"], "session": 1,
                               "niveauIntrinseque": "Facile"})
    for _ in range(3):   # une seule combinaison possible, et incomplète (2 < N=6)
        r = c.post("/api/generate", json={"matiereId": m["id"], "classeId": cl["id"], "session": "1",
                                          "difficulte": "Difficile"})
        assert r.status_code == 200 and len(r.json()["exercices"]) == 2   # jamais d'erreur bloquante
    j = c.get("/api/admin/journal", headers=H).json()["items"]
    types = [e["type"] for e in j]
    assert types.count("GENERATION") == 3 and types.count("INCOMPLETE_EXAM") == 3
    assert types.count("UNIQUENESS_SATURATED") == 2      # 2e et 3e : doublon inévitable, non signalé
    assert "RULE_50_RELAXED" in types


def test_cycle_classes_refuse(world):
    c, sec, ter = world["c"], world["sec"], world["ter"]
    r = c.put(f"/api/admin/classes/{sec['id']}", headers=H,
              json={"nom": "Seconde", "classePrecedenteId": ter["id"]})
    assert r.status_code == 422 and r.json()["code"] == "CYCLE"
    r = c.put(f"/api/admin/classes/{sec['id']}", headers=H, json={"nom": "Seconde", "classePrecedenteId": sec["id"]})
    assert r.status_code == 422


def test_arborescence(world):
    cl = {x["nom"]: x for x in world["c"].get("/api/admin/classes", headers=H).json()}
    assert cl["Terminale"]["arborescence"] == ["Première", "Seconde"]


def test_integrite_suppression_bloquee_puis_reaffectation(world):
    c = world["c"]
    p0, p1 = world["parts"][0], world["parts"][1]
    r = c.delete(f"/api/admin/parties/{p0['id']}", headers=H)
    assert r.status_code == 409 and r.json()["code"] == "REFERENCED" and r.json()["count"] >= 1
    assert c.delete(f"/api/admin/parties/{p0['id']}?reassignTo={p1['id']}", headers=H).status_code == 204
    assert all(p["id"] != p0["id"] for p in c.get("/api/admin/parties", headers=H).json())
    # classe : bloquée, puis réaffectation (exercices + classes dépendantes)
    sec, pre = world["sec"], world["pre"]
    assert c.delete(f"/api/admin/classes/{sec['id']}", headers=H).status_code == 409
    assert c.delete(f"/api/admin/classes/{sec['id']}?reassignTo={pre['id']}", headers=H).status_code == 204
    cl = {x["nom"]: x for x in c.get("/api/admin/classes", headers=H).json()}
    assert cl["Première"]["classePrecedenteId"] is None   # raccordée à l'ancêtre de Seconde (aucun)
    assert cl["Terminale"]["arborescence"] == ["Première"]


def test_derniere_partie_bloquee(env):
    c, _ = env
    m = post(c, "/matieres", {"nom": "Chimie"})
    p = post(c, "/parties", {"matiereId": m["id"], "nom": "Seule"})
    cl = post(c, "/classes", {"nom": "C"})
    post(c, "/exercices", {"sujet": "s", "corrige": "c", "affectations": [{"matiereId": m["id"], "partieId": p["id"]}],
                           "classeIds": [cl["id"]], "specialiteIds": ["SPECIAL:Aucune"], "session": None,
                           "niveauIntrinseque": "Facile"})
    assert c.delete(f"/api/admin/parties/{p['id']}", headers=H).status_code == 409
    assert c.delete(f"/api/admin/parties/{p['id']}?reassignTo={p['id']}", headers=H).status_code == 422
    assert c.delete(f"/api/admin/matieres/{m['id']}", headers=H).status_code == 409


def test_matiere_reaffectation(env):
    c, _ = env
    a, b = post(c, "/matieres", {"nom": "A"}), post(c, "/matieres", {"nom": "B"})
    pa, pb = (post(c, "/parties", {"matiereId": x["id"], "nom": "P"}) for x in (a, b))
    cl = post(c, "/classes", {"nom": "C"})
    ex = post(c, "/exercices", {"sujet": "s", "corrige": "c", "affectations": [{"matiereId": a["id"], "partieId": pa["id"]}],
                                "classeIds": [cl["id"]], "specialiteIds": ["SPECIAL:Aucune"], "session": 1,
                                "niveauIntrinseque": "Facile"})
    r = c.delete(f"/api/admin/matieres/{a['id']}?reassignTo={b['id']}&reassignPartieId={pb['id']}", headers=H)
    assert r.status_code == 204
    assert c.get(f"/api/admin/exercices/{ex['id']}", headers=H).json()["affectations"] == [
        {"matiereId": b["id"], "partieId": pb["id"]}]


def test_validation_exercice(world):
    c, w = world["c"], world
    base = {"sujet": "s", "corrige": "c", "affectations": [{"matiereId": w["m"]["id"], "partieId": w["parts"][0]["id"]}],
            "classeIds": [w["ter"]["id"]], "specialiteIds": ["SPECIAL:Aucune"], "session": None,
            "niveauIntrinseque": "Facile"}
    assert c.post("/api/admin/exercices", headers=H, json={**base, "tagExamen": True}).status_code == 422
    assert c.post("/api/admin/exercices", headers=H, json={**base, "corrige": ""}).status_code == 422
    assert c.post("/api/admin/exercices", headers=H, json={**base, "specialiteIds": ["inconnu"]}).status_code == 404
    bad = {**base, "affectations": [{"matiereId": w["m"]["id"], "partieId": "nope"}]}
    assert c.post("/api/admin/exercices", headers=H, json=bad).status_code == 422


def test_export_import_roundtrip_et_modes(world, tmp_path):
    c = world["c"]
    doc = c.get("/api/admin/export", headers=H).json()
    assert doc["schemaVersion"] == "1.2" and len(doc["exercices"]) == 90
    # réimport tel quel (fusion) : idempotent
    r = c.post("/api/admin/import?mode=fusionner", json=doc, headers=H)
    assert r.status_code == 200 and r.json()["exercices"] == 90
    assert c.get("/api/admin/exercices?limit=1", headers=H).json()["total"] == 90
    # remplacer dans une base neuve
    from fastapi.testclient import TestClient
    from app.main import create_app
    c2 = TestClient(create_app(str(tmp_path / "autre.db"), "tok"))
    assert c2.post("/api/admin/import?mode=remplacer", json=doc, headers=H).status_code == 200
    assert c2.get("/api/admin/export", headers=H).json()["exercices"] == doc["exercices"]
    # génération possible après import
    r = c2.post("/api/generate", json={"matiereId": world["m"]["id"], "classeId": world["ter"]["id"],
                                       "specialiteId": world["sp"]["id"], "difficulte": "Facile"})
    assert r.status_code == 200


def test_import_invalide_atomique(world):
    c = world["c"]
    doc = c.get("/api/admin/export", headers=H).json()
    cases = []
    d1 = json.loads(json.dumps(doc)); d1["exercices"][0]["tagExamen"] = True; d1["exercices"][0]["session"] = None
    d2 = json.loads(json.dumps(doc)); d2["exercices"][1]["classeIds"] = ["fantome"]
    d3 = json.loads(json.dumps(doc)); d3["classes"][0]["classePrecedenteId"] = d3["classes"][0]["id"]
    d4 = json.loads(json.dumps(doc)); d4["schemaVersion"] = "1.0"
    d5 = json.loads(json.dumps(doc)); d5["exercices"][2]["specialiteIds"] = ["fantome"]
    for d in (d1, d2, d3, d4, d5):
        r = c.post("/api/admin/import?mode=remplacer", json=d, headers=H)
        assert r.status_code == 422 and r.json()["code"] == "INVALID_IMPORT" and r.json()["errors"]
    assert c.get("/api/admin/exercices?limit=1", headers=H).json()["total"] == 90   # base intacte


def test_purge_conserve_derniere_generation(world):
    c, path = world["c"], world["path"]
    for _ in range(3):
        gen(world, session="", difficulte="Facile")
    con = sqlite3.connect(path)
    con.execute("UPDATE generations SET created_at='2000-01-01T00:00:00.000000+00:00'")
    con.execute("UPDATE generations SET created_at='2000-01-02T00:00:00.000000+00:00' WHERE rowid=3")
    con.commit(); con.close()
    assert c.post("/api/admin/purge", headers=H).json() == {"supprimes": 0}   # illimité par défaut
    assert c.put("/api/admin/reglages", json={"retentionJours": 30}, headers=H).json() == {"retentionJours": 30}
    assert c.post("/api/admin/purge", headers=H).json() == {"supprimes": 2}
    con = sqlite3.connect(path)
    assert con.execute("SELECT COUNT(*) FROM generations").fetchone()[0] == 1
    con.close()
    j = c.get("/api/admin/journal?type=INFO_HISTORY_PURGED", headers=H).json()
    assert j["items"][0]["details"] == {"supprimes": 2}


def test_pages_statiques_et_en_tetes(env):
    c, _ = env
    r = c.get("/")
    assert r.status_code == 200 and "default-src 'self'" in r.headers["content-security-policy"]
    assert c.get("/admin").status_code == 200
    assert "uid" in c.cookies


def test_markdown_sans_html_brut(world):
    c, w = world["c"], world
    post(c, "/exercices", {"sujet": "<script>alert(1)</script> **gras**", "corrige": "ok",
                           "affectations": [{"matiereId": w["m"]["id"], "partieId": w["parts"][0]["id"]}],
                           "classeIds": [w["ter"]["id"]], "specialiteIds": ["SPECIAL:Aucune"], "session": None,
                           "niveauIntrinseque": "Facile"})
    from app.render import md
    out = md("<script>alert(1)</script> **gras**")
    assert "<script>" not in out and "<strong>gras</strong>" in out
