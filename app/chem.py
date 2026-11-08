"""Structures chimiques : validation SMILES, formule brute, conversion en hydrogènes explicites (formule développée)
et fabrication du HTML des blocs ```mol (le dessin SVG est fait dans le navigateur par SmilesDrawer, licence MIT)."""
import html
import re
from collections import Counter

VALENCES = {"B": (3,), "C": (4,), "N": (3, 5), "O": (2,), "P": (3, 5), "S": (2, 4, 6), "F": (1,), "Cl": (1,), "Br": (1,), "I": (1,)}
PI_AROMATIQUE = {"c": 1, "n": 1, "b": 1, "p": 1, "o": 0, "s": 0}
TOKEN = re.compile(r"\[[^\]]*\]|Br|Cl|[BCNOPSFI]|[bcnops]|%\d\d|\d|[=#$:/\\\-]|[()]|\.")
BRACKET = re.compile(r"^\[(\d+)?([A-Za-z][a-z]?)(@@?)?(H\d*)?([+-]{1,2}\d*)?(:\d+)?\]$")
ORDRE = {"=": 2, "#": 3, "$": 4}
STYLES = {"topologique": "topologique", "topo": "topologique", "developpee": "developpee", "développée": "developpee",
          "developpe": "developpee", "cram": "cram", "stereo": "cram", "stéréo": "cram"}
TAILLES = {"petit": "petit", "moyen": "moyen", "grand": "grand"}
MAX_SMILES = 300


class _Atome:
    def __init__(self, idx, tok_i, sym, arom, bracket, h=None, chiral=None, tok=""):
        self.idx, self.tok_i, self.sym, self.arom, self.bracket, self.h, self.chiral, self.tok = idx, tok_i, sym, arom, bracket, h, chiral, tok
        self.somme = 0           # somme des ordres de liaison (liaisons aromatiques comptées 1)


def _tokens(s: str) -> list:
    s, pos, out = s.strip(), 0, []
    if not s:
        raise ValueError("SMILES vide")
    if len(s) > MAX_SMILES:
        raise ValueError("SMILES trop long")
    while pos < len(s):
        m = TOKEN.match(s, pos)
        if not m:
            raise ValueError("caractère inattendu « %s » en position %d" % (s[pos], pos + 1))
        out.append(m.group())
        pos = m.end()
    return out


def parse(smiles: str):
    toks = _tokens(smiles)
    atomes, rings, pile, last_ring = [], {}, [], {}
    prev, pending = None, None

    def lier(a, b, sym):
        o = ORDRE.get(sym, 1)
        a.somme += o
        b.somme += o

    for i, t in enumerate(toks):
        if t == "(":
            if prev is None:
                raise ValueError("parenthèse ouvrante sans atome précédent")
            pile.append(prev)
        elif t == ")":
            if not pile:
                raise ValueError("parenthèse fermante sans ouvrante")
            prev = pile.pop()
        elif t == ".":
            prev, pending = None, None
        elif t in "=#$:/\\-" and len(t) == 1:
            pending = t
        elif t[0] in "%0123456789":
            if prev is None:
                raise ValueError("fermeture de cycle sans atome")
            if t in rings:
                autre, sym0 = rings.pop(t)
                lier(prev, autre, pending or sym0)
            else:
                rings[t] = (prev, pending)
            pending = None
            last_ring[prev.idx] = i
        else:
            if t.startswith("["):
                m = BRACKET.match(t)
                if not m:
                    raise ValueError("atome entre crochets non reconnu : " + t)
                sym = m.group(2)
                h = 0 if not m.group(4) else int(m.group(4)[1:] or 1)
                a = _Atome(len(atomes), i, sym, sym[0].islower(), True, h, m.group(3), t)
            else:
                a = _Atome(len(atomes), i, t, t[0].islower(), False, None, None, t)
            atomes.append(a)
            if prev is not None:
                lier(prev, a, pending)
            prev, pending = a, None
    if pile:
        raise ValueError("parenthèse non fermée")
    if rings:
        raise ValueError("cycle non fermé (chiffre %s)" % sorted(rings)[0])
    if not atomes:
        raise ValueError("aucun atome")
    return toks, atomes, last_ring


def _h_implicites(a: _Atome) -> int:
    if a.bracket:
        return a.h or 0
    cap = a.sym.capitalize()
    somme = a.somme + (PI_AROMATIQUE.get(a.sym, 0) if a.arom else 0)
    for v in VALENCES[cap]:
        if v >= somme:
            return v - somme
    return 0


def valider(smiles: str) -> None:
    parse(smiles)


def formule_brute(smiles: str) -> str:
    """Formule brute (ordre de Hill) au format mhchem, ex. 'C2H6O'."""
    _, atomes, _ = parse(smiles)
    c = Counter()
    for a in atomes:
        c[a.sym.capitalize()] += 1
        h = _h_implicites(a)
        if h:
            c["H"] += h
    c["H"] += 0
    ordre = (["C", "H"] if "C" in c else []) + sorted(k for k in c if k not in ("C", "H")) if "C" in c else sorted(c)
    return "".join(k + (str(c[k]) if c[k] > 1 else "") for k in ordre if c[k])


def hydrogenes_explicites(smiles: str) -> str:
    """SMILES équivalent où tous les H sont des atomes : permet de dessiner la formule développée."""
    toks, atomes, last_ring = parse(smiles)
    insertions, remplace = {}, {}
    for a in atomes:
        h = _h_implicites(a)
        if not h:
            continue
        if a.bracket:
            if a.sym == "H":
                continue
            if a.chiral and h == 1 and a.idx in last_ring:      # ordre des voisins incertain : on laisse implicite
                continue
            m = BRACKET.match(a.tok)
            remplace[a.tok_i] = "[%s%s%s%s%s]" % (m.group(1) or "", m.group(2), m.group(3) or "", m.group(5) or "", m.group(6) or "")
        pos = last_ring.get(a.idx, a.tok_i)
        insertions[pos] = insertions.get(pos, "") + "([H])" * h
    return "".join(remplace.get(i, t) + insertions.get(i, "") for i, t in enumerate(toks))


def _attr(s: str) -> str:
    return html.escape(s, quote=True)


def rendre_bloc(info: list, contenu: str) -> str:
    """HTML d'un bloc ```mol [style] [taille] : une molécule par ligne, « SMILES  légende facultative »."""
    style, taille = "topologique", "moyen"
    for mot in info:
        mot = mot.lower()
        if mot in STYLES:
            style = STYLES[mot]
        elif mot in TAILLES:
            taille = TAILLES[mot]
    figs = []
    for ligne in contenu.splitlines():
        ligne = ligne.strip()
        if not ligne or ligne.startswith("#"):
            continue
        smi, _, legende = ligne.partition(" ")
        legende = legende.strip()
        try:
            valider(smi)
            dessin = hydrogenes_explicites(smi) if style == "developpee" else smi
        except ValueError as e:
            figs.append('<figure class="mol mol-error"><span>Structure invalide « %s » : %s</span></figure>' % (_attr(smi), _attr(str(e))))
            continue
        cap = "<figcaption>%s</figcaption>" % html.escape(legende) if legende else ""
        figs.append('<figure class="mol" data-smiles="%s" data-style="%s" data-size="%s" role="img" aria-label="Formule %s de %s">%s</figure>'
                    % (_attr(dessin), style, taille, "développée" if style == "developpee" else ("topologique" if style == "topologique" else "de Cram"),
                       _attr(legende or smi), cap))
    return '<div class="mols">%s</div>\n' % "".join(figs)
