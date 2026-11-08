"""Structures chimiques (SMILES → développée / topologique / Cram), Lewis, images téléversées."""
import base64
import json
import re

import pytest

from app import chem, render

from .conftest import H, post

PNG = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==")
SVG_OK = b'<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg" width="40" height="40"><circle cx="20" cy="20" r="10" fill="none" stroke="black"/></svg>'


@pytest.mark.parametrize("smiles,brute", [("CCO", "C2H6O"), ("CC(O)C", "C3H8O"), ("CC(=O)O", "C2H4O2"), ("C[C@H](O)CC", "C4H10O"), ("N[C@@H](C)C(=O)O", "C3H7NO2"),
                                          ("c1ccccc1", "C6H6"), ("Oc1ccccc1", "C6H6O"), ("C1CCCCC1", "C6H12"), ("C=C", "C2H4"), ("CC(C)CC", "C5H12"), ("COC", "C2H6O")])
def test_formule_brute_exacte(smiles, brute):
    assert chem.formule_brute(smiles) == brute


def test_hydrogenes_explicites_et_comptage():
    assert chem.hydrogenes_explicites("CCO") == "C([H])([H])([H])C([H])([H])O([H])"
    for smi in ("CC(=O)O", "c1ccccc1", "C1CCCCC1", "CC(C)CC", "[NH4+]", "N[C@@H](C)C(=O)O"):
        dev = chem.hydrogenes_explicites(smi)
        _, atomes, _ = chem.parse(dev)
        assert sum(1 for a in atomes if a.sym == "H") == int(re.search(r"H(\d*)", chem.formule_brute(smi)).group(1) or 1)
        assert chem.formule_brute(dev) == chem.formule_brute(smi)          # la molécule est inchangée


def test_stereochimie_preservee_dans_l_ordre_des_voisins():
    # [C@H] : l'hydrogène implicite est le premier voisin après l'atome précédent → [C@]([H])(…) conserve la chiralité
    assert chem.hydrogenes_explicites("C[C@H](O)CC") == "C([H])([H])([H])[C@]([H])(O([H]))C([H])([H])C([H])([H])([H])"


@pytest.mark.parametrize("mauvais", ["", "C(C", "C1CC", "C)", "CXC", "C[N", "C" * 400])
def test_smiles_invalide_refuse(mauvais):
    with pytest.raises(ValueError):
        chem.valider(mauvais)


def test_bloc_mol_rendu_et_securise():
    h = render.md("```mol developpee grand\nCCO éthanol\nCC(=O)O <b>acide</b>\n```")
    assert h.count('class="mol"') == 2 and 'data-style="developpee"' in h and 'data-size="grand"' in h
    assert "<b>" not in h and "&lt;b&gt;acide&lt;/b&gt;" in h                    # légende échappée
    assert 'data-smiles="C([H])([H])([H])C([H])([H])O([H])"' in h
    assert "mol-error" in render.md("```mol\nC(C\n```")                          # erreur visible, pas d'exception
    assert 'class="language-python"' in render.md("```python\nx = 1\n```")      # les autres blocs de code sont inchangés


def test_images_seules_les_medias_locaux_sont_affiches():
    h = render.md("![ok](/media/3f2b8c1e-0000-4000-8000-000000000000) ![ext](http://evil.test/x.png) ![js](javascript:alert(1))")
    assert h.count("<img") == 1 and "evil.test" not in h
    assert 'src="javascript' not in h and 'href="javascript' not in h             # au pire du texte brut, jamais un lien actif


def test_televersement_affichage_et_isolation(env):
    c, _ = env
    assert c.post("/api/admin/media", content=PNG).status_code == 401
    r = c.post("/api/admin/media", content=PNG, headers={**H, "X-Filename": "newman%20%C3%A9thane.png"})
    assert r.status_code == 201
    m = r.json()
    assert m["mime"] == "image/png" and m["markdown"].startswith("![newman éthane](/media/")
    pub = c.get(m["url"])
    assert pub.status_code == 200 and pub.content == PNG and pub.headers["content-type"] == "image/png"
    assert "sandbox" in pub.headers["content-security-policy"] and pub.headers["x-content-type-options"] == "nosniff"
    assert c.get("/media/inconnu").status_code == 404 and c.get("/media/3f2b8c1e-0000-4000-8000-000000000000").status_code == 404
    assert c.post("/api/admin/media", content=SVG_OK, headers=H).json()["mime"] == "image/svg+xml"
    assert len(c.get("/api/admin/media", headers=H).json()) == 2


@pytest.mark.parametrize("contenu,code,statut", [
    (b"", "MEDIA_VIDE", 422), (b"<html><script>alert(1)</script></html>", "MEDIA_FORMAT", 415), (b"MZ\x90\x00 programme", "MEDIA_FORMAT", 415),
    (b'<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>', "SVG_DANGEREUX", 422),
    (b'<svg xmlns="http://www.w3.org/2000/svg" onload="alert(1)"></svg>', "SVG_DANGEREUX", 422),
    (b'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"><image xlink:href="http://evil.test/t.png"/></svg>', "SVG_DANGEREUX", 422),
    (b'<svg xmlns="http://www.w3.org/2000/svg"><foreignObject/></svg>', "SVG_DANGEREUX", 422)])
def test_fichiers_dangereux_refuses_par_le_contenu(env, contenu, code, statut):
    c, _ = env
    r = c.post("/api/admin/media", content=contenu, headers={**H, "Content-Type": "image/png"})   # l'en-tête ne trompe pas
    assert r.status_code == statut and r.json()["code"] == code


def test_media_trop_gros_et_suppression_protegee(world, monkeypatch):
    c = world["c"]
    from app import media
    monkeypatch.setattr(media, "MAX_OCTETS", 100)
    assert c.post("/api/admin/media", content=PNG + b"0" * 200, headers=H).status_code == 413
    monkeypatch.setattr(media, "MAX_OCTETS", 2 * 1024 * 1024)
    m = c.post("/api/admin/media", content=PNG, headers=H).json()
    ex = world["exos"][0]
    c.put(f"/api/admin/exercices/{ex['id']}", headers=H, json={**ex, "sujet": ex["sujet"] + "\n\n" + m["markdown"]})
    r = c.delete(f"/api/admin/media/{m['id']}", headers=H)
    assert r.status_code == 409 and r.json()["count"] == 1                          # image utilisée : suppression bloquée
    assert c.delete(f"/api/admin/media/{m['id']}?force=1", headers=H).status_code == 204


def test_export_import_conserve_les_images(world, tmp_path):
    from fastapi.testclient import TestClient
    from app.main import create_app
    c = world["c"]
    m = c.post("/api/admin/media", content=PNG, headers={**H, "X-Filename": "fig.png"}).json()
    doc = c.get("/api/admin/export", headers=H).json()
    assert doc["schemaVersion"] == "1.2" and [x["id"] for x in doc["medias"]] == [m["id"]]
    c2 = TestClient(create_app(str(tmp_path / "autre.db"), "tok"))
    assert c2.post("/api/admin/import?mode=remplacer", json=doc, headers=H).json()["medias"] == 1
    assert c2.get(m["url"]).content == PNG
    doc["medias"][0]["data"] = base64.b64encode(b"pas une image").decode()
    r = c2.post("/api/admin/import?mode=fusionner", json=doc, headers=H)
    assert r.status_code == 422 and any("media" in e for e in r.json()["errors"])
    doc.pop("medias")
    doc["schemaVersion"] = "1.1"                                                     # les anciens exports restent importables
    assert c2.post("/api/admin/import?mode=fusionner", json=doc, headers=H).status_code == 200


def test_apercu_signale_les_structures_invalides(env):
    c, _ = env
    r = c.post("/api/admin/preview", headers=H, json={"markdown": "```mol\nC(C\nCCO éthanol\n```"})
    assert len(r.json()["avertissements"]) == 1 and "parenthèse" in r.json()["avertissements"][0]
