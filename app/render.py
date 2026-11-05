"""Rendu HTML des épreuves et corrigés (Markdown sans HTML brut → pas d'injection)."""
from html import escape

from markdown_it import MarkdownIt

_md = MarkdownIt("commonmark", {"html": False, "linkify": False}).enable("table")


def md(text: str) -> str:
    return _md.render(text)


def exam_page(gen: dict, corrige: bool = False, autoprint: bool = False) -> str:
    p = gen["params"]
    titre = f"{'Corrigé — ' if corrige else ''}{p['matiere']} — {p['classe']}"
    meta = " · ".join(x for x in (p["classe"], p["specialite"], p["sequence"], p["difficulte"]) if x)
    blocs = "".join(
        f'<section class="exo"><h2>Exercice {i}</h2><div class="md">{md(e["corrige"] if corrige else e["sujet"])}</div></section>'
        for i, e in enumerate(gen["contenu"], 1))
    script = '<script src="/static/print.js"></script>' if autoprint else ""
    return (f'<!doctype html><html lang="fr"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{escape(titre)}</title><link rel="stylesheet" href="/static/exam.css"></head><body>'
            f'<header><h1>{escape(titre)}</h1><p class="meta">{escape(meta)}</p></header>'
            f'<main>{blocs}</main>{script}</body></html>')
