import random
from collections import Counter

import pytest

from app.generator import (AUCUNE, Demande, bank_frame, build_candidates, generate, parse_session,
                           rank_depths, run_once, make_key, NIVEAUX)

ANC = ["P", "S"]  # Terminale (T) ← Première (P) ← Seconde (S)


def ex(i, classe="T", partie="p1", session=1, niveau="Moyen", tag=False, spec=(AUCUNE,)):
    return dict(id=f"e{i}", partie_id=partie, session=session, niveau=niveau, tag=tag,
                classe_ids=[classe], specialite_ids=list(spec))


def cands(rows, demande, classe="T", anc=ANC):
    return build_candidates(bank_frame(rows), rank_depths(classe, anc, demande.a_examen, demande.difficulte), demande)


def ids(cs):
    return {c.id for c in cs}


# ───── éligibilité statique ─────
def test_sequence_inferieure_ou_egale_et_session_vide_exclue():
    rows = [ex(1, session=1), ex(2, session=3), ex(3, session=4), ex(4, session=None)]
    assert ids(cands(rows, Demande("Moyen", seq=3))) == {"e1", "e2"}


def test_session_vide_demandee_prend_tout_pour_la_classe():
    rows = [ex(1, session=1), ex(2, session=6), ex(3, session=None)]
    assert ids(cands(rows, Demande("Moyen"))) == {"e1", "e2", "e3"}


def test_examen_taggues_et_session_vide_seulement():
    rows = [ex(1, session=2, tag=True), ex(2, session=2), ex(3, session=None)]
    for d in (Demande("Moyen", exam_mode=True),):
        assert ids(cands(rows, d)) == {"e1", "e3"}


def test_classe_inferieure_seq_5_6_seulement_et_vide_exclue():
    rows = [ex(1, "P", session=4), ex(2, "P", session=5), ex(3, "P", session=6), ex(4, "P", session=None)]
    assert ids(cands(rows, Demande("Facile", seq=2, a_examen=True))) == {"e2", "e3"}


def test_classe_inferieure_taguee_examen_seq_basse_exclue():
    rows = [ex(1, "P", session=2, tag=True), ex(2, "P", session=5, tag=True), ex(3, "P", session=5)]
    assert ids(cands(rows, Demande("Facile", exam_mode=True, a_examen=True))) == {"e2"}


def test_politique_difficulte_classes_inferieures():
    rows = [ex(1, "P", session=5), ex(2, "P", session=6), ex(3, "T", session=1)]
    assert ids(cands(rows, Demande("Facile", a_examen=True))) == {"e1", "e2", "e3"}
    assert ids(cands(rows, Demande("Moyen", a_examen=True))) == {"e2", "e3"}
    assert ids(cands(rows, Demande("Difficile", a_examen=True))) == {"e3"}


def test_profondeur_selon_a_examen():
    rows = [ex(1, "P", session=6), ex(2, "S", session=6)]
    assert ids(cands(rows, Demande("Facile", a_examen=False))) == {"e1"}
    assert ids(cands(rows, Demande("Facile", a_examen=True))) == {"e1", "e2"}


def test_specialite_aucune_universel_et_specifique():
    rows = [ex(1, spec=(AUCUNE,)), ex(2, spec=("S1",)), ex(3, spec=("S2",)), ex(4, "P", session=6, spec=(AUCUNE,))]
    assert ids(cands(rows, Demande("Facile", specialite_id="S1", a_examen=True))) == {"e1", "e2", "e4"}
    assert ids(cands(rows, Demande("Facile", a_examen=True))) == {"e1", "e4"}  # champ vide → Aucune seulement


# ───── tirage ─────
def test_nombre_exercices_par_difficulte():
    rows = [ex(i, partie=f"p{i % 8}", session=1) for i in range(40)]
    for diff, n in (("Facile", 2), ("Moyen", 4), ("Difficile", 6)):
        d = Demande(diff)
        assert len(run_once(cands(rows, d), d, random.Random(0)).ids) == n


def test_regle_50_pourcent():
    rows = [ex(i, partie=f"p{i % 6}", session=3) for i in range(12)] + \
           [ex(100 + i, partie=f"p{i % 6}", session=1) for i in range(12)]
    d = Demande("Difficile", seq=3)
    cs = cands(rows, d)
    for s in range(50):
        out = run_once(cs, d, random.Random(s))
        assert sum(1 for i in out.ids if int(i[1:]) < 100) >= 3


def test_relachement_silencieux_compense_par_classe_demandee_jamais_inferieure():
    rows = [ex(1, session=3, partie="a"), ex(2, session=1, partie="b"), ex(3, session=2, partie="c"),
            ex(4, session=1, partie="d"), ex(5, "P", session=6, partie="e")]
    d = Demande("Moyen", seq=3, a_examen=True)  # N=4, cible 2, 1 seul exercice en seq 3
    out = run_once(cands(rows, d), d, random.Random(1))
    assert out.relax == {"cible": 2, "phase1": 1, "deficit": 1, "comble": True}
    assert "e1" in out.ids and len(out.ids) == 4 and not out.incomplete
    # la compensation (phase 2a) n'utilise jamais la classe inférieure : e5 ne peut venir que de la phase 2b
    assert out.ids[1] != "e5"


def test_deficit_non_comble_epreuve_incomplete_sans_classe_inferieure():
    rows = [ex(1, session=3, partie="a"), ex(3, "P", session=6, partie="c")]
    d = Demande("Moyen", seq=3, a_examen=True)  # cible 2, 1 seul exercice en classe T ; P ne peut pas compenser
    out = run_once(cands(rows, d), d, random.Random(1))
    assert out.ids == ["e1"] and out.stopped_at == "2a" and out.incomplete
    assert out.relax["comble"] is False


def test_banque_vide():
    d = Demande("Moyen")
    out = run_once(cands([], d), d, random.Random(1))
    assert out.ids == [] and out.incomplete


def test_distribution_parties_P_inferieur_N():
    rows = [ex(i, partie=f"p{i % 4}", session=1) for i in range(40)]
    d = Demande("Difficile")  # N=6, P=4 → 2 parties ×2, 2 parties ×1
    for s in range(60):
        out = run_once(cands(rows, d), d, random.Random(s))
        cnt = Counter(f"p{int(i[1:]) % 4}" for i in out.ids)
        assert sorted(cnt.values()) == [1, 1, 2, 2]


def test_partie_unique_toute_l_epreuve_dans_la_partie():
    rows = [ex(i, partie="seule", session=1) for i in range(20)]
    d = Demande("Difficile")
    assert len(run_once(cands(rows, d), d, random.Random(0)).ids) == 6


def test_parties_superieures_a_N_une_fois_chacune():
    rows = [ex(i, partie=f"p{i % 5}", session=1) for i in range(30)]
    d = Demande("Facile")  # N=2, P=5
    for s in range(40):
        out = run_once(cands(rows, d), d, random.Random(s))
        assert len({int(i[1:]) % 5 for i in out.ids}) == 2


def test_max_un_exercice_par_niveau_inferieur():
    rows = [ex(i, "P", partie=f"p{i}", session=6) for i in range(10)] + \
           [ex(50 + i, "T", partie=f"q{i}", session=1) for i in range(3)]
    d = Demande("Facile", a_examen=False)
    for s in range(60):
        out = run_once(cands(rows, d), d, random.Random(s))
        assert sum(1 for i in out.ids if int(i[1:]) < 50) <= 1


def test_ponderation_orientee_non_bloquante():
    rows = [ex(1, partie="a", niveau="Facile"), ex(2, partie="b", niveau="Difficile")]
    d = Demande("Facile")  # N=2 → tire les deux (non bloquant)
    assert set(run_once(cands(rows, d), d, random.Random(0)).ids) == {"e1", "e2"}
    # fréquences : poids Facile 3 / Difficile 1 → Facile premier ≈ 75 %
    rows = [ex(1, partie="a", niveau="Facile", session=None), ex(2, partie="b", niveau="Difficile", session=None)]
    from app.generator import _State, _draw
    rng, firsts = random.Random(7), 0
    cs = cands(rows, d)
    for _ in range(2000):
        st = _State(1, 0)
        _draw(st, cs, 1, "Facile", rng)
        firsts += st.selected[0].id == "e1"
    assert 0.70 < firsts / 2000 < 0.80


# ───── unicité ─────
def test_unicite_evite_les_doublons_tant_que_possible():
    rows = [ex(i, partie=f"p{i % 3}", session=1) for i in range(9)]
    d = Demande("Facile")
    hist, rng = set(), random.Random(3)
    for _ in range(12):
        g = generate(cands(rows, d), d, hist, rng)
        assert not g.saturee
        k = make_key(g.outcome.ids)
        assert k not in hist
        hist.add(k)


def test_saturation_silencieuse_genere_un_doublon():
    rows = [ex(1, partie="a", session=1), ex(2, partie="b", session=1)]
    d = Demande("Facile")
    cs = cands(rows, d)
    g1 = generate(cs, d, set(), random.Random(0))
    g2 = generate(cs, d, {make_key(g1.outcome.ids)}, random.Random(0))
    assert g2.saturee and make_key(g2.outcome.ids) == make_key(g1.outcome.ids)


def test_parse_session():
    assert parse_session(None) == (None, False) and parse_session("") == (None, False)
    assert parse_session("4") == (4, False) and parse_session("EXAMEN_BLANC") == (None, True)
    with pytest.raises(ValueError):
        parse_session("7")


# ───── invariants sur banques aléatoires ─────
def test_invariants_aleatoires():
    R = random.Random(2024)
    classes, anc = ["T", "P", "S"], ANC
    for case in range(400):
        rows = []
        for i in range(R.randint(0, 60)):
            rows.append(ex(i, R.choice(classes), f"p{R.randint(0, R.randint(1, 7))}",
                           R.choice([None, 1, 2, 3, 4, 5, 6]), R.choice(NIVEAUX), R.random() < .3,
                           R.choice([(AUCUNE,), ("S1",), ("S2",), (AUCUNE, "S1")])))
        sess = R.choice([None, "1", "3", "5", "6", "EXAMEN", "EXAMEN_BLANC"])
        seq, em = parse_session(sess)
        d = Demande(R.choice(NIVEAUX), seq, em, R.choice([None, "S1"]), R.random() < .5)
        cs = cands(rows, d)
        out = run_once(cs, d, R)
        byid = {c.id: c for c in cs}
        sel = [byid[i] for i in out.ids]
        assert len(sel) == len(set(out.ids)) <= d.n                       # sans remise, ≤ N
        p = len({c.partie_id for c in cs})
        if p:
            base = max(1, d.n // p)
            cnt = Counter(c.partie_id for c in sel)
            assert max(cnt.values(), default=0) <= base + (1 if p < d.n and d.n % p else 0)
            assert sum(1 for v in cnt.values() if v > base) <= (d.n % p if p < d.n else 0)
        for depth in (1, 2):
            assert sum(1 for c in sel if c.depth == depth) <= 1            # 4.f
        if d.difficulte == "Difficile":
            assert all(c.depth == 0 for c in sel)                          # 4.k
        if d.difficulte == "Moyen":
            assert all(c.depth == 0 or c.session == 6 for c in sel)
        for c in sel:
            if c.depth > 0:
                assert c.session in (5, 6)                                 # 4.b / 4.c
            if seq:
                assert c.session is not None and (c.depth > 0 or c.session <= seq)
            if em:
                assert c.session is None or next(r for r in rows if r["id"] == c.id)["tag"]
        if seq and not out.relax:
            assert sum(1 for c in sel if c.depth == 0 and c.session == seq) >= d.n // 2 or p == 0


def test_point_a_arbitrer_4a_sans_relachement_donne_epreuve_incomplete():
    """Documenté dans docs/ (C.1) : P=2, N=6, une partie n'a qu'1 exercice → 4 exercices alors que la banque en a plus."""
    rows = [ex(0, partie="petite", session=1)] + [ex(i, partie="grande", session=1) for i in range(1, 10)]
    d = Demande("Difficile")
    out = run_once(cands(rows, d), d, random.Random(0))
    assert len(out.ids) == 4 and out.stopped_at == "2b"


def test_retentative_evite_le_piege_du_tirage_glouton():
    """Une épreuve complète existe, mais un tirage séquentiel peut consommer l'unique créneau « rang inférieur »
    nécessaire pour atteindre la partie C. generate() retente et renvoie une épreuve complète."""
    rows = [ex(i, "T", "A", session=1) for i in range(4)] + [ex(10 + i, "T", "B", session=1) for i in range(4)] \
        + [ex(20 + i, "P", "C", session=6) for i in range(3)] + [ex(30 + i, "P", "B", session=6) for i in range(3)]
    d = Demande("Moyen", a_examen=True)          # N=4, P=3 parties (A, B, C) : C n'est joignable que via le rang inférieur
    cs = cands(rows, d)
    seuls = [len(run_once(cs, d, random.Random(s)).ids) for s in range(80)]
    assert min(seuls) < 4                        # le piège existe bel et bien avec un seul tirage
    for s in range(80):
        g = generate(cs, d, set(), random.Random(s))
        assert len(g.outcome.ids) == 4 and not g.outcome.incomplete


def test_completude_prioritaire_sur_unicite():
    """Entre une épreuve complète déjà vue et une épreuve incomplète inédite, on préfère la complète."""
    rows = [ex(1, partie="a", session=1), ex(2, partie="b", session=1)]
    d = Demande("Facile")
    cs = cands(rows, d)
    vue = make_key(["e1", "e2"])
    g = generate(cs, d, {vue}, random.Random(0))
    assert make_key(g.outcome.ids) == vue and g.saturee and not g.outcome.incomplete
