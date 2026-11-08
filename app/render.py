"""Rendu HTML des épreuves et corrigés (Markdown sans HTML brut → pas d'injection)."""
import re
from html import escape

from markdown_it import MarkdownIt
from mdit_py_plugins.dollarmath import dollarmath_plugin

from . import chem

# $...$ = formule en ligne, $$...$$ = formule centrée. Le LaTeX est conservé tel quel (échappé) : les _ et * des indices
# ne sont jamais pris pour du Markdown. Un « $ » isolé (ex. « 5 $ ») reste du texte (allow_space=False).
_md = (MarkdownIt("commonmark", {"html": False, "linkify": False}).enable("table")
       .use(dollarmath_plugin, allow_space=False, allow_digits=True, double_inline=False))


_MEDIA = re.compile(r"^/media/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")


def _fence(self, tokens, idx, options, env):
    """```mol [topologique|developpee|cram] [petit|moyen|grand] : une molécule (SMILES) par ligne, légende facultative."""
    tok = tokens[idx]
    info = tok.info.strip().split()
    if info and info[0].lower() in ("mol", "smiles", "molecule", "molécule"):
        return chem.rendre_bloc(info[1:], tok.content)
    return self.fence(tokens, idx, options, env)


def _image(self, tokens, idx, options, env):
    """Seules les images téléversées dans l'application (/media/<id>) sont affichées ; tout autre lien d'image est ignoré."""
    tok = tokens[idx]
    alt = self.renderInlineAsText(tok.children, options, env)
    src = tok.attrGet("src") or ""
    if not _MEDIA.match(src):
        return escape(alt)
    return '<img class="figure" src="%s" alt="%s">' % (escape(src, quote=True), escape(alt, quote=True))


_md.add_render_rule("fence", _fence)
_md.add_render_rule("image", _image)


def md(text: str) -> str:
    return _md.render(text)


def exam_page(gen: dict, corrige: bool = False, autoprint: bool = False) -> str:
    p = gen["params"]
    titre = f"{'Corrigé — ' if corrige else ''}{p['matiere']} — {p['classe']}"
    meta = " · ".join(x for x in (p["classe"], p["specialite"], p["sequence"], p["difficulte"]) if x)
    blocs = "".join(
        f'<section class="exo"><h2>Exercice {i}</h2><div class="md">{md(e["corrige"] if corrige else e["sujet"])}</div></section>'
        for i, e in enumerate(gen["contenu"], 1))
    script = ('<script src="/static/katex/katex.min.js"></script><script src="/static/katex/mhchem.min.js"></script>'
              '<script src="/static/katex/macros.js"></script><script src="/static/math.js"></script>'
              + ('<script src="/static/print.js"></script>' if autoprint else ""))
    return (f'<!doctype html><html lang="fr"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{escape(titre)}</title><link rel="stylesheet" href="/static/katex/katex.min.css"><link rel="stylesheet" href="/static/exam.css"></head><body>'
            f'<header><h1>{escape(titre)}</h1><p class="meta">{escape(meta)}</p></header>'
            f'<main>{blocs}</main>{script}</body></html>')
