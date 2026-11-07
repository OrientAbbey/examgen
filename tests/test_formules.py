"""Rendu des formules : indices, exposants, fractions, formules moléculaires, ions, unités (KaTeX + mhchem)."""
import html
import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

from app import demo_bank, render

from .conftest import H, post

ROOT = Path(__file__).resolve().parent.parent
KATEX = ROOT / "app" / "static" / "katex"
INLINE = re.compile(r'<span class="math inline">(.*?)</span>', re.S)
BLOCK = re.compile(r'<div class="math block">\n?(.*?)\n?</div>', re.S)


def fragments(texts):
    out = []
    for t in texts:
        h = render.md(t)
        out += [{"tex": html.unescape(m), "block": False} for m in INLINE.findall(h)]
        out += [{"tex": html.unescape(m.strip()), "block": True} for m in BLOCK.findall(h)]
    return out


def check_katex(frags):
    r = subprocess.run(["node", str(ROOT / "tests" / "check_latex.cjs"), str(KATEX)], input=json.dumps(frags), capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


def test_latex_conserve_tel_quel_cote_serveur():
    h = render.md(r"Soit $u_1$ et $u_{n+1} = 2u_n * 3$, puis $\mathrm{e}^{2}$ et <b>x</b> & $a<b$.")
    assert INLINE.findall(h) == ["u_1", "u_{n+1} = 2u_n * 3", r"\mathrm{e}^{2}", "a&lt;b"]
    assert "<em>" not in h and "<b>" not in h and "&lt;b&gt;" in h          # ni emphase Markdown, ni HTML brut


def test_dollar_isole_et_echappe_restent_du_texte():
    h = render.md(r"Un prix de 5 $ ou 6 $, et \$ échappé.")
    assert "math" not in h and "5 $ ou 6 $" in h


def test_formule_centree():
    assert BLOCK.findall(render.md("$$\\int_0^1 x\\,dx$$")) == [r"\int_0^1 x\,dx"]


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js absent")
def test_toutes_les_formules_de_la_banque_sont_valides_katex():
    frags = fragments([e["sujet"] for e in demo_bank.tous()] + [e["corrige"] for e in demo_bank.tous()])
    assert len(frags) > 1000
    res = check_katex(frags)
    assert res["checked"] == len(frags) and res["bad"] == [], res["bad"][:5]


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js absent")
def test_chimie_unites_macros_et_detection_des_erreurs():
    ok = [r"\ce{H2O}", r"\ce{SO4^2-}", r"\ce{CH4 + 2O2 -> CO2 + 2H2O}", r"\ce{H3O+ + HO- <=> 2H2O}", r"[\ce{H3O+}] = 1{,}0 \times 10^{-3}\,\pu{mol.L-1}",
          r"\pu{m.s-1}", r"\R, \N, \Z, \Q, \C", r"u_{n+1}", r"\mathrm{e}^{-\frac{x}{2}}", r"\overrightarrow{AB}", r"\binom{n}{k}"]
    res = check_katex([{"tex": t} for t in ok] + [{"tex": r"\frac{1"}, {"tex": r"\commandeinconnue{x}"}])
    assert [b["tex"] for b in res["bad"]] == [r"\frac{1", r"\commandeinconnue{x}"]      # le contrôle détecte bien les vraies erreurs


def test_assets_katex_servis_et_pages_les_chargent(world):
    c = world["c"]
    assert c.get("/static/katex/katex.min.js").status_code == 200
    assert c.get("/static/katex/mhchem.min.js").status_code == 200
    css = c.get("/static/katex/katex.min.css")
    assert css.status_code == 200 and "woff2" in css.text and ".ttf" not in css.text
    assert c.get("/static/katex/fonts/KaTeX_Main-Regular.woff2").status_code == 200
    j = c.post("/api/generate", json={"matiereId": world["m"]["id"], "classeId": world["ter"]["id"], "specialiteId": world["sp"]["id"], "difficulte": "Facile"}).json()
    for url in (j["urls"]["epreuve"], j["urls"]["corrige"]):
        page = c.get(url).text
        for ressource in ("katex.min.css", "katex.min.js", "mhchem.min.js", "macros.js", "math.js"):
            assert ressource in page, (url, ressource)
    imp = c.get(j["urls"]["imprimer"]).text
    assert imp.index("math.js") < imp.index("print.js")          # on n'imprime qu'après la mise en forme des formules


def test_apercu_admin_meme_rendu_et_protege(env):
    c, _ = env
    assert c.post("/api/admin/preview", json={"markdown": "x"}).status_code == 401
    r = c.post("/api/admin/preview", headers=H, json={"markdown": r"Eau $\ce{H2O}$, **gras**, <script>alert(1)</script>"})
    h = r.json()["html"]
    assert r.status_code == 200 and INLINE.findall(h) == [r"\ce{H2O}"] and "<strong>gras</strong>" in h and "<script>" not in h
