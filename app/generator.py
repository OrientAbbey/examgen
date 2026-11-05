"""Algorithme de génération d'épreuves (cahier des charges V4.11, §4 et 7.4).

Module pur : aucune E/S. Le pool statique est construit avec Polars (filtres
d'éligibilité), puis le tirage pondéré sans remise est fait en Python.
"""
from __future__ import annotations

import random
from dataclasses import dataclass

import polars as pl

AUCUNE = "SPECIAL:Aucune"
NIVEAUX = ("Facile", "Moyen", "Difficile")
N_PAR_DIFFICULTE = {"Facile": 2, "Moyen": 4, "Difficile": 6}
# 7.4 — poids[difficulté de l'épreuve][niveau intrinsèque de l'exercice]
POIDS = {
    "Facile": {"Facile": 3, "Moyen": 2, "Difficile": 1},
    "Moyen": {"Facile": 1, "Moyen": 3, "Difficile": 1},
    "Difficile": {"Facile": 1, "Moyen": 2, "Difficile": 3},
}
# 4.k « Facile : le système encourage » les classes inférieures → multiplicateur de poids.
FACILE_BONUS_CLASSE_INFERIEURE = 2.0
MAX_TENTATIVES = 50


@dataclass(frozen=True)
class Candidate:
    id: str
    partie_id: str
    session: int | None
    niveau: str
    depth: int  # 0 = classe demandée ; 1, 2 = rang inférieur


@dataclass(frozen=True)
class Demande:
    difficulte: str
    seq: int | None = None        # séquence 1-6 demandée
    exam_mode: bool = False       # « Examen » ou « Examen blanc »
    specialite_id: str | None = None
    a_examen: bool = False        # la classe demandée a un examen (4.e)

    @property
    def n(self) -> int:
        return N_PAR_DIFFICULTE[self.difficulte]


def parse_session(value) -> tuple:
    """None/'' → (None, False) ; '1'..'6' → (n, False) ; EXAMEN/EXAMEN_BLANC → (None, True)."""
    if value is None or value == "":
        return None, False
    if value in ("EXAMEN", "EXAMEN_BLANC"):
        return None, True
    if str(value) in {"1", "2", "3", "4", "5", "6"}:
        return int(value), False
    raise ValueError(f"session invalide : {value!r}")


def rank_depths(classe_id: str, ancestors: list, a_examen: bool, difficulte: str) -> dict:
    """{classe_id → profondeur} pour la classe demandée et les rangs inférieurs autorisés (4.e, 4.k)."""
    max_depth = 0 if difficulte == "Difficile" else (2 if a_examen else 1)
    out = {classe_id: 0}
    for i, cid in enumerate(ancestors[:max_depth]):
        out[cid] = i + 1
    return out


BANK_SCHEMA = {
    "id": pl.Utf8, "partie_id": pl.Utf8, "session": pl.Int64, "niveau": pl.Utf8,
    "tag": pl.Boolean, "classe_ids": pl.List(pl.Utf8), "specialite_ids": pl.List(pl.Utf8),
}


def bank_frame(rows: list) -> pl.DataFrame:
    """rows : dicts avec les clés de BANK_SCHEMA (pour la matière demandée)."""
    if not rows:
        return pl.DataFrame(schema=BANK_SCHEMA)
    return pl.DataFrame(rows, schema=BANK_SCHEMA)


def build_candidates(bank: pl.DataFrame, depth_by_class: dict, demande: Demande) -> list:
    """Éligibilité statique : tableau 4.0 + 4.b + 4.c + 4.d/4.l + 4.h + 4.k."""
    if bank.height == 0:
        return []
    # Spécialité (4.d / 4.l) : « Aucune » est universel ; sinon la spécialité de l'utilisateur doit figurer.
    spec_ok = pl.col("specialite_ids").list.contains(AUCUNE)
    if demande.specialite_id:
        spec_ok = spec_ok | pl.col("specialite_ids").list.contains(demande.specialite_id)
    # Profondeur de classe (la plus petite si l'exercice cible plusieurs classes).
    depth_map = pl.DataFrame(
        {"classe_ids": list(depth_by_class), "depth": list(depth_by_class.values())},
        schema={"classe_ids": pl.Utf8, "depth": pl.Int64},
    )
    depths = (
        bank.select("id", "classe_ids").explode("classe_ids")
        .join(depth_map, on="classe_ids", how="inner")
        .group_by("id").agg(pl.col("depth").min())
    )
    df = bank.filter(spec_ok).join(depths, on="id", how="inner")

    s, d, tag = pl.col("session"), pl.col("depth"), pl.col("tag")
    if demande.seq is not None:                         # 4.b : séquences ≤ demandée ; vide exclue
        ok0 = s.is_not_null() & (s <= demande.seq)
    elif demande.exam_mode:                             # 4.h : tagués + session vide
        ok0 = s.is_null() | tag
    else:                                               # session vide demandée : tout
        ok0 = pl.lit(True)
    lower_seqs = [6] if demande.difficulte == "Moyen" else [5, 6]   # 4.b/4.c + 4.k
    # Classes inférieures : Seq 5-6 uniquement (la session vide y est exclue), tag requis en examen.
    ok_low = s.is_in(lower_seqs) & (tag if demande.exam_mode else pl.lit(True))
    df = df.filter(pl.when(d == 0).then(ok0).otherwise(ok_low).fill_null(False))

    return [Candidate(r["id"], r["partie_id"], r["session"], r["niveau"], r["depth"])
            for r in df.select("id", "partie_id", "session", "niveau", "depth").to_dicts()]


class _State:
    """État du tirage : applique 4.a (parties), 4.f (1 exercice max par rang inférieur), sans remise."""

    def __init__(self, base: int, extra: int):
        self.base, self.extra = base, extra
        self.selected: list = []
        self.ids: set = set()
        self.part_counts: dict = {}
        self.depths: set = set()

    def allowed(self, c: Candidate) -> bool:
        if c.id in self.ids:
            return False
        if c.depth > 0 and c.depth in self.depths:
            return False
        n = self.part_counts.get(c.partie_id, 0)
        if n < self.base:
            return True
        if n == self.base:   # occurrence supplémentaire : au plus `extra` parties au-delà de base
            return sum(1 for v in self.part_counts.values() if v > self.base) < self.extra
        return False

    def add(self, c: Candidate) -> None:
        self.selected.append(c)
        self.ids.add(c.id)
        self.part_counts[c.partie_id] = self.part_counts.get(c.partie_id, 0) + 1
        if c.depth > 0:
            self.depths.add(c.depth)


def _poids(c: Candidate, difficulte: str) -> float:
    w = POIDS[difficulte][c.niveau]
    if difficulte == "Facile" and c.depth > 0:
        w *= FACILE_BONUS_CLASSE_INFERIEURE
    return w


def _draw(st: _State, cands: list, k: int, difficulte: str, rng, only=lambda c: True) -> int:
    drawn = 0
    for _ in range(k):
        pool = [c for c in cands if only(c) and st.allowed(c)]
        if not pool:
            break
        pick = rng.choices(pool, weights=[_poids(c, difficulte) for c in pool], k=1)[0]
        st.add(pick)
        drawn += 1
    return drawn


@dataclass
class Outcome:
    ids: list                      # ordre de tirage
    n_demande: int
    parties_p: int = 0
    relax: dict | None = None      # RULE_50_RELAXED : {cible, phase1, deficit, comble}
    stopped_at: str | None = None  # "2a" | "2b" | "vide" si épreuve incomplète

    @property
    def incomplete(self) -> bool:
        return len(self.ids) < self.n_demande


def run_once(cands: list, demande: Demande, rng) -> Outcome:
    n = demande.n
    p = len({c.partie_id for c in cands})
    if p == 0:
        return Outcome([], n, 0, stopped_at="vide")
    # 4.a : P ≥ N → 1 par partie ; P < N → ⌊N/P⌋ par partie, N mod P parties en reçoivent une de plus.
    base = max(1, n // p)
    extra = n % p if p < n else 0
    st = _State(base, extra)
    relax, stop = None, None
    if demande.seq is not None:                                   # Phase 1 (4.g)
        cible = n // 2
        got1 = _draw(st, cands, cible, demande.difficulte, rng,
                     only=lambda c: c.depth == 0 and c.session == demande.seq)
        deficit = cible - got1
        if deficit > 0:                                           # Phase 2a : classe demandée uniquement
            got2 = _draw(st, cands, deficit, demande.difficulte, rng, only=lambda c: c.depth == 0)
            relax = {"cible": cible, "phase1": got1, "deficit": deficit, "comble": got2 == deficit}
            if got2 < deficit:
                stop = "2a"                                       # 2b sautée (décision 26)
    if stop is None:                                              # Phase 2b
        reste = n - len(st.selected)
        if reste > 0 and _draw(st, cands, reste, demande.difficulte, rng) < reste:
            stop = "2b"
    return Outcome([c.id for c in st.selected], n, p, relax, stop)


def make_key(ids) -> str:
    """Multiensemble d'exercices : l'ordre est indifférent (4.i)."""
    return ",".join(sorted(ids))


@dataclass
class Generation:
    outcome: Outcome
    tentatives: int
    saturee: bool


def generate(cands: list, demande: Demande, history_keys: set,
             rng=None, max_tentatives: int = MAX_TENTATIVES) -> Generation:
    """Tirage + unicité silencieuse (4.i). Les contraintes pédagogiques priment : en cas de
    saturation, le dernier tirage (doublon) est conservé."""
    rng = rng or random.Random()
    last = None
    for t in range(1, max_tentatives + 1):
        last = run_once(cands, demande, rng)
        if not last.ids or make_key(last.ids) not in history_keys:
            return Generation(last, t, False)
    return Generation(last, max_tentatives, True)
