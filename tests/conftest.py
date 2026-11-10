import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from app.main import create_app

H = {"X-Admin-Token": "tok"}


@pytest.fixture(autouse=True)
def no_default_bootstrap(monkeypatch):
    """Keep isolated test databases empty unless a bootstrap file is under test."""
    monkeypatch.setenv("EXAMGEN_BOOTSTRAP_FILE", str(Path(__file__).with_name("__missing_bootstrap__.json")))


@pytest.fixture
def env(tmp_path):
    app = create_app(str(tmp_path / "t.db"), "tok")
    c = TestClient(app)
    return c, str(tmp_path / "t.db")


def post(c, path, body, ok=(200, 201)):
    r = c.post("/api/admin" + path, json=body, headers=H)
    assert r.status_code in ok, (path, r.status_code, r.text)
    return r.json()


def peupler(c):
    """Matière à 4 parties, classes Seconde←Première←Terminale (examen), 1 spécialité, 90 exercices (graine fixe)."""
    m = post(c, "/matieres", {"nom": "Maths"})
    parts = [post(c, "/parties", {"matiereId": m["id"], "nom": f"P{i}", "ordre": i}) for i in range(4)]
    sec = post(c, "/classes", {"nom": "Seconde"})
    pre = post(c, "/classes", {"nom": "Première", "classePrecedenteId": sec["id"]})
    ter = post(c, "/classes", {"nom": "Terminale", "classePrecedenteId": pre["id"], "aExamen": True, "specialiteObligatoire": True})
    sp = post(c, "/specialites", {"nom": "S"})
    import random
    R = random.Random(5)
    exos = []
    for i in range(90):
        classe = [ter, pre, sec][i % 3]
        exos.append(post(c, "/exercices", {
            "sujet": f"Sujet {i}", "corrige": f"Corrigé {i}",
            "affectations": [{"matiereId": m["id"], "partieId": parts[R.randrange(4)]["id"]}],
            "classeIds": [classe["id"]], "specialiteIds": ["SPECIAL:Aucune"],
            "session": R.randint(1, 6), "niveauIntrinseque": R.choice(["Facile", "Moyen", "Difficile"]),
            "tagExamen": R.random() < 0.3}))
    return dict(c=c, m=m, parts=parts, sec=sec, pre=pre, ter=ter, sp=sp, exos=exos)


@pytest.fixture
def world(env):
    c, path = env
    return {**peupler(c), "path": path}
