"""Banque de démonstration RÉALISTE : mathématiques (Seconde / Première / Terminale) et physique-chimie.

Chaque énoncé est construit à partir de paramètres et son corrigé est CALCULÉ (fractions exactes) avec des vérifications
(assert). Les formules sont écrites en LaTeX entre « $ » ($u_1$, $\\mathrm{e}^{2}$, $\\ce{H2O}$ …) et mises en forme par KaTeX.
Convention : le corrigé commence par « Solution : » ; aucun sujet ne contient ce mot.
"""
from fractions import Fraction as F
from math import acos, ceil, comb, degrees, e, exp, isqrt, log, log10, sqrt

from . import chem

R = r"\R"
SEMI = r"\,;\,"


# ───────────────────────── mise en forme LaTeX ─────────────────────────
def M(s: str) -> str:
    return "$" + s + "$"


def n(x) -> str:
    """Nombre exact : entier ou \\frac{a}{b} (le signe moins est placé devant)."""
    x = F(x)
    if x.denominator == 1:
        return str(x.numerator)
    return ("-" if x < 0 else "") + r"\frac{%d}{%d}" % (abs(x.numerator), x.denominator)


def dec(x, d=2) -> str:
    """Décimal à la française dans une formule : 0{,}368 (la virgule est protégée de l'espacement)."""
    return f"{float(x):.{d}f}".replace(".", "{,}")


def par(x) -> str:
    return "(%s)" % n(x) if F(x) < 0 else n(x)


def sg(x) -> str:
    """Terme signé : ' + 3' ou ' - 3'."""
    return " - %s" % n(abs(F(x))) if F(x) < 0 else " + %s" % n(x)


def poly(cs, var="x") -> str:
    deg, out = len(cs) - 1, ""
    for i, c in enumerate(cs):
        c, p = F(c), deg - i
        if c == 0:
            continue
        a = abs(c)
        mono = "" if p == 0 else (var if p == 1 else "%s^{%d}" % (var, p))
        body = ("" if (a == 1 and p != 0) else n(a)) + mono
        out += ("-" if c < 0 else "") + body if not out else (" - " if c < 0 else " + ") + body
    return out or "0"


def lin(terms, const=None) -> str:
    """Forme linéaire 2x - y + 3z - 5 (coefficients ±1 omis)."""
    out = ""
    for c, v in terms:
        c = F(c)
        if c == 0:
            continue
        body = ("" if abs(c) == 1 else n(abs(c))) + v
        out += ("-" if c < 0 else "") + body if not out else (" - " if c < 0 else " + ") + body
    if const:
        out += sg(const)
    return out or "0"


def rad(m: int) -> str:
    k = 1
    for d in range(isqrt(m), 1, -1):
        if m % (d * d) == 0:
            k, m = d, m // (d * d)
            break
    return str(k) if m == 1 else (str(k) if k > 1 else "") + r"\sqrt{%d}" % m


def radeq(m: int) -> str:
    return (r"\sqrt{%d}" % m) if rad(m) == r"\sqrt{%d}" % m else r"\sqrt{%d} = %s" % (m, rad(m))


def cx(re, im) -> str:
    re, im = F(re), F(im)
    if im == 0:
        return n(re)
    a = abs(im)
    i = r"\mathrm{i}" if a == 1 else n(a) + r"\mathrm{i}"
    if re == 0:
        return ("-" if im < 0 else "") + i
    return "%s %s %s" % (n(re), "-" if im < 0 else "+", i)


def pt(*c) -> str:
    return "(" + SEMI.join(n(x) for x in c) + ")"


def lst(items) -> str:
    return "\n".join("%d. %s" % (i, t) for i, t in enumerate(items, 1))


OPS = {"≤": r"\leq", "<": "<", "≥": r"\geq", ">": ">"}
FLIP = {"≤": "≥", "<": ">", "≥": "≤", ">": "<"}


def interval(op, v) -> str:
    if op == "≤":
        return r"]-\infty%s%s]" % (SEMI, n(v))
    if op == "<":
        return r"]-\infty%s%s[" % (SEMI, n(v))
    if op == "≥":
        return r"[%s%s+\infty[" % (n(v), SEMI)
    return r"]%s%s+\infty[" % (n(v), SEMI)


def ex(a) -> str:
    """Exposant de l'exponentielle pour a·x : 2x, -x, -\\frac{x}{2}."""
    a = F(a)
    sign, a = ("-" if a < 0 else ""), abs(a)
    if a.denominator == 1:
        return f"{sign}{'' if a == 1 else a.numerator}x"
    return sign + r"\frac{%sx}{%d}" % ("" if a.numerator == 1 else a.numerator, a.denominator)


def par_t(p, c) -> str:
    t = ("" if abs(F(c)) == 1 else n(abs(F(c)))) + "t"
    if c == 0:
        return n(p)
    if p == 0:
        return ("-" if c < 0 else "") + t
    return "%s %s %s" % (n(p), "-" if c < 0 else "+", t)


# ───────────────────────── SECONDE ─────────────────────────
def eq1(v):
    sets = [[(3, 7, 1, 15), (5, -2, 2, 10)], [(4, 3, -1, 13), (6, -5, 2, 9), (7, 1, 3, -4)],
            [(-3, 8, 2, -7), (9, -4, -5, 11), (2, 5, 7, -5)]][v]
    q, s = [], []
    for p_, q_, r_, s_ in sets:
        x = F(s_ - q_, p_ - r_)
        assert p_ * x + q_ == r_ * x + s_
        eq = "%s = %s" % (poly([p_, q_]), poly([r_, s_]))
        q.append(M(eq))
        s.append(M(r"%s \Leftrightarrow %s = %s \Leftrightarrow x = %s" % (eq, poly([p_ - r_, 0]), n(s_ - q_), n(x))))
    return ("**Équations du premier degré.** Résoudre dans " + M(R) + " les équations suivantes :\n\n" + lst(q), "Solution :\n\n" + lst(s))


def dev(v):
    sets = [[(1, 3, 1, 5), (1, -4, 1, -4)], [(1, 2, 1, -7), (2, 3, 1, -1), (1, 6, 1, 6)],
            [(3, -2, 2, 5), (2, 1, 2, 1), (1, -5, 1, 5)]][v]
    q, s = [], []
    for p_, q_, r_, s_ in sets:
        sq = (p_, q_) == (r_, s_)
        expr = "(%s)^{2}" % poly([p_, q_]) if sq else "(%s)(%s)" % (poly([p_, q_]), poly([r_, s_]))
        q.append(M(expr))
        s.append(M("%s = %s" % (expr, poly([p_ * r_, p_ * s_ + q_ * r_, q_ * s_]))))
    return ("**Développer et réduire** chacune des expressions suivantes :\n\n" + lst(q), "Solution :\n\n" + lst(s))


def ineq(v):
    sets = [[(2, 3, "≤", 11)], [(3, -1, ">", 8), (-2, 5, "≤", 1)],
            [(-4, 3, "<", 15), (5, 2, "≥", -8), (-3, 1, ">", 7)]][v]
    q, s = [], []
    for a, b, op, c in sets:
        val, op2 = F(c - b, a), (op if a > 0 else FLIP[op])
        q.append(M("%s %s %s" % (poly([a, b]), OPS[op], n(c))))
        s.append(M(r"%s %s %s \Leftrightarrow %s %s %s \Leftrightarrow x %s %s" % (poly([a, b]), OPS[op], n(c), poly([a, 0]), OPS[op], n(c - b), OPS[op2], n(val)))
                 + ". Ensemble des solutions : " + M(interval(op2, val)) + "." + (" (On change le sens de l'inégalité car on divise par un nombre négatif.)" if a < 0 else ""))
    return ("**Inéquations.** Résoudre dans " + M(R) + ", puis donner l'ensemble des solutions sous forme d'intervalle :\n\n" + lst(q), "Solution :\n\n" + lst(s))


def affine(v):
    m, p_, a, c = [(2, 1, 3, 9), (-3, 4, 2, -5), (F(5, 2), -1, 4, 14)][v]
    f = lambda x: m * x + p_
    x0 = F(c - p_) / F(m)
    assert f(x0) == c
    return ("Soit $f$ la fonction affine définie sur " + M(R) + " par " + M("f(x) = " + poly([m, p_])) + ".\n\n"
            + lst(["Calculer " + M("f(%s)" % n(a)) + ".", "Déterminer l'antécédent de " + M(n(c)) + " par $f$.", "Donner le sens de variation de $f$, en justifiant."]),
            "Solution :\n\n" + lst([M("f(%s) = %s" % (n(a), n(f(a)))) + ".",
                                    M(r"f(x) = %s \Leftrightarrow %s = %s \Leftrightarrow x = %s" % (n(c), poly([m, p_]), n(c), n(x0))) + ".",
                                    "Le coefficient directeur " + M(n(m)) + " est %s : $f$ est strictement %s sur " % ("positif" if m > 0 else "négatif", "croissante" if m > 0 else "décroissante") + M(R) + "."]))


def carre(v):
    k, t = [(4, None), (6, 16), (10, 24)][v]
    h, q = k // 2, k * k // 4
    f = "f(x) = x^{2} - %dx" % k
    qs = ["Factoriser " + M("f(x)") + ".", "Résoudre l'équation " + M("f(x) = 0") + ".",
          "Montrer que " + M("f(x) = (x - %d)^{2} - %d" % (h, q)) + ". En déduire le minimum de $f$."]
    ss = [M("f(x) = x(x - %d)" % k) + ".", M(r"x(x - %d) = 0 \Leftrightarrow x = 0 \text{ ou } x = %d" % (k, k)) + ".",
          M("(x - %d)^{2} - %d = x^{2} - %dx + %d - %d = f(x)" % (h, q, k, q, q)) + ". Un carré est positif ou nul, donc " + M(r"f(x) \geq -%d" % q)
          + ", avec égalité pour " + M("x = %d" % h) + " : le minimum de $f$ est " + M("-%d" % q) + "."]
    if t:
        r = isqrt(t + q)
        assert r * r == t + q and (h + r) ** 2 - k * (h + r) == t and (h - r) ** 2 - k * (h - r) == t
        qs.append("Résoudre l'équation " + M("f(x) = %d" % t) + ".")
        ss.append(M(r"f(x) = %d \Leftrightarrow (x - %d)^{2} = %d \Leftrightarrow x = %d \text{ ou } x = %d" % (t, h, t + q, h + r, h - r)) + ".")
    return ("Soit $f$ la fonction définie sur " + M(R) + " par " + M(f) + ".\n\n" + lst(qs), "Solution :\n\n" + lst(ss))


def dist(v):
    A, B = [((1, 2), (4, 6)), ((-2, 1), (3, -4)), ((-3, -1), (5, 5))][v]
    dx, dy = B[0] - A[0], B[1] - A[1]
    d2 = dx * dx + dy * dy
    I = (F(A[0] + B[0], 2), F(A[1] + B[1], 2))
    return ("Dans un repère orthonormé, on considère les points " + M("A" + pt(*A)) + " et " + M("B" + pt(*B)) + ".\n\n"
            + lst(["Calculer la distance " + M("AB") + ".", "Déterminer les coordonnées du milieu $I$ du segment " + M("[AB]") + "."]),
            "Solution :\n\n" + lst([M(r"AB = \sqrt{(%s - %s)^{2} + (%s - %s)^{2}} = \sqrt{%d + %d} = %s" % (n(B[0]), par(A[0]), n(B[1]), par(A[1]), dx * dx, dy * dy, radeq(d2))) + ".",
                                    M(r"I\left(\frac{%s + %s}{2}%s\frac{%s + %s}{2}\right) = I%s" % (n(A[0]), par(B[0]), SEMI, n(A[1]), par(B[1]), pt(*I))) + "."]))


def para(v):
    A, B, C = [((1, 1), (4, 2), (5, 5)), ((-1, 2), (2, 0), (4, 3)), ((0, -2), (3, 1), (2, 5))][v]
    D = (A[0] + C[0] - B[0], A[1] + C[1] - B[1])
    AB, DC = (B[0] - A[0], B[1] - A[1]), (C[0] - D[0], C[1] - D[1])
    assert AB == DC
    I = (F(A[0] + C[0], 2), F(A[1] + C[1], 2))
    assert I == (F(B[0] + D[0], 2), F(B[1] + D[1], 2))
    return ("Dans un repère orthonormé, on donne " + M("A" + pt(*A)) + ", " + M("B" + pt(*B)) + " et " + M("C" + pt(*C)) + ".\n\n"
            + lst(["Déterminer les coordonnées du point $D$ tel que $ABCD$ soit un parallélogramme.", "Vérifier que les diagonales " + M("[AC]") + " et " + M("[BD]") + " ont le même milieu."]),
            "Solution :\n\n" + lst(["$ABCD$ est un parallélogramme si et seulement si " + M(r"\overrightarrow{AB} = \overrightarrow{DC}") + ". Or " + M(r"\overrightarrow{AB}" + pt(*AB))
                                    + " et, en notant " + M("D(x%sy)" % SEMI) + ", " + M(r"\overrightarrow{DC}(%s - x%s%s - y)" % (n(C[0]), SEMI, n(C[1]))) + ". On obtient " + M("D" + pt(*D)) + ".",
                                    "Milieu de " + M("[AC]") + " : " + M("I" + pt(*I)) + ". Milieu de " + M("[BD]") + " : " + M("I" + pt(*I)) + ". Les deux milieux sont confondus."]))


def urne(v):
    r, b, g = [(3, 5, 2), (6, 4, 5), (7, 9, 4)][v]
    N = r + b + g
    pr = F(r, N)
    qs = ["Calculer la probabilité de tirer une boule rouge.", "Calculer la probabilité de ne pas tirer une boule rouge.", "Calculer la probabilité de tirer une boule rouge ou une boule verte."]
    fr = r"\frac{%d}{%d}" % (r, N)
    ss = [M("P(R) = %s%s" % (fr, "" if fr == n(pr) else " = " + n(pr))) + ".", M(r"P(\overline{R}) = 1 - %s = %s" % (n(pr), n(1 - pr))) + ".",
          M(r"P(R \cup V) = \frac{%d + %d}{%d} = %s" % (r, g, N, n(F(r + g, N)))) + "."]
    ctx = "Une urne contient %d boules rouges, %d boules bleues et %d boules vertes, indiscernables au toucher. On tire une boule au hasard." % (r, b, g)
    if v == 1:
        ctx += " On répète l'expérience deux fois, **avec remise**."
        qs.append("Calculer la probabilité d'obtenir deux boules rouges.")
        ss.append("Tirages indépendants : " + M(r"P = \left(%s\right)^{2} = %s" % (n(pr), n(pr ** 2))) + ".")
    if v == 2:
        ctx += " On tire ensuite deux boules successivement, **sans remise**."
        qs.append("Calculer la probabilité d'obtenir deux boules rouges.")
        ss.append(M(r"P = \frac{%d}{%d} \times \frac{%d}{%d} = %s" % (r, N, r - 1, N - 1, n(pr * F(r - 1, N - 1)))) + ".")
    return ctx + "\n\n" + lst(qs), "Solution :\n\n" + lst(ss)


def stat(v):
    notes = [[12, 8, 13, 10, 13, 9, 12], [6, 15, 9, 12, 11, 8, 16, 10, 12], [4, 17, 9, 12, 14, 7, 19, 10, 15]][v]
    s, N = sorted(notes), len(notes)
    mean, med = F(sum(notes), N), s[N // 2]
    if mean.denominator == 1:
        moy = "Moyenne : " + M(r"\frac{%d}{%d} = %d" % (sum(notes), N, mean)) + "."
    else:
        moy = "Moyenne : " + M(r"\frac{%d}{%d} \approx %s" % (sum(notes), N, dec(mean))) + "."
    qs = ["Calculer la moyenne de cette série.", "Déterminer sa médiane.", "Calculer son étendue."]
    ss = [moy, "Série ordonnée : %s. Effectif impair (%d) : la médiane est la valeur de rang %d, soit %d." % (" ; ".join(map(str, s)), N, N // 2 + 1, med),
          "Étendue : " + M("%d - %d = %d" % (s[-1], s[0], s[-1] - s[0])) + "."]
    if v == 2:
        q1, q3 = s[ceil(N / 4) - 1], s[ceil(3 * N / 4) - 1]
        qs.append("Déterminer les premier et troisième quartiles.")
        ss.append("$Q_1$ est la valeur de rang %d : " % ceil(N / 4) + M("Q_1 = %d" % q1) + ". $Q_3$ est la valeur de rang %d : " % ceil(3 * N / 4) + M("Q_3 = %d" % q3) + ".")
    return ("Voici les notes obtenues par %d élèves à un contrôle : %s.\n\n" % (N, " ; ".join(map(str, notes))) + lst(qs), "Solution :\n\n" + lst(ss))


def vecteurs(v):
    (a, b), (c, d), extra = [((2, 3), (1, -4), None), ((-3, 6), (2, -4), None), ((4, -2), (-6, 3), 6)][v]
    det = a * d - b * c
    qs = ["Calculer les coordonnées de " + M(r"\vec{u} + \vec{v}") + " et de " + M(r"2\vec{u} - \vec{v}") + ".", "Les vecteurs " + M(r"\vec{u}") + " et " + M(r"\vec{v}") + " sont-ils colinéaires ? Justifier."]
    ss = [M(r"\vec{u} + \vec{v}") + " a pour coordonnées " + M(pt(a + c, b + d)) + " et " + M(r"2\vec{u} - \vec{v}") + " a pour coordonnées " + M(pt(2 * a - c, 2 * b - d)) + ".",
          "Déterminant : " + M("%s \\times %s - %s \\times %s = %s" % (n(a), par(d), par(b), par(c), n(det))) + ". "
          + ("Il est nul : les vecteurs sont colinéaires." if det == 0 else "Il n'est pas nul : les vecteurs ne sont pas colinéaires.")]
    if extra:
        k = F(a * extra, b)
        assert a * extra - b * k == 0
        qs.append("Déterminer le réel $k$ tel que " + M(r"\vec{u}") + " et " + M(r"\vec{w}(k%s%d)" % (SEMI, extra)) + " soient colinéaires.")
        ss.append(M(r"\vec{u}") + " et " + M(r"\vec{w}") + " colinéaires " + M(r"\Leftrightarrow %s \times %d - %s \times k = 0 \Leftrightarrow k = %s" % (n(a), extra, par(b), n(k))) + ".")
    return ("Dans un repère orthonormé, on considère les vecteurs " + M(r"\vec{u}" + pt(a, b)) + " et " + M(r"\vec{v}" + pt(c, d)) + ".\n\n" + lst(qs), "Solution :\n\n" + lst(ss))


def systemes(v):
    a, b, e_, c, d, f = [(1, 1, 3, 1, -1, 1), (2, 3, 12, 1, -1, 1), (3, -2, 4, 5, 4, 14)][v]
    det = a * d - b * c
    x, y = F(e_ * d - b * f, det), F(a * f - c * e_, det)
    assert a * x + b * y == e_ and c * x + d * y == f
    sys_ = r"\begin{cases} %s = %s \quad (L_1) \\ %s = %s \quad (L_2) \end{cases}" % (lin([(a, "x"), (b, "y")]), n(e_), lin([(c, "x"), (d, "y")]), n(f))
    return ("**Système d'équations.** Résoudre dans " + M(r"\R^{2}") + " le système suivant, en éliminant une inconnue par combinaison linéaire :\n\n$$" + sys_ + "$$",
            "Solution :\n\n- On élimine $y$ : " + M("(L_1) \\times %s - (L_2) \\times %s" % (par(d), par(b))) + " donne " + M("%sx = %s" % (n(det), n(e_ * d - b * f))) + ", d'où " + M("x = %s" % n(x)) + ".\n"
            "- En reportant dans " + M("(L_1)") + " : " + M("%s \\times %s %s = %s" % (n(a), par(x), lin([(b, "y")]).replace("-", "- ", 1) if b < 0 else "+ " + lin([(b, "y")]), n(e_))) + ", d'où " + M("y = %s" % n(y)) + ".\n"
            "- Vérification dans " + M("(L_2)") + " : " + M("%s \\times %s %s \\times %s = %s" % (n(c), par(x), "+" if d > 0 else "-", par(abs(d)) if abs(d) != 1 else "1", n(c * x + d * y)))
            + " ✓.\n\nConclusion : " + M("(x%sy) = %s" % (SEMI, pt(x, y))) + ".")


def inverse(v):
    a1, a2, c = [(2, 4, 5), (F(1, 3), 3, 10), (5, 2, F(1, 4))][v]
    a1, a2, c = F(a1), F(a2), F(c)
    small, big = sorted([a1, a2])
    return ("Soit $f$ la fonction inverse définie sur " + M(r"]0%s+\infty[" % SEMI) + " par " + M(r"f(x) = \frac{1}{x}") + ".\n\n"
            + lst(["Calculer " + M("f(%s)" % n(a1)) + " et " + M("f(%s)" % n(a2)) + ".", "Déterminer l'antécédent de " + M(n(c)) + " par $f$.",
                   "Comparer " + M("f(%s)" % n(small)) + " et " + M("f(%s)" % n(big)) + ". Que peut-on en déduire pour le sens de variation de $f$ ?"]),
            "Solution :\n\n" + lst([M("f(%s) = %s" % (n(a1), n(1 / a1))) + " et " + M("f(%s) = %s" % (n(a2), n(1 / a2))) + ".",
                                    M(r"f(x) = %s \Leftrightarrow \frac{1}{x} = %s \Leftrightarrow x = %s" % (n(c), n(c), n(1 / c))) + ".",
                                    M("f(%s) = %s > f(%s) = %s" % (n(small), n(1 / small), n(big), n(1 / big))) + " alors que " + M("%s < %s" % (n(small), n(big)))
                                    + " : l'ordre est inversé, ce qui illustre que $f$ est strictement décroissante sur " + M(r"]0%s+\infty[" % SEMI) + "."]))


# ───────────────────────── PREMIÈRE ─────────────────────────
def second(v):
    a, r1, r2 = [(1, 2, 3), (1, -1, 4), (2, 1, -3)][v]
    b, c = -a * (r1 + r2), a * r1 * r2
    D = b * b - 4 * a * c
    sd = isqrt(D)
    assert sd * sd == D and sorted([F(-b - sd, 2 * a), F(-b + sd, 2 * a)]) == sorted([F(r1), F(r2)])
    lo, hi = sorted([r1, r2])
    pos = a > 0
    return ("Soit $f$ la fonction définie sur " + M(R) + " par " + M("f(x) = " + poly([a, b, c])) + ".\n\n"
            + lst(["Calculer le discriminant $\\Delta$ de " + M("f(x)") + ".", "Résoudre l'équation " + M("f(x) = 0") + ".", "En déduire le signe de " + M("f(x)") + " selon les valeurs de $x$."]),
            "Solution :\n\n" + lst([M(r"\Delta = b^{2} - 4ac = %s^{2} - 4 \times %s \times %s = %d" % (par(b), par(a), par(c), D)) + ".",
                                    M(r"\Delta > 0") + " : deux racines " + M(r"x_1 = \frac{%s - %d}{%d} = %s" % (n(-b), sd, 2 * a, n(F(-b - sd, 2 * a)))) + " et "
                                    + M(r"x_2 = \frac{%s + %d}{%d} = %s" % (n(-b), sd, 2 * a, n(F(-b + sd, 2 * a)))) + ".",
                                    "Le coefficient de " + M("x^{2}") + " est %s : " % ("positif" if pos else "négatif") + M("f(x)") + " est %s à l'extérieur des racines et %s entre " % ("positif" if pos else "négatif", "négatif" if pos else "positif") + M(n(lo)) + " et " + M(n(hi)) + "."]))


def suite_arith(v):
    u0, r, t = [(3, 2, 50), (-4, 3, 100), (12, -2, None)][v]
    u10 = u0 + 10 * r
    S = F(11 * (u0 + u10), 2)
    assert S == sum(u0 + r * k for k in range(11))
    qs = ["Exprimer $u_n$ en fonction de $n$.", "Calculer $u_{10}$.", "Calculer " + M(r"S = u_0 + u_1 + \dots + u_{10}") + "."]
    ss = [M("u_n = u_0 + n \\times r = %s" % poly([r, u0], "n")) + ".", M("u_{10} = %s + 10 \\times %s = %s" % (n(u0), par(r), n(u10))) + ".",
          M(r"S = 11 \times \frac{u_0 + u_{10}}{2} = 11 \times \frac{%s%s}{2} = %s" % (n(u0), sg(u10), n(S))) + "."]
    if t is not None:
        k = (t - u0) // r + 1
        assert u0 + r * k > t >= u0 + r * (k - 1)
        qs.append("Déterminer le plus petit entier $n$ tel que " + M("u_n > %d" % t) + ".")
        ss.append(M(r"%s > %d \Leftrightarrow n > %s" % (poly([r, u0], "n"), t, n(F(t - u0, r)))) + " ; le plus petit entier est " + M("n = %d" % k) + " (" + M("u_{%d} = %d" % (k, u0 + r * k)) + ").")
    return ("Soit $(u_n)$ la suite arithmétique de premier terme " + M("u_0 = %s" % n(u0)) + " et de raison " + M("r = %s" % n(r)) + ".\n\n" + lst(qs), "Solution :\n\n" + lst(ss))


def deriv(v):
    a, b, c, d = [(1, -3, 0, 2), (2, 1, -4, 5), (-1, 4, 3, -2)][v]
    f1, fp1 = a + b + c + d, 3 * a + 2 * b + c
    qs = ["Calculer " + M("f'(x)") + ".", "Calculer " + M("f(1)") + " et " + M("f'(1)") + ".", "En déduire une équation de la tangente $T$ à la courbe de $f$ au point d'abscisse 1."]
    ss = [M("f'(x) = " + poly([3 * a, 2 * b, c])) + ".", M("f(1) = %s" % n(f1)) + " et " + M("f'(1) = %s" % n(fp1)) + ".",
          M("T : y = f'(1)(x - 1) + f(1) = %s(x - 1) + %s" % (n(fp1), n(f1))) + ", soit " + M("y = %s" % poly([fp1, f1 - fp1])) + "."]
    if v == 0:
        qs.append("Résoudre " + M("f'(x) = 0") + ".")
        ss.append(M(r"f'(x) = 3x^{2} - 6x = 3x(x - 2) = 0 \Leftrightarrow x = 0 \text{ ou } x = 2") + ".")
    return ("Soit $f$ la fonction définie sur " + M(R) + " par " + M("f(x) = " + poly([a, b, c, d])) + ".\n\n" + lst(qs), "Solution :\n\n" + lst(ss))


def variations(v):
    m = v + 1
    f = lambda x: x ** 3 - 3 * m * m * x
    assert f(-m) == 2 * m ** 3 and f(m) == -2 * m ** 3
    inf = r"-\infty"
    return ("Soit $f$ la fonction définie sur " + M(R) + " par " + M("f(x) = x^{3} - %dx" % (3 * m * m)) + ".\n\n"
            + lst(["Calculer " + M("f'(x)") + " et la factoriser.", "Étudier le signe de " + M("f'(x)") + " et dresser le tableau de variations de $f$.", "Préciser les extremums locaux de $f$."]),
            "Solution :\n\n" + lst([M("f'(x) = 3x^{2} - %d = 3(x - %d)(x + %d)" % (3 * m * m, m, m)) + ".",
                                    M("f'(x)") + " est positif pour " + M(r"x \leq -%d" % m) + " et pour " + M(r"x \geq %d" % m) + ", négatif entre " + M("-%d" % m) + " et " + M("%d" % m) + ". $f$ est donc croissante sur "
                                    + M(r"]%s%s-%d]" % (inf, SEMI, m)) + ", décroissante sur " + M(r"[-%d%s%d]" % (m, SEMI, m)) + ", croissante sur " + M(r"[%d%s+\infty[" % (m, SEMI)) + ".",
                                    "Maximum local " + M("f(-%d) = %d" % (m, 2 * m ** 3)) + " ; minimum local " + M("f(%d) = -%d" % (m, 2 * m ** 3)) + "."]))


def prodscal(v):
    (a, b), (c, d) = [((3, 4), (-4, 3)), ((2, 1), (1, 3)), ((2, 3), (1, 5))][v]
    dot, nu, nv = a * c + b * d, a * a + b * b, c * c + d * d
    U, V = r"\vec{u}", r"\vec{v}"
    qs = ["Calculer le produit scalaire " + M(r"\vec{u} \cdot \vec{v}") + ".", "Les vecteurs " + M(U) + " et " + M(V) + " sont-ils orthogonaux ?", "Calculer les normes " + M(r"\lVert \vec{u} \rVert") + " et " + M(r"\lVert \vec{v} \rVert") + "."]
    ss = [M(r"\vec{u} \cdot \vec{v} = %s \times %s + %s \times %s = %s" % (n(a), par(c), n(b), par(d), n(dot))) + ".",
          M(r"\vec{u} \cdot \vec{v} %s" % ("= 0" if dot == 0 else r"= %d \neq 0" % dot)) + (" : les vecteurs sont orthogonaux." if dot == 0 else " : ils ne sont pas orthogonaux."),
          M(r"\lVert \vec{u} \rVert = %s" % radeq(nu)) + " et " + M(r"\lVert \vec{v} \rVert = %s" % radeq(nv)) + "."]
    if dot != 0:
        th = degrees(acos(dot / sqrt(nu * nv)))
        qs.append("Déterminer l'angle géométrique $\\theta$ entre " + M(U) + " et " + M(V) + ", au dixième de degré près.")
        ss.append(M(r"\cos\theta = \frac{\vec{u} \cdot \vec{v}}{\lVert \vec{u} \rVert \times \lVert \vec{v} \rVert} = \frac{%d}{\sqrt{%d}} \approx %s" % (dot, nu * nv, dec(dot / sqrt(nu * nv), 4)))
                  + ", donc " + M(r"\theta \approx %s^\circ" % dec(th, 1)) + ".")
    return ("Dans un repère orthonormé, on considère les vecteurs " + M(U + pt(a, b)) + " et " + M(V + pt(c, d)) + ".\n\n" + lst(qs), "Solution :\n\n" + lst(ss))


TRIGO = {r"\cos x = \frac{1}{2}": r"\frac{\pi}{3} ; \frac{5\pi}{3}", r"\cos x = -\frac{1}{2}": r"\frac{2\pi}{3} ; \frac{4\pi}{3}",
         r"\cos x = \frac{\sqrt{2}}{2}": r"\frac{\pi}{4} ; \frac{7\pi}{4}", r"\cos x = -\frac{\sqrt{2}}{2}": r"\frac{3\pi}{4} ; \frac{5\pi}{4}",
         r"\sin x = \frac{1}{2}": r"\frac{\pi}{6} ; \frac{5\pi}{6}", r"\sin x = \frac{\sqrt{3}}{2}": r"\frac{\pi}{3} ; \frac{2\pi}{3}",
         r"\sin x = \frac{\sqrt{2}}{2}": r"\frac{\pi}{4} ; \frac{3\pi}{4}", r"\sin x = -\frac{1}{2}": r"\frac{7\pi}{6} ; \frac{11\pi}{6}"}


def trigo(v):
    eqs = [[r"\cos x = \frac{1}{2}"], [r"\sin x = \frac{\sqrt{3}}{2}", r"\cos x = -\frac{\sqrt{2}}{2}"],
           [r"\sin x = -\frac{1}{2}", r"\cos x = -\frac{1}{2}", r"\sin x = \frac{\sqrt{2}}{2}"]][v]
    return ("**Trigonométrie.** Résoudre dans l'intervalle " + M(r"[0%s2\pi]" % SEMI) + " les équations suivantes :\n\n" + lst([M(q) for q in eqs]),
            "Solution :\n\n" + lst([M(r"%s \Leftrightarrow x \in \left\{ %s \right\}" % (q, TRIGO[q])) + "." for q in eqs]))


def cond(v):
    p_, q_, r_ = [(F(2, 5), F(1, 2), F(1, 10)), (F(1, 3), F(3, 4), F(1, 2)), (F(3, 10), F(2, 3), F(1, 5))][v]
    pab = p_ * q_
    pb = pab + (1 - p_) * r_
    pba = pab / pb
    return ("Dans un lycée, une proportion " + M(n(p_)) + " des élèves est en classe de Première (événement $A$). Parmi ces élèves, une proportion " + M(n(q_))
            + " pratique un sport (événement $B$) ; parmi les autres élèves, une proportion " + M(n(r_)) + " pratique un sport. On choisit un élève au hasard.\n\n"
            + lst(["Calculer " + M(r"P(A \cap B)") + ".", "Calculer " + M("P(B)") + " à l'aide de la formule des probabilités totales.", "Sachant que l'élève pratique un sport, quelle est la probabilité qu'il soit en Première ?"]),
            "Solution :\n\n" + lst([M(r"P(A \cap B) = P(A) \times P_A(B) = %s \times %s = %s" % (n(p_), n(q_), n(pab))) + ".",
                                    M(r"P(B) = P(A \cap B) + P(\overline{A} \cap B) = %s + %s \times %s = %s" % (n(pab), n(1 - p_), n(r_), n(pb))) + ".",
                                    M(r"P_B(A) = \frac{P(A \cap B)}{P(B)} = \frac{%s}{%s} = %s" % (n(pab), n(pb), n(pba))) + "."]))


def binom_p(v):
    nn, p_, k = [(4, F(1, 2), 2), (5, F(1, 3), 2), (6, F(1, 4), 3)][v]
    pk = comb(nn, k) * p_ ** k * (1 - p_) ** (nn - k)
    p1 = 1 - (1 - p_) ** nn
    assert sum(comb(nn, j) * p_ ** j * (1 - p_) ** (nn - j) for j in range(nn + 1)) == 1
    return ("Soit $X$ une variable aléatoire suivant la loi binomiale " + M(r"\mathcal{B}(%d%s%s)" % (nn, SEMI, n(p_))) + ".\n\n"
            + lst(["Calculer " + M("P(X = %d)" % k) + ".", "Calculer " + M(r"P(X \geq 1)") + ".", "Calculer l'espérance " + M("E(X)") + "."]),
            "Solution :\n\n" + lst([M(r"P(X = %d) = \binom{%d}{%d} \left(%s\right)^{%d} \left(%s\right)^{%d} = %d \times %s \times %s = %s" % (k, nn, k, n(p_), k, n(1 - p_), nn - k, comb(nn, k), n(p_ ** k), n((1 - p_) ** (nn - k)), n(pk))) + ".",
                                    M(r"P(X \geq 1) = 1 - P(X = 0) = 1 - \left(%s\right)^{%d} = %s" % (n(1 - p_), nn, n(p1))) + ".",
                                    M(r"E(X) = n \times p = %d \times %s = %s" % (nn, n(p_), n(nn * p_))) + "."]))


def droite(v):
    A, B, C = [((1, 2), (3, 6), (4, 8)), ((-1, 3), (2, -3), (3, -4)), ((0, 5), (4, 2), (8, -1))][v]
    m = F(B[1] - A[1], B[0] - A[0])
    p_ = A[1] - m * A[0]
    assert B[1] == m * B[0] + p_
    inside = C[1] == m * C[0] + p_
    return ("Dans un repère orthonormé, on considère les points " + M("A" + pt(*A)) + ", " + M("B" + pt(*B)) + " et " + M("C" + pt(*C)) + ".\n\n"
            + lst(["Calculer le coefficient directeur de la droite " + M("(AB)") + ".", "Déterminer une équation réduite de " + M("(AB)") + ".", "Le point $C$ appartient-il à la droite " + M("(AB)") + " ?"]),
            "Solution :\n\n" + lst([M(r"m = \frac{y_B - y_A}{x_B - x_A} = \frac{%s - %s}{%s - %s} = %s" % (n(B[1]), par(A[1]), n(B[0]), par(A[0]), n(m))) + ".",
                                    M("y = %s" % poly([m, p_])) + " : en effet, $A$ appartient à la droite, donc " + M("%s = %s \\times %s + p" % (n(A[1]), n(m), par(A[0]))) + ", d'où " + M("p = %s" % n(p_)) + ".",
                                    "Pour " + M("x = %s" % n(C[0])) + " : " + M("%s \\times %s%s = %s" % (n(m), par(C[0]), sg(p_), n(m * C[0] + p_))) + (" " + M("= %s" % n(C[1])) + " : $C$ appartient à " + M("(AB)") + "." if inside
                                                                                                                                                   else " " + M(r"\neq %s" % n(C[1])) + " : $C$ n'appartient pas à " + M("(AB)") + ".")]))


def suite_def(v):
    a, b, c = [(1, 3, 0), (3, 0, -2), (-2, 0, 10)][v]
    u = lambda k: a * k * k + b * k + c
    diff = [2 * a, a + b]
    assert all(u(k + 1) - u(k) == diff[0] * k + diff[1] for k in range(10))
    pos = all(diff[0] * k + diff[1] > 0 for k in range(10))
    neg = all(diff[0] * k + diff[1] < 0 for k in range(10))
    assert pos or neg
    return ("Soit $(u_n)$ la suite définie pour tout entier naturel $n$ par " + M("u_n = " + poly([a, b, c], "n")) + ".\n\n"
            + lst(["Calculer $u_0$, $u_1$ et $u_2$.", "Exprimer " + M("u_{n+1} - u_n") + " en fonction de $n$.", "En déduire le sens de variation de la suite " + M("(u_n)") + "."]),
            "Solution :\n\n" + lst([M("u_0 = %d, \\quad u_1 = %d, \\quad u_2 = %d" % (u(0), u(1), u(2))) + ".", M("u_{n+1} - u_n = %s" % poly([diff[0], diff[1]], "n")) + ".",
                                    "Pour tout " + M(r"n \geq 0") + ", " + M(poly([diff[0], diff[1]], "n")) + " est %s : la suite " % ("strictement positif" if pos else "strictement négatif") + M("(u_n)") + " est strictement %s." % ("croissante" if pos else "décroissante")]))


def deriv_prod(v):
    a_, p_, q_ = [(1, 2, -3), (-2, 3, 1), (4, -1, 2)][v]
    f = lambda x: (x * x + a_) * (p_ * x + q_)
    coefs = [3 * p_, 2 * q_, a_ * p_]
    for x in range(-3, 4):
        h = 1e-6
        assert abs((f(x + h) - f(x - h)) / (2 * h) - (coefs[0] * x * x + coefs[1] * x + coefs[2])) < 1e-4
    fp1 = sum(coefs)
    uu = "x^{2}" + sg(a_)
    return ("Soit $f$ la fonction définie sur " + M(R) + " par " + M("f(x) = (%s)(%s)" % (uu, poly([p_, q_]))) + ".\n\n"
            + lst(["En utilisant la formule de dérivation d'un produit, calculer " + M("f'(x)") + ".", "Calculer " + M("f'(1)") + "."]),
            "Solution :\n\n" + lst(["$f = uv$ avec " + M("u(x) = " + uu) + " et " + M("v(x) = " + poly([p_, q_])) + " ; " + M("u'(x) = 2x") + " et " + M("v'(x) = %s" % n(p_)) + ". "
                                    + M("f'(x) = u'v + uv' = 2x(%s) + %s(%s) = %s" % (poly([p_, q_]), par(p_), uu, poly(coefs))) + ".",
                                    M("f'(1) = %s + %s + %s = %s" % (n(coefs[0]), par(coefs[1]), par(coefs[2]), n(fp1))) + "."]))


def suite_geo_p(v):
    u0, q, k, m_ = [(2, 3, 4, 5), (5, 2, 5, 6), (81, F(1, 3), 3, 4)][v]
    u0, q = F(u0), F(q)
    uk = u0 * q ** k
    S = sum(u0 * q ** i for i in range(m_ + 1))
    assert S == u0 * (1 - q ** (m_ + 1)) / (1 - q)
    return ("Soit $(u_n)$ la suite géométrique de premier terme " + M("u_0 = %s" % n(u0)) + " et de raison " + M("q = %s" % n(q)) + ".\n\n"
            + lst(["Exprimer $u_n$ en fonction de $n$.", "Calculer " + M("u_{%d}" % k) + ".", "Calculer " + M(r"S = u_0 + u_1 + \dots + u_{%d}" % m_) + "."]),
            "Solution :\n\n" + lst([M(r"u_n = u_0 \times q^{n} = %s \times \left(%s\right)^{n}" % (n(u0), n(q))) + ".", M(r"u_{%d} = %s \times \left(%s\right)^{%d} = %s" % (k, n(u0), n(q), k, n(uk))) + ".",
                                    M(r"S = u_0 \times \frac{1 - q^{%d}}{1 - q} = %s \times \frac{1 - \left(%s\right)^{%d}}{1 - %s} = %s" % (m_ + 1, n(u0), n(q), m_ + 1, par(q), n(S))) + "."]))


# ───────────────────────── TERMINALE ─────────────────────────
def recurrence(v):
    u0, a, b, form, her = [(1, 2, 1, "2^{n+1} - 1", r"u_{n+1} = 2\left(2^{n+1} - 1\right) + 1 = 2^{n+2} - 2 + 1 = 2^{n+2} - 1"),
                           (0, 2, 1, "2^{n} - 1", r"u_{n+1} = 2\left(2^{n} - 1\right) + 1 = 2^{n+1} - 2 + 1 = 2^{n+1} - 1"),
                           (2, 3, -2, "3^{n} + 1", r"u_{n+1} = 3\left(3^{n} + 1\right) - 2 = 3^{n+1} + 3 - 2 = 3^{n+1} + 1")][v]
    closed = [lambda k: 2 ** (k + 1) - 1, lambda k: 2 ** k - 1, lambda k: 3 ** k + 1][v]
    u = [u0]
    for _ in range(10):
        u.append(a * u[-1] + b)
    assert all(u[k] == closed(k) for k in range(11))
    rel = "u_{n+1} = %du_n %s" % (a, ("+ %d" % b) if b > 0 else ("- %d" % -b))
    return ("Soit $(u_n)$ la suite définie par " + M("u_0 = %d" % u0) + " et, pour tout entier naturel $n$, " + M(rel) + ".\n\n"
            + lst(["Calculer $u_1$, $u_2$ et $u_3$.", "Démontrer par récurrence que, pour tout entier naturel $n$, " + M("u_n = " + form) + "."]),
            "Solution :\n\n" + lst([M("u_1 = %d, \\quad u_2 = %d, \\quad u_3 = %d" % (u[1], u[2], u[3])) + ".",
                                    "**Initialisation** : pour " + M("n = 0") + ", " + M("%s = %d = u_0" % (form.replace("n", "0"), closed(0))) + " : la propriété est vraie.\n"
                                    "   **Hérédité** : supposons " + M("u_n = " + form) + " pour un entier $n$. Alors " + M(her) + ". La propriété est vraie au rang " + M("n+1") + ".\n"
                                    "   **Conclusion** : elle est vraie pour tout entier naturel $n$."]))


def suite_geo(v):
    u0, q = [(8, F(1, 2)), (5, F(1, 3)), (-6, F(2, 3))][v]
    u5 = u0 * q ** 5
    lim = F(u0) / (1 - q)
    assert abs(float(sum(u0 * q ** k for k in range(200))) - float(lim)) < 1e-9
    return ("Soit $(u_n)$ la suite géométrique de premier terme " + M("u_0 = %s" % n(u0)) + " et de raison " + M("q = %s" % n(q)) + ".\n\n"
            + lst(["Exprimer $u_n$ en fonction de $n$, puis calculer $u_5$.", "Déterminer la limite de " + M("(u_n)") + ".",
                   "Pour tout $n$, on pose " + M(r"S_n = u_0 + u_1 + \dots + u_n") + ". Exprimer $S_n$ en fonction de $n$ puis déterminer la limite de " + M("(S_n)") + "."]),
            "Solution :\n\n" + lst([M(r"u_n = %s \times \left(%s\right)^{n}" % (n(u0), n(q))) + " ; " + M(r"u_5 = %s \times \left(%s\right)^{5} = %s" % (n(u0), n(q), n(u5))) + ".",
                                    "Comme " + M("-1 < q < 1") + ", " + M("(q^{n})") + " tend vers 0, donc " + M("(u_n)") + " converge vers 0.",
                                    M(r"S_n = u_0 \times \frac{1 - q^{n+1}}{1 - q} = %s \left(1 - \left(%s\right)^{n+1}\right)" % (n(u0 / (1 - q)), n(q))) + ". Comme " + M("q^{n+1}") + " tend vers 0, " + M("S_n") + " tend vers " + M(n(lim)) + "."]))


def suite_lim(v):
    num, den, n0, lim = [((2, 1), (1, 3), 0, 2), ((3, 0, 1), (1, 1, 0), 1, 3), ((4, 7), (2, 1), 0, 2)][v]
    pol = lambda cs, k: sum(F(c) * k ** (len(cs) - 1 - i) for i, c in enumerate(cs))
    u = lambda k: pol(num, k) / pol(den, k)
    assert abs(float(u(10 ** 6)) - lim) < 1e-3
    deg = len(num) - 1
    nd = "n^{2}" if deg == 2 else "n"
    return ("Soit $(u_n)$ la suite définie pour tout entier " + M(r"n \geq %d" % n0) + " par " + M(r"u_n = \frac{%s}{%s}" % (poly(list(num), "n"), poly(list(den), "n"))) + ".\n\n"
            + lst(["Calculer " + M("u_{%d}" % n0) + " et " + M("u_{%d}" % (n0 + 1)) + ".", "Déterminer la limite de " + M("(u_n)") + " en factorisant numérateur et dénominateur par le terme de plus haut degré."]),
            "Solution :\n\n" + lst([M("u_{%d} = %s" % (n0, n(u(n0)))) + " et " + M("u_{%d} = %s" % (n0 + 1, n(u(n0 + 1)))) + ".",
                                    "On factorise par " + M(nd) + " au numérateur et au dénominateur : " + M(r"u_n = \frac{%s + \dots}{%s + \dots}" % (n(num[0]), n(den[0])))
                                    + " où les termes omis tendent vers 0. Donc " + M(r"\lim_{n \to +\infty} u_n = \frac{%s}{%s} = %s" % (n(num[0]), n(den[0]), n(lim))) + "."]))


def limites(v):
    a, b, c, d = [(2, 1, 1, -3), (3, -2, 2, 4), (-1, 5, 4, -2)][v]
    assert a * d - b * c != 0
    x0 = F(-d, c)
    lim = F(a, c)
    nume, deno = poly([a, b]), poly([c, d])
    return ("Soit $f$ la fonction définie sur " + M(r"\R \setminus \{%s\}" % n(x0)) + " par " + M(r"f(x) = \frac{%s}{%s}" % (nume, deno)) + ".\n\n"
            + lst(["Déterminer la limite de $f$ en " + M(r"+\infty") + ". Que peut-on en déduire pour la courbe de $f$ ?", "Justifier que la droite d'équation " + M("x = %s" % n(x0)) + " est asymptote verticale à la courbe."]),
            "Solution :\n\n" + lst(["Pour " + M(r"x \neq 0") + ", " + M(r"f(x) = \frac{%s %s \frac{%s}{x}}{%s %s \frac{%s}{x}}" % (n(a), "+" if b >= 0 else "-", n(abs(F(b))), n(c), "+" if d >= 0 else "-", n(abs(F(d)))))
                                    + " ; donc " + M(r"\lim_{x \to +\infty} f(x) = %s" % n(lim)) + ". La droite d'équation " + M("y = %s" % n(lim)) + " est asymptote horizontale à la courbe en " + M(r"+\infty") + ".",
                                    "Le dénominateur s'annule en " + M("x = %s" % n(x0)) + " alors que le numérateur y vaut " + M(n(a * x0 + b)) + r" $\neq 0$ : " + M("f(x)") + " tend vers " + M(r"\pm\infty")
                                    + " quand $x$ se rapproche de " + M(n(x0)) + ", donc la droite " + M("x = %s" % n(x0)) + " est asymptote verticale."]))


def expo(v):
    a = v
    mn = -e ** (-(a + 1))
    assert abs(((-a - 1) + a) * exp(-a - 1) - mn) < 1e-12
    fx = r"x\,\mathrm{e}^{x}" if a == 0 else r"(x + %d)\mathrm{e}^{x}" % a
    u = "x" if a == 0 else "x + %d" % a
    return ("Soit $f$ la fonction définie sur " + M(R) + " par " + M("f(x) = " + fx) + ".\n\n"
            + lst(["Calculer " + M("f'(x)") + " et montrer que " + M(r"f'(x) = (x + %d)\mathrm{e}^{x}" % (a + 1)) + ".", "Étudier le signe de " + M("f'(x)") + " et dresser le tableau de variations de $f$.",
                   "En déduire le minimum de $f$ ; donner une valeur approchée à " + M("10^{-3}") + " près."]),
            "Solution :\n\n" + lst(["$f = uv$ avec " + M("u(x) = " + u) + " et " + M(r"v(x) = \mathrm{e}^{x}") + " : " + M(r"f'(x) = 1 \times \mathrm{e}^{x} + %s\mathrm{e}^{x} = (x + %d)\mathrm{e}^{x}" % (("x" if a == 0 else "(%s)" % u), a + 1)) + ".",
                                    M(r"\mathrm{e}^{x} > 0") + ", donc " + M("f'(x)") + " a le signe de " + M("x + %d" % (a + 1)) + " : $f$ est décroissante sur " + M(r"]-\infty%s-%d]" % (SEMI, a + 1))
                                    + " et croissante sur " + M(r"[-%d%s+\infty[" % (a + 1, SEMI)) + ".",
                                    "Le minimum est " + M(r"f(-%d) = -\mathrm{e}^{-%d} \approx %s" % (a + 1, a + 1, dec(mn, 3))) + "."]))


def ln_(v):
    k, a, b = [(5, 1, 7), (12, 2, 9), (20, 3, 11)][v]
    return ("**Exponentielle et logarithme.** Résoudre dans " + M(R) + " :\n\n"
            + lst([M(r"\mathrm{e}^{x} = %d" % k), M(r"\ln(x + %d) = \ln(%d)" % (a, b)) + " (on précisera l'ensemble de définition)", M(r"\mathrm{e}^{x} \geq %d" % k)]),
            "Solution :\n\n" + lst([M(r"\mathrm{e}^{x} = %d \Leftrightarrow x = \ln(%d) \approx %s" % (k, k, dec(log(k), 3))) + ".",
                                    "L'équation a un sens pour " + M("x + %d > 0" % a) + ", soit " + M("x > -%d" % a) + ". Alors " + M(r"x + %d = %d \Leftrightarrow x = %d" % (a, b, b - a)) + ", valeur bien supérieure à " + M("-%d" % a) + ".",
                                    "La fonction " + M(r"\ln") + " est croissante : " + M(r"\mathrm{e}^{x} \geq %d \Leftrightarrow x \geq \ln(%d)" % (k, k)) + ". Ensemble des solutions : " + M(r"[\ln(%d)%s+\infty[" % (k, SEMI)) + "."]))


def integrale(v):
    a, b, c = [(3, 2, 1), (6, -4, 5), (4, 3, -2)][v]
    val = F(a, 3) + F(b, 2) + c
    return ("Soit $f$ la fonction définie sur " + M(R) + " par " + M("f(x) = " + poly([a, b, c])) + ".\n\n"
            + lst(["Déterminer une primitive $F$ de $f$ sur " + M(R) + ".", "Calculer l'intégrale " + M(r"I = \int_0^1 f(x)\,\mathrm{d}x") + "."]),
            "Solution :\n\n" + lst([M("F(x) = " + poly([F(a, 3), F(b, 2), c, 0])) + ".", M("I = F(1) - F(0) = %s - 0 = %s" % (n(val), n(val))) + "."]))


def diffeq(v):
    a, b, y0, x1 = [(F(2), 0, 3, 1), (F(-1, 2), 0, 4, 2), (F(2), 4, 1, 1)][v]
    C = F(y0) + F(b) / a
    part = -F(b) / a
    y = lambda x: float(C) * exp(float(a) * x) + float(part)
    assert abs(y(0) - y0) < 1e-12
    cst = (" + %s" % n(part) if part > 0 else " - %s" % n(abs(part))) if b else ""
    rel = "y' = %s y" % par(a) + (" + %d" % b if b else "")
    E = r"\mathrm{e}^{%s}"
    ex1 = F(a * x1)
    gen = ("Les solutions de " + M("y' = ay") + " sont les fonctions " + M(r"y(x) = C\,\mathrm{e}^{ax}") + ". " if not b else
           "Une solution constante est " + M("y = -\\frac{b}{a} = %s" % n(part)) + " ; les solutions sont " + M(r"y(x) = C\,\mathrm{e}^{%s}%s" % (ex(a), cst)) + ". ")
    coef = "" if C == 1 else n(C)
    return ("On considère le problème : " + M(rel + ", \\quad y(0) = %d" % y0) + ".\n\n"
            + lst(["Déterminer la solution $y$ de ce problème.", "Calculer " + M("y(%d)" % x1) + " (valeur approchée à " + M("10^{-2}") + " près)."]),
            "Solution :\n\n" + lst([gen + "La condition " + M("y(0) = %d" % y0) + " donne " + M("C = %s" % n(C)) + ". Donc " + M(r"y(x) = %s\mathrm{e}^{%s}%s" % (coef, ex(a), cst)) + ".",
                                    M(r"y(%d) = %s\mathrm{e}^{%s}%s \approx %s" % (x1, coef, n(ex1), cst, dec(y(x1), 2))) + "."]))


def espace(v):
    (a, b, c, d), A = [((2, -1, 3, -5), (1, 0, 1)), ((1, 2, -1, -3), (2, 1, 3)), ((3, -2, 1, -4), (1, -1, -1))][v]
    val = a * A[0] + b * A[1] + c * A[2] + d
    eq = lin([(a, "x"), (b, "y"), (c, "z")], d) + " = 0"
    check = "%s \\times %s %s %s \\times %s %s %s \\times %s%s = %s" % (n(a), par(A[0]), "-" if b < 0 else "+", n(abs(b)), par(A[1]), "-" if c < 0 else "+", n(abs(c)), par(A[2]), sg(d), n(val))
    qs = ["Donner un vecteur normal au plan $P$.", "Le point " + M("A" + pt(*A)) + " appartient-il à $P$ ?", "Donner une représentation paramétrique de la droite $D$ perpendiculaire à $P$ passant par $A$."]
    sysp = r"\begin{cases} x = %s \\ y = %s \\ z = %s \end{cases}" % (par_t(A[0], a), par_t(A[1], b), par_t(A[2], c))
    ss = ["Un vecteur normal est " + M(r"\vec{n}" + pt(a, b, c)) + ".",
          M(check) + (" : $A$ appartient à $P$." if val == 0 else r" " + M(r"\neq 0") + " : $A$ n'appartient pas à $P$."),
          "$D$ est dirigée par " + M(r"\vec{n}") + " : " + M(sysp) + ", avec " + M(r"t \in \R") + "."]
    if val != 0:
        qs.append("Calculer la distance du point $A$ au plan $P$.")
        ss.append(M(r"d(A, P) = \frac{|%s|}{\sqrt{%d + %d + %d}} = \frac{%d}{\sqrt{%d}} \approx %s" % (n(val), a * a, b * b, c * c, abs(val), a * a + b * b + c * c, dec(abs(val) / sqrt(a * a + b * b + c * c), 3))) + ".")
    return ("L'espace est muni d'un repère orthonormé. Le plan $P$ a pour équation " + M(eq) + ".\n\n" + lst(qs), "Solution :\n\n" + lst(ss))


def vec_espace(v):
    A, B, C = [((1, 2, 3), (3, -1, 4), (5, -4, 5)), ((0, 1, -2), (2, 3, 0), (1, 2, 1)), ((-1, 0, 2), (1, 2, 6), (2, 3, 8))][v]
    AB = tuple(B[i] - A[i] for i in range(3))
    AC = tuple(C[i] - A[i] for i in range(3))
    k = next(F(AC[i], AB[i]) for i in range(3) if AB[i] != 0)
    aligned = all(AC[i] == k * AB[i] for i in range(3))
    nn = sum(c * c for c in AB)
    return ("L'espace est muni d'un repère orthonormé. On considère les points " + M("A" + pt(*A)) + ", " + M("B" + pt(*B)) + " et " + M("C" + pt(*C)) + ".\n\n"
            + lst(["Calculer les coordonnées du vecteur " + M(r"\overrightarrow{AB}") + ", puis la distance " + M("AB") + ".", "Les points $A$, $B$ et $C$ sont-ils alignés ?"]),
            "Solution :\n\n" + lst([M(r"\overrightarrow{AB}" + pt(*AB)) + " et " + M(r"AB = \sqrt{%s} = %s" % (" + ".join("%s^{2}" % par(c) for c in AB), radeq(nn))) + ".",
                                    M(r"\overrightarrow{AC}" + pt(*AC)) + ". " + ("On a " + M(r"\overrightarrow{AC} = %s \overrightarrow{AB}" % n(k)) + " : les vecteurs sont colinéaires, donc $A$, $B$ et $C$ sont alignés." if aligned
                                                                                  else "Les coordonnées de " + M(r"\overrightarrow{AC}") + " et " + M(r"\overrightarrow{AB}") + " ne sont pas proportionnelles : les vecteurs ne sont pas colinéaires, donc $A$, $B$ et $C$ ne sont pas alignés.")]))


def complexes(v):
    (a, b), (c, d) = [((1, 2), (3, -1)), ((-2, 3), (1, 1)), ((3, -4), (2, 1))][v]
    z1, z2 = complex(a, b), complex(c, d)
    den = c * c + d * d
    qr, qi = F(a * c + b * d, den), F(b * c - a * d, den)
    assert abs(z1 * z2 - complex(a * c - b * d, a * d + b * c)) < 1e-12 and abs(z1 / z2 - complex(float(qr), float(qi))) < 1e-12
    mod = a * a + b * b
    return ("On considère les nombres complexes " + M("z_1 = " + cx(a, b)) + " et " + M("z_2 = " + cx(c, d)) + ".\n\n"
            + lst(["Calculer " + M("z_1 + z_2") + " et " + M(r"z_1 \times z_2") + ".", "Calculer le module de " + M("z_1") + ".", "Écrire le quotient " + M(r"\frac{z_1}{z_2}") + " sous forme algébrique."]),
            "Solution :\n\n" + lst([M("z_1 + z_2 = " + cx(a + c, b + d)) + " et " + M(r"z_1 \times z_2 = " + cx(a * c - b * d, a * d + b * c)) + ".",
                                    M(r"|z_1| = \sqrt{%s^{2} + %s^{2}} = %s" % (par(a), par(b), radeq(mod))) + ".",
                                    M(r"\frac{z_1}{z_2} = \frac{z_1 \times \overline{z_2}}{|z_2|^{2}} = \frac{(%s)(%s)}{%d} = %s" % (cx(a, b), cx(c, -d), den, cx(qr, qi))) + "."]))


def binom_t(v):
    nn, p_, k = [(10, 0.3, 3), (8, 0.5, 4), (12, 0.2, 2)][v]
    pk = comb(nn, k) * p_ ** k * (1 - p_) ** (nn - k)
    p1 = 1 - (1 - p_) ** nn
    return ("Un test comporte %d questions indépendantes ; pour chacune, la probabilité de répondre correctement au hasard est " % nn + M(dec(p_, 1)) + ". On note $X$ le nombre de bonnes réponses.\n\n"
            + lst(["Justifier que $X$ suit une loi binomiale dont on précisera les paramètres.", "Calculer " + M("P(X = %d)" % k) + " à " + M("10^{-4}") + " près.",
                   "Calculer la probabilité d'obtenir au moins une bonne réponse (à " + M("10^{-4}") + " près).", "Calculer " + M("E(X)") + "."]),
            "Solution :\n\n" + lst(["On répète %d fois la même épreuve de Bernoulli (succès de probabilité " % nn + M(dec(p_, 1)) + ") de façon indépendante : " + M(r"X \sim \mathcal{B}(%d%s%s)" % (nn, SEMI, dec(p_, 1))) + ".",
                                    M(r"P(X = %d) = \binom{%d}{%d} \times %s^{%d} \times %s^{%d} \approx %s" % (k, nn, k, dec(p_, 1), k, dec(1 - p_, 1), nn - k, dec(pk, 4))) + ".",
                                    M(r"P(X \geq 1) = 1 - %s^{%d} \approx %s" % (dec(1 - p_, 1), nn, dec(p1, 4))) + ".", M(r"E(X) = %d \times %s = %s" % (nn, dec(p_, 1), dec(nn * p_, 1))) + "."]))


def denombrement(v):
    w, h, k, j = [(6, 4, 3, 2), (7, 5, 4, 2), (8, 6, 5, 3)][v]
    tot, exa, al = comb(w + h, k), comb(w, j) * comb(h, k - j), comb(w + h, k) - comb(h, k)
    return ("Un comité de %d personnes est choisi parmi %d candidats : %d femmes et %d hommes.\n\n" % (k, w + h, w, h)
            + lst(["Combien de comités différents peut-on former ?", "Combien de comités comportent exactement %d femmes ?" % j, "Combien de comités comportent au moins une femme ?"]),
            "Solution :\n\n" + lst([M(r"\binom{%d}{%d} = %d" % (w + h, k, tot)) + ".", M(r"\binom{%d}{%d} \times \binom{%d}{%d} = %d \times %d = %d" % (w, j, h, k - j, comb(w, j), comb(h, k - j), exa)) + ".",
                                    "Total moins les comités sans femme : " + M(r"%d - \binom{%d}{%d} = %d - %d = %d" % (tot, h, k, tot, comb(h, k), al)) + "."]))


def synthese(v):
    E = r"\mathrm{e}"
    if v < 2:
        a = v + 1
        fx = r"x\,%s^{-x}" % E if a == 1 else r"x\,%s^{-2x}" % E
        x0, fm = F(1, a), 1 / (a * e)
        cc = "" if a == 1 else "2"
        ea = r"%s^{-%sx}" % (E, cc)
        return ("**Problème.** Soit $f$ la fonction définie sur " + M(R) + " par " + M("f(x) = " + fx) + ".\n\n"
                + lst(["Déterminer la limite de $f$ en " + M(r"-\infty") + ", puis en " + M(r"+\infty") + " (on admettra que " + M(r"\lim_{x \to +\infty} %s = 0" % fx) + ").",
                       "Calculer " + M("f'(x)") + " et dresser le tableau de variations de $f$.", "En déduire que $f$ admet un maximum et donner sa valeur exacte, puis une valeur approchée à " + M("10^{-3}") + " près."]),
                "Solution :\n\n" + lst(["En " + M(r"-\infty") + " : " + M(r"x \to -\infty") + " et " + M(ea + r" \to +\infty") + ", donc " + M(r"f(x) \to -\infty") + ". En " + M(r"+\infty") + " : " + M(r"f(x) \to 0") + ".",
                                        M(r"f'(x) = %s - %sx\,%s = (1 - %sx)%s" % (ea, cc, ea, cc, ea)) + ". Elle est positive pour " + M("x < %s" % n(x0)) + " et négative ensuite : $f$ est croissante sur "
                                        + M(r"]-\infty%s%s]" % (SEMI, n(x0))) + " et décroissante sur " + M(r"[%s%s+\infty[" % (n(x0), SEMI)) + ".",
                                        "$f$ admet un maximum en " + M("x = %s" % n(x0)) + " : " + M(r"f\left(%s\right) = %s%s^{-1} = %s \approx %s" % (n(x0), "" if a == 1 else r"\frac{1}{2}", E, r"\frac{1}{%s}" % ("e" if a == 1 else "2e"), dec(fm, 3))) + "."]))
    return ("**Problème.** Soit $f$ la fonction définie sur " + M(R) + " par " + M(r"f(x) = x^{2}\,%s^{-x}" % E) + ".\n\n"
            + lst(["Déterminer la limite de $f$ en " + M(r"-\infty") + " (on admettra que " + M(r"\lim_{x \to +\infty} x^{2}%s^{-x} = 0" % E) + ").", "Montrer que " + M(r"f'(x) = x(2 - x)%s^{-x}" % E) + ".",
                   "Dresser le tableau de variations de $f$.", "Préciser les extremums locaux (valeurs exactes puis approchées à " + M("10^{-3}") + " près)."]),
            "Solution :\n\n" + lst(["En " + M(r"-\infty") + " : " + M(r"x^{2} \to +\infty") + " et " + M(r"%s^{-x} \to +\infty" % E) + ", donc " + M(r"f(x) \to +\infty") + ". En " + M(r"+\infty") + " : " + M(r"f(x) \to 0") + ".",
                                    M(r"f'(x) = 2x\,%s^{-x} - x^{2}%s^{-x} = x(2 - x)%s^{-x}" % (E, E, E)) + ".",
                                    M(r"%s^{-x} > 0" % E) + " : " + M("f'") + " a le signe de " + M("x(2 - x)") + ". $f$ est décroissante sur " + M(r"]-\infty%s0]" % SEMI) + ", croissante sur " + M(r"[0%s2]" % SEMI) + ", décroissante sur " + M(r"[2%s+\infty[" % SEMI) + ".",
                                    "Minimum local " + M("f(0) = 0") + " ; maximum local " + M(r"f(2) = 4%s^{-2} \approx %s" % (E, dec(4 * exp(-2), 3))) + "."]))


# ───────────────────────── PHYSIQUE-CHIMIE (formules moléculaires, ions, équations-bilans, unités) ─────────────────────────
MASSES = {"H": 1.0, "C": 12.0, "N": 14.0, "O": 16.0, "Na": 23.0, "Cl": 35.5}
U_MOL = r"\pu{g.mol-1}"


def molar(comp: dict) -> float:
    return sum(MASSES[a] * k for a, k in comp.items())


def donnees(*atoms) -> str:
    return " ; ".join(M(r"M(\ce{%s}) = %s\,%s" % (a, dec(MASSES[a], 1), U_MOL)) for a in atoms)


def qte_matiere(v):
    f, comp, m_ = [("H2O", {"H": 2, "O": 1}, 36.0), ("CO2", {"C": 1, "O": 2}, 88.0), ("C6H12O6", {"C": 6, "H": 12, "O": 6}, 90.0)][v]
    Mm = molar(comp)
    nn = m_ / Mm
    detail = " + ".join("%s \\times %s" % (k, dec(MASSES[a], 1)) for a, k in comp.items())
    return ("On donne les masses molaires atomiques : " + donnees(*comp) + ".\n\n"
            + lst(["Calculer la masse molaire moléculaire de " + M(r"\ce{%s}" % f) + ".", "Calculer la quantité de matière $n$ contenue dans " + M(r"%s\,\pu{g}" % dec(m_, 1)) + " de ce composé."]),
            "Solution :\n\n" + lst([M(r"M(\ce{%s}) = %s = %s\,%s" % (f, detail.replace(" + ", " + "), dec(Mm, 1), U_MOL)) + ".",
                                    M(r"n = \frac{m}{M} = \frac{%s}{%s} = %s\,\pu{mol}" % (dec(m_, 1), dec(Mm, 1), dec(nn, 2))) + "."]))


def concentration(v):
    f, comp, m_, vml, eq = [("NaCl", {"Na": 1, "Cl": 1}, 5.85, 250, r"\ce{NaCl(s) -> Na+(aq) + Cl-(aq)}"),
                            ("NaOH", {"Na": 1, "O": 1, "H": 1}, 4.0, 500, r"\ce{NaOH(s) -> Na+(aq) + HO-(aq)}"),
                            ("C6H12O6", {"C": 6, "H": 12, "O": 6}, 9.0, 100, r"\ce{C6H12O6(s) -> C6H12O6(aq)}")][v]
    Mm = molar(comp)
    nn = m_ / Mm
    c = nn / (vml / 1000)
    return ("On dissout " + M(r"%s\,\pu{g}" % dec(m_, 2 if m_ < 10 and v == 0 else 1)) + " de " + M(r"\ce{%s}" % f) + " dans de l'eau pour obtenir " + M(r"%d\,\pu{mL}" % vml) + " de solution. Masses molaires atomiques : " + donnees(*comp) + ".\n\n"
            + lst(["Écrire l'équation de la dissolution du composé dans l'eau.", "Calculer la quantité de matière " + M("n") + " de soluté dissoute.", "En déduire la concentration en quantité de matière " + M("c") + " de la solution, en " + M(r"\pu{mol.L-1}") + "."]),
            "Solution :\n\n" + lst([M(eq) + ".", M(r"M = %s\,%s \quad ; \quad n = \frac{m}{M} = \frac{%s}{%s} = %s\,\pu{mol}" % (dec(Mm, 1), U_MOL, dec(m_, 2 if v == 0 else 1), dec(Mm, 1), dec(nn, 3))) + ".",
                                    M(r"c = \frac{n}{V} = \frac{%s}{%s} = %s\,\pu{mol.L-1}" % (dec(nn, 3), dec(vml / 1000, 3), dec(c, 3))) + "."]))


def equilibrage(v):
    brute, bonne, atomes, n0, ratio, nO2 = [
        (r"\ce{CH4 + O2 -> CO2 + H2O}", r"\ce{CH4 + 2O2 -> CO2 + 2H2O}", r"carbone : 1 = 1 ; hydrogène : 4 = 2 \times 2 ; oxygène : 2 \times 2 = 2 + 2", "2,0", F(2), "4,0"),
        (r"\ce{C3H8 + O2 -> CO2 + H2O}", r"\ce{C3H8 + 5O2 -> 3CO2 + 4H2O}", r"carbone : 3 = 3 ; hydrogène : 8 = 4 \times 2 ; oxygène : 5 \times 2 = 3 \times 2 + 4", "0,50", F(5), "2,5"),
        (r"\ce{C4H10 + O2 -> CO2 + H2O}", r"\ce{2C4H10 + 13O2 -> 8CO2 + 10H2O}", r"carbone : 2 \times 4 = 8 ; hydrogène : 2 \times 10 = 10 \times 2 ; oxygène : 13 \times 2 = 8 \times 2 + 10", "4,0", F(13, 2), "26"),
    ][v]
    gaz = [("méthane", r"\ce{CH4}"), ("propane", r"\ce{C3H8}"), ("butane", r"\ce{C4H10}")][v]
    n0f = float(n0.replace(",", "."))
    assert abs(float(ratio) * n0f - float(nO2.replace(",", "."))) < 1e-9
    return ("La combustion complète du %s (%s) dans le dioxygène produit du dioxyde de carbone et de l'eau. Son équation, non ajustée, s'écrit : " % (gaz[0], M(gaz[1])) + M(brute) + ".\n\n"
            + lst(["Ajuster cette équation de réaction.", "Quelle quantité de dioxygène faut-il pour brûler " + M(r"%s\,\pu{mol}" % n0) + " de " + gaz[0] + " ?"]),
            "Solution :\n\n" + lst(["Équation ajustée : " + M(bonne) + ". Vérification — " + M(atomes) + ".",
                                    "D'après les nombres stœchiométriques, " + M(r"n(\ce{O2}) = %s \times n(%s) = %s \times %s = %s\,\pu{mol}" % (n(ratio), gaz[1].replace(r"\ce", r"\ce"), n(ratio), n0, nO2)) + "."]))


def ph(v):
    h, kind = [(1.0e-3, "acide"), (2.5e-4, "acide"), (1.0e-11, "basique")][v]
    val = -log10(h)
    mant, exp10 = f"{h:.1e}".split("e")
    mant = mant.replace(".", "{,}")
    e10 = int(exp10)
    return ("La concentration en ions oxonium d'une solution aqueuse vaut " + M(r"[\ce{H3O+}] = %s \times 10^{%d}\,\pu{mol.L-1}" % (mant, e10)) + ".\n\n"
            + lst(["Calculer le pH de cette solution (à " + M("0{,}1") + " près).", "La solution est-elle acide, neutre ou basique ? Justifier."]),
            "Solution :\n\n" + lst([M(r"\mathrm{pH} = -\log\left([\ce{H3O+}]\right) = -\log\left(%s \times 10^{%d}\right) \approx %s" % (mant, e10, dec(val, 1))) + ".",
                                    "Le pH est %s à 7 : la solution est %s." % ("inférieur" if kind == "acide" else "supérieur", kind)]))


def vitesse(v):
    d, t = [(120, 1.5), (45, 0.5), (210, 2.5)][v]
    vkm = d / t
    vms = vkm / 3.6
    return ("Un véhicule parcourt " + M(r"%s\,\pu{km}" % dec(d, 0)) + " en " + M(r"%s\,\pu{h}" % dec(t, 1)) + " à vitesse constante.\n\n"
            + lst(["Calculer sa vitesse " + M("v") + " en " + M(r"\pu{km.h-1}") + ".", "Convertir cette vitesse en " + M(r"\pu{m.s-1}") + "."]),
            "Solution :\n\n" + lst([M(r"v = \frac{d}{t} = \frac{%s}{%s} = %s\,\pu{km.h-1}" % (dec(d, 0), dec(t, 1), dec(vkm, 1))) + ".",
                                    M(r"v = \frac{%s}{3{,}6} \approx %s\,\pu{m.s-1}" % (dec(vkm, 1), dec(vms, 1))) + "."]))


def ohm(v):
    r_, i = [(100, 0.050), (220, 0.020), (47, 0.30)][v]
    u = r_ * i
    p = u * i
    return ("Un conducteur ohmique de résistance " + M(r"R = %d\,\Omega" % r_) + " est parcouru par un courant d'intensité " + M(r"I = %s\,\pu{A}" % dec(i, 3 if v < 2 else 2)) + ".\n\n"
            + lst(["Calculer la tension " + M("U") + " à ses bornes, en volts.", "Calculer la puissance " + M("P") + " dissipée par effet Joule, en watts."]),
            "Solution :\n\n" + lst([M(r"U = R \times I = %d \times %s = %s\,\pu{V}" % (r_, dec(i, 3 if v < 2 else 2), dec(u, 2 if v else 1))) + " (loi d'Ohm).",
                                    M(r"P = U \times I = %s \times %s \approx %s\,\pu{W}" % (dec(u, 2 if v else 1), dec(i, 3 if v < 2 else 2), dec(p, 3 if v else 2))) + "."]))


def energie(v):
    m_, vit = [(1200, 20), (800, 25), (70, 10)][v]
    ec = 0.5 * m_ * vit ** 2
    mant, exp10 = f"{ec:.1e}".split("e")
    return ("Un véhicule de masse " + M(r"m = %d\,\pu{kg}" % m_) + " roule à la vitesse " + M(r"v = %d\,\pu{m.s-1}" % vit) + ".\n\n"
            + lst(["Calculer son énergie cinétique " + M(r"E_\mathrm{c} = \frac{1}{2} m v^{2}") + " (résultat en notation scientifique).", "Par quel facteur l'énergie cinétique est-elle multipliée lorsque la vitesse double ?"]),
            "Solution :\n\n" + lst([M(r"E_\mathrm{c} = \frac{1}{2} \times %d \times %d^{2} = %s\,\pu{J} = %s \times 10^{%d}\,\pu{J}" % (m_, vit, dec(ec, 0), mant.replace(".", "{,}"), int(exp10))) + ".",
                                    "L'énergie cinétique est proportionnelle à " + M("v^{2}") + " : si " + M("v") + " double, " + M(r"E_\mathrm{c}") + " est multipliée par " + M(r"2^{2} = 4") + "."]))


def desintegration(v):
    th, t = [(8, 16), (5, 15), (3, 12)][v]
    k = t // th
    assert k * th == t
    frac = F(1, 2 ** k)
    return ("Un échantillon radioactif contient initialement " + M("N_0") + " noyaux. La demi-vie de l'isotope est " + M(r"t_{1/2} = %d\,\pu{jours}" % th) + ". On rappelle que " + M(r"N(t) = N_0 \left(\frac{1}{2}\right)^{t/t_{1/2}}") + ".\n\n"
            + lst(["Combien de demi-vies se sont écoulées au bout de " + M(r"%d\,\pu{jours}" % t) + " ?", "Quelle fraction de " + M("N_0") + " reste-t-il à cet instant ?", "Exprimer ce résultat en pourcentage."]),
            "Solution :\n\n" + lst([M(r"\frac{t}{t_{1/2}} = \frac{%d}{%d} = %d" % (t, th, k)) + " demi-vies.", M(r"N(t) = N_0 \left(\frac{1}{2}\right)^{%d} = \frac{N_0}{%d}" % (k, 2 ** k)) + ".",
                                    M(r"\frac{1}{%d} = %s\,\%%" % (2 ** k, dec(100 / 2 ** k, 2))) + "."]))


def _mol(style: str, *lignes: str) -> str:
    return "```mol %s\n%s\n```" % (style, "\n".join(lignes))


def semi_developpee(v):
    smi, nom, semi, groupe, familles, brute = [("CCO", "éthanol", r"\ce{CH3-CH2-OH}", "hydroxyle", "alcools", "C2H6O"),
                                               ("CC(O)C", "propan-2-ol", r"\ce{CH3-CH(OH)-CH3}", "hydroxyle", "alcools", "C3H8O"),
                                               ("CCC(=O)O", "acide propanoïque", r"\ce{CH3-CH2-COOH}", "carboxyle", "acides carboxyliques", "C3H6O2")][v]
    cet = ("de l'" if nom[0] in "aeiouéè" else "du ") + nom
    assert chem.formule_brute(smi) == brute
    return ("On considère la molécule représentée ci-dessous en formule topologique.\n\n" + _mol("topologique", smi) + "\n\n"
            + lst(["Déterminer sa formule brute.", "Écrire sa formule semi-développée.", "Nommer le groupe caractéristique présent et en déduire la famille de composés."]),
            "Solution :\n\n" + lst(["Chaque sommet et chaque extrémité de ligne est un atome de carbone, complété par des atomes d'hydrogène : " + M(r"\ce{%s}" % brute) + ".",
                                    "Formule semi-développée : " + M(semi) + " (les liaisons entre les atomes de carbone et avec le groupe caractéristique sont conservées, celles avec l'hydrogène sont omises).",
                                    "Le groupe %s caractérise la famille des %s. Il s'agit %s." % (groupe, familles, cet)])
            + "\n\nFormule développée (toutes les liaisons) :\n\n" + _mol("developpee", smi))


def isomeres(v):
    a, na, b, nb, kind, detail = [("CCCCO", "butan-1-ol", "CCC(C)O", "butan-2-ol", "isomères de position", "le groupe hydroxyle est porté par un carbone différent"),
                                  ("CCO", "éthanol", "COC", "méthoxyméthane", "isomères de fonction", "la première molécule est un alcool, la seconde un éther"),
                                  ("CCCCC", "pentane", "CC(C)CC", "2-méthylbutane", "isomères de chaîne", "le squelette carboné est linéaire dans un cas et ramifié dans l'autre")][v]
    fa, fb = chem.formule_brute(a), chem.formule_brute(b)
    assert fa == fb
    return ("On considère les deux molécules suivantes, représentées en formule topologique.\n\n" + _mol("topologique", a + " molécule A", b + " molécule B") + "\n\n"
            + lst(["Déterminer la formule brute de chacune des molécules.", "Ces deux molécules sont-elles isomères ? Justifier.", "Préciser le type d'isomérie."]),
            "Solution :\n\n" + lst(["Molécule A : " + M(r"\ce{%s}" % fa) + " ; molécule B : " + M(r"\ce{%s}" % fb) + ".",
                                    "Les deux molécules ont la même formule brute " + M(r"\ce{%s}" % fa) + " mais des formules développées différentes : ce sont des isomères.",
                                    "Ce sont des %s : %s. Il s'agit du %s (molécule A) et du %s (molécule B)." % (kind, detail, na, nb)]))


def lewis(v):
    f, comp, schema, doublets_nl, smi = [(r"\ce{H2O}", {"H": 2, "O": 1}, r"\mathrm{H}-\lTB{O}-\mathrm{H}", 2, "O"),
                                         (r"\ce{CO2}", {"C": 1, "O": 2}, r"\lTB{O}=\mathrm{C}=\lTB{O}", 4, "O=C=O"),
                                         (r"\ce{HCl}", {"H": 1, "Cl": 1}, r"\mathrm{H}-\lTBR{Cl}", 3, "Cl")][v]
    VAL = {"H": 1, "C": 4, "O": 6, "Cl": 7}
    total = sum(k * VAL[a] for a, k in comp.items())
    dev = {"O": "[H]O[H]", "O=C=O": "O=C=O", "Cl": "[H]Cl"}[smi]
    detail = " + ".join("%d \\times %d" % (k, VAL[a]) for a, k in comp.items())
    return ("Les atomes possèdent le nombre d'électrons de valence suivant : " + ", ".join(M(r"\ce{%s} : %d" % (a, VAL[a])) for a in comp) + ".\n\n"
            + lst(["Calculer le nombre total d'électrons de valence de la molécule " + M(f) + ".", "En déduire le nombre total de doublets d'électrons à répartir.", "Établir le schéma de Lewis de la molécule."]),
            "Solution :\n\n" + lst([M(r"%s = %d" % (detail, total)) + " électrons de valence.", M(r"\frac{%d}{2} = %d" % (total, total // 2)) + " doublets (liants et non liants).",
                                    "Schéma de Lewis : " + M(schema) + " ; la molécule comporte " + M(str(doublets_nl)) + " doublets non liants et respecte la règle de l'octet (ou du duet pour l'hydrogène)."])
            + "\n\nFormule développée correspondante :\n\n" + _mol("developpee petit", dev))


def cram(v):
    smi, ent, nom, subst = [("C[C@H](O)CC", "C[C@@H](O)CC", "butan-2-ol", [r"\ce{H}", r"\ce{OH}", r"\ce{CH3}", r"\ce{C2H5}"]),
                            ("C[C@H](O)C(=O)O", "C[C@@H](O)C(=O)O", "acide lactique", [r"\ce{H}", r"\ce{OH}", r"\ce{CH3}", r"\ce{COOH}"]),
                            ("N[C@@H](C)C(=O)O", "N[C@H](C)C(=O)O", "alanine", [r"\ce{H}", r"\ce{NH2}", r"\ce{CH3}", r"\ce{COOH}"])][v]
    assert chem.formule_brute(smi) == chem.formule_brute(ent) and smi != ent
    return ("La molécule ci-dessous est représentée en perspective de Cram.\n\n" + _mol("cram grand", smi) + "\n\n"
            + lst(["Repérer l'atome de carbone asymétrique et justifier.", "Combien de stéréoisomères de configuration cette molécule possède-t-elle ?", "Représenter, en perspective de Cram, l'énantiomère de cette molécule."]),
            "Solution :\n\n" + lst(["Le carbone asymétrique est le carbone lié à quatre substituants tous différents : " + ", ".join(M(x) for x in subst) + ".",
                                    "Un seul carbone asymétrique : " + M("2^{1} = 2") + " stéréoisomères, qui sont deux énantiomères (images l'un de l'autre dans un miroir, non superposables).",
                                    "L'énantiomère s'obtient en échangeant deux substituants du carbone asymétrique (liaisons en coin plein et en pointillé inversées)."])
            + "\n\nCouple d'énantiomères (" + nom + ") :\n\n" + _mol("cram grand", smi + " molécule étudiée", ent + " énantiomère"))


# (classe, partie, séquence, constructeur)
FAMILLES = [
    ("Seconde", "Algèbre", 1, eq1), ("Seconde", "Algèbre", 2, dev), ("Seconde", "Algèbre", 3, ineq),
    ("Seconde", "Analyse", 2, affine), ("Seconde", "Analyse", 4, carre),
    ("Seconde", "Géométrie", 3, dist), ("Seconde", "Géométrie", 5, para),
    ("Seconde", "Probabilités et statistiques", 4, urne), ("Seconde", "Probabilités et statistiques", 6, stat),
    ("Première", "Algèbre", 1, second), ("Première", "Algèbre", 3, suite_arith),
    ("Première", "Analyse", 2, deriv), ("Première", "Analyse", 5, variations),
    ("Première", "Géométrie", 4, prodscal), ("Première", "Géométrie", 6, trigo),
    ("Première", "Probabilités et statistiques", 3, cond), ("Première", "Probabilités et statistiques", 6, binom_p),
    ("Terminale", "Algèbre", 4, recurrence), ("Terminale", "Algèbre", 5, suite_geo),
    ("Terminale", "Analyse", 1, limites), ("Terminale", "Analyse", 2, expo), ("Terminale", "Analyse", 3, ln_),
    ("Terminale", "Analyse", 4, integrale), ("Terminale", "Analyse", 6, diffeq),
    ("Terminale", "Géométrie", 5, espace), ("Terminale", "Géométrie", 6, complexes),
    ("Terminale", "Probabilités et statistiques", 3, binom_t), ("Terminale", "Probabilités et statistiques", 5, denombrement),
    ("Seconde", "Géométrie", 1, vecteurs), ("Seconde", "Algèbre", 5, systemes), ("Seconde", "Analyse", 6, inverse),
    ("Première", "Géométrie", 1, droite), ("Première", "Algèbre", 2, suite_def), ("Première", "Analyse", 4, deriv_prod), ("Première", "Algèbre", 5, suite_geo_p),
    ("Terminale", "Algèbre", 1, suite_lim), ("Terminale", "Géométrie", 2, vec_espace),
    ("Terminale", "Analyse", None, synthese),   # problèmes de synthèse : session vide (épreuves d'examen)
]
FAMILLES_PC = [
    ("Seconde", "Chimie", 1, qte_matiere), ("Seconde", "Physique", 2, vitesse), ("Seconde", "Chimie", 3, concentration), ("Seconde", "Physique", 5, ohm),
    ("Première", "Chimie", 2, equilibrage), ("Première", "Physique", 5, energie),
    ("Terminale", "Physique", 2, desintegration), ("Terminale", "Chimie", 4, ph),
    ("Première", "Chimie", 1, semi_developpee), ("Première", "Chimie", 4, isomeres), ("Seconde", "Chimie", 4, lewis), ("Terminale", "Chimie", 1, cram),
]
NIVEAUX = ["Facile", "Moyen", "Difficile"]
AUCUNE, MATHS, PC = "SPECIAL:Aucune", "Mathématiques", "Physique-Chimie"


def _construire(familles, matiere, maths: bool) -> list:
    out = []
    for classe, partie, seq, build in familles:
        for v in range(3):
            sujet, corrige = build(v)
            if maths and build is diffeq:
                specs = [MATHS, PC]
            elif maths and classe != "Seconde" and v == 2:
                specs = [MATHS]                       # variante la plus difficile : enseignement de spécialité
            else:
                specs = [AUCUNE]
            out.append({"matiere": matiere, "classe": classe, "partie": partie, "session": seq, "niveau": NIVEAUX[v], "sujet": sujet, "corrige": corrige,
                        "specialites": specs, "tag": seq is not None and (v == 2 or (v == 1 and seq in (3, 6)))})
    return out


def exercices() -> list:
    """Mathématiques."""
    return _construire(FAMILLES, "Mathématiques", True)


def exercices_pc() -> list:
    """Physique-chimie (formules moléculaires, ions, équations-bilans, unités)."""
    return _construire(FAMILLES_PC, "Physique-Chimie", False)


def tous() -> list:
    return exercices() + exercices_pc()
