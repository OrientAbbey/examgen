"""La banque de démonstration doit ressembler à une vraie banque : énoncés sensés, corrigés vérifiés, couverture suffisante."""
import random
import re
from collections import Counter, defaultdict

import pytest

from app import db, demo_bank, seed, service
from app.models import GenerateIn

EX = demo_bank.exercices()
N = {"Facile": 2, "Moyen": 4, "Difficile": 6}
MATH = re.compile(r"\$\$.*?\$\$|\$[^$]*\$", re.S)
# Aucun symbole mathématique en Unicode « brut » : indices, exposants, racines… s'écrivent en LaTeX ($u_1$, $\\mathrm{e}^{2}$).
UNICODE_MATH = set("²³⁰¹⁴⁵⁶⁷⁸⁹₀₁₂₃₄₅₆₇₈₉ₙ₊₋⁻√≤≥≠⇔∈ℝ∞∫Δπθ×−→≈·")
# mise en forme défectueuse À L'INTÉRIEUR des formules : signes empilés, coefficient 1 superflu, None/nan
DEFAUT = re.compile(r"\\times -|\+ -|- -|\+ \+|= =|\b1[xyzt]\b|\bNone\b|\bnan\b|\\frac\{1\}\{1\}|\{,\}\}")


TOUS = demo_bank.tous()


def test_enonces_et_corriges_complets_et_propres():
    assert len(EX) >= 100 and len(demo_bank.exercices_pc()) >= 20
    for e in TOUS:
        txt = e["sujet"] + e["corrige"]
        assert len(e["sujet"]) > 40 and "Solution :" in e["corrige"] and "Solution" not in e["sujet"], e
        assert not (set(txt) & UNICODE_MATH), (e["classe"], e["partie"], sorted(set(txt) & UNICODE_MATH))
        hors = MATH.sub("", txt)
        assert not re.search(r"[\^_\\]", hors), ("formule hors $…$ :", e["classe"], e["partie"], re.search(r".{0,20}[\^_\\].{0,20}", hors).group())
        assert txt.replace("\\$", "").count("$") % 2 == 0, "dollars non appariés"
        for f in MATH.findall(txt):
            assert not DEFAUT.search(f), (e["classe"], e["partie"], f)
        assert "démonstration" not in e["sujet"].lower() and "voir le cours" not in e["corrige"].lower()
    sujets = [e["sujet"] for e in TOUS]
    assert len(set(sujets)) == len(sujets), "énoncés en double"


def test_physique_chimie_utilise_les_formules_moleculaires_ions_et_unites():
    pc = demo_bank.exercices_pc()
    txt = " ".join(e["sujet"] + e["corrige"] for e in pc)
    for attendu in (r"\ce{H2O}", r"\ce{CO2}", r"\ce{H3O+}", r"Na+(aq)", r"\ce{CH4 + 2O2 -> CO2 + 2H2O}", r"\pu{mol.L-1}", r"\pu{m.s-1}", r"\Omega"):
        assert attendu in txt, attendu


def test_couverture_deux_themes_par_classe_et_sequence():
    """Pour chaque classe et chaque séquence 1-6 : au moins 2 thèmes de parties différentes (sinon épreuves de 4-6 exercices impossibles)."""
    parties = defaultdict(set)
    for e in EX:
        if e["session"]:
            parties[(e["classe"], e["session"])].add(e["partie"])
    for classe in ("Seconde", "Première", "Terminale"):
        for seq in range(1, 7):
            assert len(parties[(classe, seq)]) >= 2, (classe, seq)


def test_trois_niveaux_pour_chaque_theme_et_problemes_de_synthese():
    c = Counter((e["classe"], e["partie"], e["session"]) for e in EX)
    assert all(v == 3 for v in c.values())
    assert sum(1 for e in EX if e["session"] is None) >= 3                     # pool « examen » (session vide)
    assert {e["niveau"] for e in EX} == {"Facile", "Moyen", "Difficile"}
    assert any(e["tag"] for e in EX)


@pytest.fixture(scope="module")
def conn(tmp_path_factory):
    path = str(tmp_path_factory.mktemp("demo") / "demo.db")
    seed.main(path)
    return db.connect(path)


def test_generation_sur_toute_la_grille(conn):
    """Toute combinaison valide produit une épreuve ; on mesure la part d'épreuves complètes."""
    m = conn.execute("SELECT id FROM matieres WHERE nom='Mathématiques'").fetchone()[0]
    cl = {r["nom"]: r["id"] for r in conn.execute("SELECT id, nom FROM classes")}
    sp = {r["nom"]: r["id"] for r in conn.execute("SELECT id, nom FROM specialites")}
    rng = random.Random(7)
    total = complete = 0
    for classe in cl:
        for spec in ([None] if classe == "Seconde" else ["Mathématiques", "Physique-Chimie"]):
            for sess in ["", "1", "2", "3", "4", "5", "6", "EXAMEN_BLANC", "EXAMEN"]:
                for diff in N:
                    g = service.generate_exam(conn, "u", GenerateIn(matiereId=m, classeId=cl[classe], specialiteId=sp[spec] if spec else None,
                                                                    session=sess or None, difficulte=diff), rng)
                    assert len(g["contenu"]) > 0, (classe, spec, sess, diff)
                    total += 1
                    complete += len(g["contenu"]) == N[diff]
    assert complete / total >= 0.85, f"{complete}/{total} épreuves complètes"


def test_epreuve_type_terminale_est_complete_et_coherente(conn):
    m = conn.execute("SELECT id FROM matieres WHERE nom='Mathématiques'").fetchone()[0]
    ter = conn.execute("SELECT id FROM classes WHERE nom='Terminale'").fetchone()[0]
    sp = conn.execute("SELECT id FROM specialites WHERE nom='Mathématiques'").fetchone()[0]
    rng = random.Random(3)
    for _ in range(40):
        g = service.generate_exam(conn, "u2", GenerateIn(matiereId=m, classeId=ter, specialiteId=sp, session="3", difficulte="Moyen"), rng)
        assert len(g["contenu"]) == 4
        assert len({c["partie"] for c in g["contenu"]}) >= 2                      # plusieurs thèmes
        assert len({c["id"] for c in g["contenu"]}) == 4
