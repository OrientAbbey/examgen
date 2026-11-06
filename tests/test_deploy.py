import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import bank_io, db
from app.main import create_app

from .conftest import H, post

GEN = {"matiereId": "x", "classeId": "y", "difficulte": "Facile"}


def test_healthz(env):
    c, _ = env
    assert c.get("/healthz").json() == {"status": "ok"}


def test_production_exige_un_jeton(tmp_path, monkeypatch):
    monkeypatch.setenv("EXAMGEN_ENV", "production")
    monkeypatch.delenv("EXAMGEN_ADMIN_TOKEN", raising=False)
    with pytest.raises(RuntimeError):
        create_app(str(tmp_path / "p.db"))
    create_app(str(tmp_path / "p.db"), "secret")        # ok avec jeton


def test_bootstrap_restaure_une_base_vide_sans_ecraser(world, tmp_path, monkeypatch):
    doc = world["c"].get("/api/admin/export", headers=H).json()
    f = tmp_path / "banque.json"
    f.write_text(json.dumps(doc), encoding="utf-8")
    monkeypatch.setenv("EXAMGEN_BOOTSTRAP_FILE", str(f))
    path = str(tmp_path / "neuve.db")
    c = TestClient(create_app(path, "tok"))
    assert c.get("/api/admin/exercices?limit=1", headers=H).json()["total"] == 90
    c.delete("/api/admin/exercices/" + doc["exercices"][0]["id"], headers=H)
    c2 = TestClient(create_app(path, "tok"))             # redémarrage : base non vide → pas de ré-import
    assert c2.get("/api/admin/exercices?limit=1", headers=H).json()["total"] == 89


def test_bootstrap_fichier_invalide_ne_bloque_pas_le_demarrage(tmp_path, monkeypatch):
    f = tmp_path / "banque.json"
    f.write_text('{"schemaVersion": "0"}', encoding="utf-8")
    monkeypatch.setenv("EXAMGEN_BOOTSTRAP_FILE", str(f))
    c = TestClient(create_app(str(tmp_path / "b.db"), "tok"))
    assert c.get("/healthz").status_code == 200 and c.get("/api/meta").json()["matieres"] == []


def test_limite_de_debit_generation(tmp_path, monkeypatch):
    monkeypatch.setenv("EXAMGEN_GEN_PER_MIN", "3")
    c = TestClient(create_app(str(tmp_path / "r.db"), "tok"))
    codes = [c.post("/api/generate", json=GEN).status_code for _ in range(4)]
    assert codes == [422, 422, 422, 429]


def test_force_brute_jeton_admin(env):
    c, _ = env
    for _ in range(10):
        assert c.get("/api/admin/ping", headers={"X-Admin-Token": "faux"}).status_code == 401
    assert c.get("/api/admin/ping", headers=H).status_code == 429     # même le bon jeton : bloqué temporairement


def test_cookie_secure_et_hsts_en_https(tmp_path):
    c = TestClient(create_app(str(tmp_path / "h.db"), "tok"), base_url="https://exemple.test")
    r = c.get("/")
    assert "secure" in r.headers["set-cookie"].lower() and "max-age=31536000" in r.headers["strict-transport-security"]
    r = TestClient(create_app(str(tmp_path / "h2.db"), "tok")).get("/")
    assert "secure" not in r.headers["set-cookie"].lower() and "strict-transport-security" not in r.headers


def test_sauvegarde_quotidienne_rotation(world, tmp_path):
    conn = db.connect(world["path"])
    d = tmp_path / "bk"
    d.mkdir()
    for i in range(20):
        (d / f"banque-2020{i + 1:02d}01.json").write_text("{}")
    out = bank_io.backup_to_dir(conn, str(d), keep=5)
    files = sorted(p.name for p in d.glob("banque-*.json"))
    assert len(files) == 5 and Path(out).name in files
    assert json.loads(Path(out).read_text(encoding="utf-8"))["schemaVersion"] == "1.1"
    vide = db.connect(str(tmp_path / "vide.db")); db.init(vide)
    assert bank_io.backup_to_dir(vide, str(tmp_path / "bk2")) is None
