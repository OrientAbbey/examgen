"""Banque de démonstration RÉALISTE (mathématiques Seconde / Première / Terminale).

Chaque énoncé est construit à partir de paramètres et son corrigé est CALCULÉ (fractions exactes), avec des
vérifications (assert) : solutions qui vérifient l'équation, racines, dérivées, etc. Notation en Unicode (pas de LaTeX).
Convention : le corrigé commence par « Solution : » ; aucun sujet ne contient ce mot.
"""
from fractions import Fraction as F
from math import acos, ceil, comb, degrees, e, exp, isqrt, log, sqrt

M = "−"
SUP = {2: "²", 3: "³"}


def n(x) -> str:
    x = F(x)
    s = str(x.numerator) if x.denominator == 1 else f"{x.numerator}/{x.denominator}"
    return s.replace("-", M)


def dec(x, d=2) -> str:
    return f"{float(x):.{d}f}".replace(".", ",").replace("-", M)


def poly(cs, var="x") -> str:
    deg, out = len(cs) - 1, ""
    for i, c in enumerate(cs):
        c, p = F(c), deg - i
        if c == 0:
            continue
        a = abs(c)
        mono = "" if p == 0 else (var if p == 1 else var + SUP.get(p, f"^{p}"))
        coef = "" if (a == 1 and p != 0) else (n(a) if a.denominator == 1 else f"({n(a)})")
        body = coef + mono
        out += (M if c < 0 else "") + body if not out else (f" {M} " if c < 0 else " + ") + body
    return out or "0"


def rad(m: int) -> str:
    k = 1
    for d in range(isqrt(m), 1, -1):
        if m % (d * d) == 0:
            k, m = d, m // (d * d)
            break
    return str(k) if m == 1 else (str(k) if k > 1 else "") + f"√{m}"


def cx(re, im) -> str:
    re, im = F(re), F(im)
    if im == 0:
        return n(re)
    a = abs(im)
    i = "i" if a == 1 else (n(a) + "i" if a.denominator == 1 else f"({n(a)})i")
    if re == 0:
        return (M if im < 0 else "") + i
    return f"{n(re)} {M if im < 0 else '+'} {i}"


def lst(items, start=1):
    return "\n".join(f"{i}. {t}" for i, t in enumerate(items, start))


def interval(op, v) -> str:
    return {"≤": f"]{M}∞ ; {n(v)}]", "<": f"]{M}∞ ; {n(v)}[", "≥": f"[{n(v)} ; +∞[", ">": f"]{n(v)} ; +∞["}[op]


def par(x) -> str:
    """Nombre entre parenthèses s'il est négatif : (−4)."""
    return f"({n(x)})" if F(x) < 0 else n(x)


def sg(x) -> str:
    """Terme signé pour une somme : ' + 3' ou ' − 3'."""
    return f" {M} {n(abs(F(x)))}" if F(x) < 0 else f" + {n(x)}"


def radeq(m: int) -> str:
    """√m, suivi de sa forme simplifiée seulement si elle diffère."""
    return f"√{m}" if rad(m) == f"√{m}" else f"√{m} = {rad(m)}"


def lin(terms, const=None) -> str:
    """Forme linéaire 2x − y + 3z − 5 (coefficients ±1 omis)."""
    out = ""
    for c, v in terms:
        c = F(c)
        if c == 0:
            continue
        body = ("" if abs(c) == 1 else n(abs(c))) + v
        out += (M if c < 0 else "") + body if not out else (f" {M} " if c < 0 else " + ") + body
    if const:
        out += sg(const)
    return out or "0"


def ax(a) -> str:
    """Exposant a·x lisible : 2x, −x, −x/2."""
    a = F(a)
    sign, a = (M if a < 0 else ""), abs(a)
    if a.denominator == 1:
        return f"{sign}{'' if a == 1 else a.numerator}x"
    return f"{sign}{'' if a.numerator == 1 else a.numerator}x/{a.denominator}"


def par_t(p, c) -> str:
    """p + c·t pour une représentation paramétrique."""
    t = ("" if abs(F(c)) == 1 else n(abs(F(c)))) + "t"
    if c == 0:
        return n(p)
    if p == 0:
        return (M if c < 0 else "") + t
    return f"{n(p)} {M if c < 0 else '+'} {t}"


FLIP = {"≤": "≥", "<": ">", "≥": "≤", ">": "<"}

# ───────────────────────── SECONDE ─────────────────────────
def eq1(v):
    sets = [[(3, 7, 1, 15), (5, -2, 2, 10)], [(4, 3, -1, 13), (6, -5, 2, 9), (7, 1, 3, -4)],
            [(-3, 8, 2, -7), (9, -4, -5, 11), (2, 5, 7, -5)]][v]
    q, s = [], []
    for p_, q_, r_, s_ in sets:
        x = F(s_ - q_, p_ - r_)
        assert p_ * x + q_ == r_ * x + s_
        q.append(f"{poly([p_, q_])} = {poly([r_, s_])}")
        s.append(f"{poly([p_, q_])} = {poly([r_, s_])} ⇔ {poly([p_ - r_, 0])} = {n(s_ - q_)} ⇔ x = {n(x)}")
    return ("**Équations du premier degré.** Résoudre dans ℝ les équations suivantes :\n\n" + lst(q),
            "Solution :\n\n" + lst(s))


def dev(v):
    sets = [[(1, 3, 1, 5), (1, -4, 1, -4)], [(1, 2, 1, -7), (2, 3, 1, -1), (1, 6, 1, 6)],
            [(3, -2, 2, 5), (2, 1, 2, 1), (1, -5, 1, 5)]][v]
    q, s = [], []
    for p_, q_, r_, s_ in sets:
        sq = (p_, q_) == (r_, s_)
        res = [p_ * r_, p_ * s_ + q_ * r_, q_ * s_]
        q.append(f"({poly([p_, q_])})²" if sq else f"({poly([p_, q_])})({poly([r_, s_])})")
        s.append((f"({poly([p_, q_])})²" if sq else f"({poly([p_, q_])})({poly([r_, s_])})") + f" = {poly(res)}")
    return ("**Développer et réduire** chacune des expressions suivantes :\n\n" + lst(q), "Solution :\n\n" + lst(s))


def ineq(v):
    sets = [[(2, 3, "≤", 11)], [(3, -1, ">", 8), (-2, 5, "≤", 1)],
            [(-4, 3, "<", 15), (5, 2, "≥", -8), (-3, 1, ">", 7)]][v]
    q, s = [], []
    for a, b, op, c in sets:
        val, op2 = F(c - b, a), (op if a > 0 else FLIP[op])
        q.append(f"{poly([a, b])} {op} {n(c)}")
        s.append(f"{poly([a, b])} {op} {n(c)} ⇔ {poly([a, 0])} {op} {n(c - b)} ⇔ x {op2} {n(val)}. "
                 f"Ensemble des solutions : {interval(op2, val)}." + (" (On change le sens de l'inégalité car on divise par un nombre négatif.)" if a < 0 else ""))
    return ("**Inéquations.** Résoudre dans ℝ, puis donner l'ensemble des solutions sous forme d'intervalle :\n\n" + lst(q),
            "Solution :\n\n" + lst(s))


def affine(v):
    m, p_, a, c = [(2, 1, 3, 9), (-3, 4, 2, -5), (F(5, 2), -1, 4, 14)][v]
    f = lambda x: m * x + p_
    x0 = F(c - p_) / F(m)
    assert f(x0) == c
    return (f"Soit f la fonction affine définie sur ℝ par f(x) = {poly([m, p_])}.\n\n"
            + lst([f"Calculer f({n(a)}).", f"Déterminer l'antécédent de {n(c)} par f.", "Donner le sens de variation de f, en justifiant."]),
            "Solution :\n\n" + lst([f"f({n(a)}) = {n(f(a))}.", f"f(x) = {n(c)} ⇔ {poly([m, p_])} = {n(c)} ⇔ x = {n(x0)}.",
                                    f"Le coefficient directeur {n(m)} est {'positif' if m > 0 else 'négatif'} : f est strictement "
                                    f"{'croissante' if m > 0 else 'décroissante'} sur ℝ."]))


def carre(v):
    k, t = [(4, None), (6, 16), (10, 24)][v]
    h, q = k // 2, k * k // 4
    qs = ["Factoriser f(x).", "Résoudre l'équation f(x) = 0.", f"Montrer que f(x) = (x {M} {h})² {M} {q}. En déduire le minimum de f."]
    ss = [f"f(x) = x(x {M} {k}).", f"x(x {M} {k}) = 0 ⇔ x = 0 ou x = {k}.",
          f"(x {M} {h})² {M} {q} = x² {M} {k}x + {q} {M} {q} = f(x). Un carré est positif ou nul, donc f(x) ≥ {M}{q}, "
          f"avec égalité pour x = {h} : le minimum de f est {M}{q}."]
    if t:
        r = isqrt(t + q)
        assert r * r == t + q and (h + r) ** 2 - k * (h + r) == t and (h - r) ** 2 - k * (h - r) == t
        qs.append(f"Résoudre l'équation f(x) = {t}.")
        ss.append(f"f(x) = {t} ⇔ (x {M} {h})² = {t + q} ⇔ x {M} {h} = {r} ou x {M} {h} = {M}{r} ⇔ x = {n(h + r)} ou x = {n(h - r)}.")
    return (f"Soit f la fonction définie sur ℝ par f(x) = x² {M} {k}x.\n\n" + lst(qs), "Solution :\n\n" + lst(ss))


def dist(v):
    A, B = [((1, 2), (4, 6)), ((-2, 1), (3, -4)), ((-3, -1), (5, 5))][v]
    dx, dy = B[0] - A[0], B[1] - A[1]
    d2 = dx * dx + dy * dy
    I = (F(A[0] + B[0], 2), F(A[1] + B[1], 2))
    P = lambda t: f"({n(t[0])} ; {n(t[1])})"
    return (f"Dans un repère orthonormé, on considère les points A{P(A)} et B{P(B)}.\n\n"
            + lst(["Calculer la distance AB.", "Déterminer les coordonnées du milieu I du segment [AB]."]),
            "Solution :\n\n" + lst([f"AB = √(({n(B[0])} {M} {par(A[0])})² + ({n(B[1])} {M} {par(A[1])})²) = √({dx * dx} + {dy * dy}) = {radeq(d2)}.",
                                    f"I a pour coordonnées (({n(A[0])} + {par(B[0])})/2 ; ({n(A[1])} + {par(B[1])})/2) = {P(I)}."]))


def para(v):
    A, B, C = [((1, 1), (4, 2), (5, 5)), ((-1, 2), (2, 0), (4, 3)), ((0, -2), (3, 1), (2, 5))][v]
    D = (A[0] + C[0] - B[0], A[1] + C[1] - B[1])
    AB, DC = (B[0] - A[0], B[1] - A[1]), (C[0] - D[0], C[1] - D[1])
    assert AB == DC
    I = (F(A[0] + C[0], 2), F(A[1] + C[1], 2))
    assert I == (F(B[0] + D[0], 2), F(B[1] + D[1], 2))
    P = lambda t: f"({n(t[0])} ; {n(t[1])})"
    return (f"Dans un repère orthonormé, on donne A{P(A)}, B{P(B)} et C{P(C)}.\n\n"
            + lst(["Déterminer les coordonnées du point D tel que ABCD soit un parallélogramme.", "Vérifier que les diagonales [AC] et [BD] ont le même milieu."]),
            "Solution :\n\n" + lst([f"ABCD est un parallélogramme ⇔ le vecteur AB est égal au vecteur DC. AB a pour coordonnées {P(AB)} ; "
                                    f"en notant D(x ; y), DC a pour coordonnées ({n(C[0])} {M} x ; {n(C[1])} {M} y). On obtient D{P(D)}.",
                                    f"Milieu de [AC] : {P(I)}. Milieu de [BD] : {P(I)}. Les deux milieux sont confondus."]))


def urne(v):
    r, b, g = [(3, 5, 2), (6, 4, 5), (7, 9, 4)][v]
    N = r + b + g
    qs = ["Calculer la probabilité de tirer une boule rouge.", "Calculer la probabilité de ne pas tirer une boule rouge.", "Calculer la probabilité de tirer une boule rouge ou une boule verte."]
    ss = [f"P(R) = {r}/{N}" + ("" if f"{r}/{N}" == n(F(r, N)) else f" = {n(F(r, N))}") + ".", f"P(non R) = 1 {M} {n(F(r, N))} = {n(1 - F(r, N))}.", f"P(R ou V) = ({r} + {g})/{N} = {n(F(r + g, N))}."]
    ctx = f"Une urne contient {r} boules rouges, {b} boules bleues et {g} boules vertes, indiscernables au toucher. On tire une boule au hasard."
    if v == 1:
        ctx += " On répète l'expérience deux fois, **avec remise**."
        qs.append("Calculer la probabilité d'obtenir deux boules rouges.")
        ss.append(f"Tirages indépendants : P = ({n(F(r, N))})² = {n(F(r, N) ** 2)}.")
    if v == 2:
        ctx += " On tire ensuite deux boules successivement, **sans remise**."
        qs.append("Calculer la probabilité d'obtenir deux boules rouges.")
        ss.append(f"P = {r}/{N} × {r - 1}/{N - 1} = {n(F(r, N) * F(r - 1, N - 1))}.")
    return ctx + "\n\n" + lst(qs), "Solution :\n\n" + lst(ss)


def stat(v):
    notes = [[12, 8, 13, 10, 13, 9, 12], [6, 15, 9, 12, 11, 8, 16, 10, 12], [4, 17, 9, 12, 14, 7, 19, 10, 15]][v]
    s, N = sorted(notes), len(notes)
    mean, med = F(sum(notes), N), s[N // 2]
    qs = ["Calculer la moyenne de cette série.", "Déterminer sa médiane.", "Calculer son étendue."]
    ss = [f"Moyenne = {sum(notes)}/{N} " + (f"= {n(mean)}" if f"{sum(notes)}/{N}" != n(mean) else f"≈ {dec(mean)}") + (f" ≈ {dec(mean)}" if f"{sum(notes)}/{N}" != n(mean) and mean.denominator != 1 else "") + ".",
          f"Série ordonnée : {' ; '.join(map(str, s))}. Effectif impair ({N}) : la médiane est la valeur de rang {N // 2 + 1}, soit {med}.",
          f"Étendue = {s[-1]} {M} {s[0]} = {s[-1] - s[0]}."]
    if v == 2:
        q1, q3 = s[ceil(N / 4) - 1], s[ceil(3 * N / 4) - 1]
        qs.append("Déterminer les premier et troisième quartiles.")
        ss.append(f"Q1 est la valeur de rang {ceil(N / 4)} : Q1 = {q1}. Q3 est la valeur de rang {ceil(3 * N / 4)} : Q3 = {q3}.")
    return (f"Voici les notes obtenues par {N} élèves à un contrôle : {' ; '.join(map(str, notes))}.\n\n" + lst(qs), "Solution :\n\n" + lst(ss))


# ───────────────────────── PREMIÈRE ─────────────────────────
def second(v):
    a, r1, r2 = [(1, 2, 3), (1, -1, 4), (2, 1, -3)][v]
    b, c = -a * (r1 + r2), a * r1 * r2
    D = b * b - 4 * a * c
    sd = isqrt(D)
    assert sd * sd == D and sorted([F(-b - sd, 2 * a), F(-b + sd, 2 * a)]) == sorted([F(r1), F(r2)])
    lo, hi = sorted([r1, r2])
    P = poly([a, b, c])
    return (f"Soit f la fonction définie sur ℝ par f(x) = {P}.\n\n" + lst(["Calculer le discriminant Δ de f(x).", "Résoudre l'équation f(x) = 0.", "En déduire le signe de f(x) selon les valeurs de x."]),
            "Solution :\n\n" + lst([f"Δ = b² {M} 4ac = {par(b)}² {M} 4×{par(a)}×{par(c)} = {D}.",
                                    f"Δ > 0 : deux racines x₁ = ({n(-b)} {M} {sd})/{2 * a} = {n(F(-b - sd, 2 * a))} et x₂ = ({n(-b)} + {sd})/{2 * a} = {n(F(-b + sd, 2 * a))}.",
                                    f"Le coefficient de x² est {'positif' if a > 0 else 'négatif'} : f(x) est {'positif' if a > 0 else 'négatif'} à l'extérieur des racines et "
                                    f"{'négatif' if a > 0 else 'positif'} entre {n(lo)} et {n(hi)}."]))


def suite_arith(v):
    u0, r, t = [(3, 2, 50), (-4, 3, 100), (12, -2, None)][v]
    u10 = u0 + 10 * r
    S = F(11 * (u0 + u10), 2)
    assert S == sum(u0 + r * k for k in range(11))
    qs = ["Exprimer u_n en fonction de n.", "Calculer u₁₀.", "Calculer S = u₀ + u₁ + … + u₁₀."]
    ss = [f"u_n = u₀ + n×r = {poly([r, u0], 'n')}.", f"u₁₀ = {n(u0)} + 10×{par(r)} = {n(u10)}.", f"S = 11 × (u₀ + u₁₀)/2 = 11 × ({n(u0)}{sg(u10)})/2 = {n(S)}."]
    if t is not None:
        k = (t - u0) // r + 1
        assert u0 + r * k > t >= u0 + r * (k - 1)
        qs.append(f"Déterminer le plus petit entier n tel que u_n > {t}.")
        ss.append(f"{poly([r, u0], 'n')} > {t} ⇔ n > {n(F(t - u0, r))} ; le plus petit entier est n = {k} (u_{k} = {u0 + r * k}).")
    return (f"Soit (u_n) la suite arithmétique de premier terme u₀ = {n(u0)} et de raison r = {n(r)}.\n\n" + lst(qs), "Solution :\n\n" + lst(ss))


def deriv(v):
    a, b, c, d = [(1, -3, 0, 2), (2, 1, -4, 5), (-1, 4, 3, -2)][v]
    f1, fp1 = a + b + c + d, 3 * a + 2 * b + c
    qs = ["Calculer f'(x).", "Calculer f(1) et f'(1).", "En déduire une équation de la tangente T à la courbe de f au point d'abscisse 1."]
    ss = [f"f'(x) = {poly([3 * a, 2 * b, c])}.", f"f(1) = {n(f1)} et f'(1) = {n(fp1)}.",
          f"T : y = f'(1)(x {M} 1) + f(1) = {n(fp1)}(x {M} 1) + {n(f1)}, soit y = {poly([fp1, f1 - fp1])}."]
    if v == 0:
        qs.append("Résoudre f'(x) = 0.")
        ss.append("f'(x) = 3x² − 6x = 3x(x − 2) = 0 ⇔ x = 0 ou x = 2.")
    return (f"Soit f la fonction définie sur ℝ par f(x) = {poly([a, b, c, d])}.\n\n" + lst(qs), "Solution :\n\n" + lst(ss))


def variations(v):
    m = v + 1
    f = lambda x: x ** 3 - 3 * m * m * x
    assert f(-m) == 2 * m ** 3 and f(m) == -2 * m ** 3
    return (f"Soit f la fonction définie sur ℝ par f(x) = x³ {M} {3 * m * m}x.\n\n" + lst(["Calculer f'(x) et la factoriser.", "Étudier le signe de f'(x) et dresser le tableau de variations de f.", "Préciser les extremums locaux de f."]),
            "Solution :\n\n" + lst([f"f'(x) = 3x² {M} {3 * m * m} = 3(x {M} {m})(x + {m}).",
                                    f"f'(x) est positif pour x ≤ {M}{m} et pour x ≥ {m}, négatif entre {M}{m} et {m}. "
                                    f"f est donc croissante sur ]{M}∞ ; {M}{m}], décroissante sur [{M}{m} ; {m}], croissante sur [{m} ; +∞[.",
                                    f"Maximum local f({M}{m}) = {2 * m ** 3} ; minimum local f({m}) = {M}{2 * m ** 3}."]))


def prodscal(v):
    (a, b), (c, d) = [((3, 4), (-4, 3)), ((2, 1), (1, 3)), ((2, 3), (1, 5))][v]
    dot, nu, nv = a * c + b * d, a * a + b * b, c * c + d * d
    qs = ["Calculer le produit scalaire u · v.", "Les vecteurs u et v sont-ils orthogonaux ?", "Calculer les normes ‖u‖ et ‖v‖."]
    ss = [f"u · v = {n(a)}×{par(c)} + {n(b)}×{par(d)} = {n(dot)}.",
          f"u · v {'= 0 : les vecteurs sont orthogonaux' if dot == 0 else f'= {dot} ≠ 0 : ils ne sont pas orthogonaux'}.",
          f"‖u‖ = {radeq(nu)} et ‖v‖ = {radeq(nv)}."]
    if dot != 0:
        th = degrees(acos(dot / sqrt(nu * nv)))
        qs.append("Déterminer l'angle géométrique θ entre u et v, au dixième de degré près.")
        ss.append(f"cos θ = u · v / (‖u‖ × ‖v‖) = {dot}/√{nu * nv} ≈ {dec(dot / sqrt(nu * nv), 4)}, donc θ ≈ {dec(th, 1)}°.")
    return (f"Dans un repère orthonormé, on considère les vecteurs u({n(a)} ; {n(b)}) et v({n(c)} ; {n(d)}).\n\n" + lst(qs), "Solution :\n\n" + lst(ss))


TRIGO = {"cos x = 1/2": "π/3 ; 5π/3", "cos x = −1/2": "2π/3 ; 4π/3", "cos x = √2/2": "π/4 ; 7π/4", "cos x = −√2/2": "3π/4 ; 5π/4",
         "sin x = 1/2": "π/6 ; 5π/6", "sin x = √3/2": "π/3 ; 2π/3", "sin x = √2/2": "π/4 ; 3π/4", "sin x = −1/2": "7π/6 ; 11π/6"}


def trigo(v):
    eqs = [["cos x = 1/2"], ["sin x = √3/2", "cos x = −√2/2"], ["sin x = −1/2", "cos x = −1/2", "sin x = √2/2"]][v]
    return ("**Trigonométrie.** Résoudre dans l'intervalle [0 ; 2π] les équations suivantes :\n\n" + lst(eqs),
            "Solution :\n\n" + lst([f"{q} ⇔ x ∈ {{ {TRIGO[q]} }}." for q in eqs]))


def cond(v):
    p_, q_, r_ = [(F(2, 5), F(1, 2), F(1, 10)), (F(1, 3), F(3, 4), F(1, 2)), (F(3, 10), F(2, 3), F(1, 5))][v]
    pab = p_ * q_
    pb = pab + (1 - p_) * r_
    pba = pab / pb
    return (f"Dans un lycée, une proportion {n(p_)} des élèves est en classe de Première (événement A). Parmi ces élèves, une proportion {n(q_)} pratique un sport (événement B) ; "
            f"parmi les autres élèves, une proportion {n(r_)} pratique un sport. On choisit un élève au hasard.\n\n"
            + lst(["Calculer P(A ∩ B).", "Calculer P(B) à l'aide de la formule des probabilités totales.", "Sachant que l'élève pratique un sport, quelle est la probabilité qu'il soit en Première ?"]),
            "Solution :\n\n" + lst([f"P(A ∩ B) = P(A) × P_A(B) = ({n(p_)}) × ({n(q_)}) = {n(pab)}.",
                                    f"P(B) = P(A ∩ B) + P(Ā ∩ B) = {n(pab)} + ({n(1 - p_)}) × ({n(r_)}) = {n(pb)}.",
                                    f"P_B(A) = P(A ∩ B) / P(B) = ({n(pab)}) / ({n(pb)}) = {n(pba)}."]))


def binom_p(v):
    nn, p_, k = [(4, F(1, 2), 2), (5, F(1, 3), 2), (6, F(1, 4), 3)][v]
    pk = comb(nn, k) * p_ ** k * (1 - p_) ** (nn - k)
    p1 = 1 - (1 - p_) ** nn
    assert sum(comb(nn, j) * p_ ** j * (1 - p_) ** (nn - j) for j in range(nn + 1)) == 1
    return (f"Soit X une variable aléatoire suivant la loi binomiale B({nn} ; {n(p_)}).\n\n"
            + lst([f"Calculer P(X = {k}).", "Calculer P(X ≥ 1).", "Calculer l'espérance E(X)."]),
            "Solution :\n\n" + lst([f"P(X = {k}) = C({nn},{k}) × ({n(p_)})^{k} × ({n(1 - p_)})^{nn - k} = {comb(nn, k)} × {n(p_ ** k)} × {n((1 - p_) ** (nn - k))} = {n(pk)}.",
                                    f"P(X ≥ 1) = 1 {M} P(X = 0) = 1 {M} ({n(1 - p_)})^{nn} = {n(p1)}.", f"E(X) = n × p = {nn} × {n(p_)} = {n(nn * p_)}."]))


# ───────────────────────── TERMINALE ─────────────────────────
def recurrence(v):
    u0, a, b, form, her = [(1, 2, 1, "2^(n+1) − 1", "u_{n+1} = 2(2^(n+1) − 1) + 1 = 2^(n+2) − 2 + 1 = 2^(n+2) − 1"),
                           (0, 2, 1, "2^n − 1", "u_{n+1} = 2(2^n − 1) + 1 = 2^(n+1) − 2 + 1 = 2^(n+1) − 1"),
                           (2, 3, -2, "3^n + 1", "u_{n+1} = 3(3^n + 1) − 2 = 3^(n+1) + 3 − 2 = 3^(n+1) + 1")][v]
    closed = [lambda k: 2 ** (k + 1) - 1, lambda k: 2 ** k - 1, lambda k: 3 ** k + 1][v]
    u = [u0]
    for _ in range(10):
        u.append(a * u[-1] + b)
    assert all(u[k] == closed(k) for k in range(11))
    rel = f"u_{{n+1}} = {a}u_n {'+' if b > 0 else M} {abs(b)}"
    return (f"Soit (u_n) la suite définie par u₀ = {u0} et, pour tout entier naturel n, {rel}.\n\n"
            + lst(["Calculer u₁, u₂ et u₃.", f"Démontrer par récurrence que, pour tout entier naturel n, u_n = {form}."]),
            "Solution :\n\n" + lst([f"u₁ = {u[1]}, u₂ = {u[2]}, u₃ = {u[3]}.",
                                    f"**Initialisation** : pour n = 0, {form.replace('n', '0')} = {closed(0)} = u₀ : la propriété est vraie.\n"
                                    f"   **Hérédité** : supposons u_n = {form} pour un entier n. Alors {her}. La propriété est vraie au rang n+1.\n"
                                    "   **Conclusion** : elle est vraie pour tout entier naturel n."]))


def suite_geo(v):
    u0, q = [(8, F(1, 2)), (5, F(1, 3)), (-6, F(2, 3))][v]
    u5 = u0 * q ** 5
    lim = F(u0) / (1 - q)
    assert abs(float(sum(u0 * q ** k for k in range(200))) - float(lim)) < 1e-9
    return (f"Soit (u_n) la suite géométrique de premier terme u₀ = {n(u0)} et de raison q = {n(q)}.\n\n"
            + lst(["Exprimer u_n en fonction de n, puis calculer u₅.", "Déterminer la limite de (u_n).", "Pour tout n, on pose S_n = u₀ + u₁ + … + u_n. Exprimer S_n en fonction de n puis déterminer la limite de (S_n)."]),
            "Solution :\n\n" + lst([f"u_n = {n(u0)} × ({n(q)})^n ; u₅ = {n(u0)} × ({n(q)})⁵ = {n(u5)}.",
                                    f"Comme {M}1 < q < 1, (q^n) tend vers 0, donc (u_n) converge vers 0.",
                                    f"S_n = u₀ × (1 {M} q^(n+1))/(1 {M} q) = {n(u0 / (1 - q))} × (1 {M} ({n(q)})^(n+1)). Comme q^(n+1) → 0, S_n tend vers {n(lim)}."]))


def limites(v):
    a, b, c, d = [(2, 1, 1, -3), (3, -2, 2, 4), (-1, 5, 4, -2)][v]
    assert a * d - b * c != 0
    x0 = F(-d, c)
    g = f"({poly([a, b])})/({poly([c, d])})"
    lim = F(a, c)
    r = n(a) if c == 1 else f"{n(a)}/{n(c)}"
    r = r if r == n(lim) else f"{r} = {n(lim)}"
    return (f"Soit f la fonction définie sur ℝ \\ {{{n(x0)}}} par f(x) = {g}.\n\n"
            + lst(["Déterminer la limite de f en +∞. Que peut-on en déduire pour la courbe de f ?", f"Justifier que la droite d'équation x = {n(x0)} est asymptote verticale à la courbe."]),
            "Solution :\n\n" + lst([f"Pour x ≠ 0, f(x) = ({n(a)}{sg(F(b))[:3]}{n(abs(F(b)))}/x) / ({n(c)}{sg(F(d))[:3]}{n(abs(F(d)))}/x) → {r} quand x → +∞. "
                                    f"La droite d'équation y = {n(lim)} est asymptote horizontale à la courbe en +∞.",
                                    f"Le dénominateur s'annule en x = {n(x0)} alors que le numérateur y vaut {n(a * x0 + b)} ≠ 0 : f(x) tend vers ±∞ quand x se rapproche de {n(x0)}, "
                                    f"donc la droite x = {n(x0)} est asymptote verticale."]))


def expo(v):
    a = v
    mn = -e ** (-(a + 1))
    assert abs(((-a - 1) + a) * exp(-a - 1) - mn) < 1e-12
    fx = "x e^x" if a == 0 else f"(x + {a})e^x"
    return (f"Soit f la fonction définie sur ℝ par f(x) = {fx}.\n\n"
            + lst(["Calculer f'(x) et montrer que f'(x) = (x + " + str(a + 1) + ")e^x.", "Étudier le signe de f'(x) et dresser le tableau de variations de f.", "En déduire le minimum de f ; donner une valeur approchée à 10⁻³ près."]),
            "Solution :\n\n" + lst([f"f = u×v avec u(x) = {'x' if a == 0 else f'x + {a}'} et v(x) = e^x : f'(x) = 1×e^x + {'x' if a == 0 else f'(x + {a})'}e^x = (x + {a + 1})e^x.",
                                    f"e^x > 0, donc f'(x) a le signe de x + {a + 1} : f est décroissante sur ]{M}∞ ; {M}{a + 1}] et croissante sur [{M}{a + 1} ; +∞[.",
                                    f"Le minimum est f({M}{a + 1}) = {M}e^({M}{a + 1}) ≈ {dec(mn, 3)}."]))


def ln_(v):
    k, a, b = [(5, 1, 7), (12, 2, 9), (20, 3, 11)][v]
    return ("**Exponentielle et logarithme.** Résoudre dans ℝ :\n\n"
            + lst([f"e^x = {k}", f"ln(x + {a}) = ln({b})  (on précisera l'ensemble de définition)", f"e^x ≥ {k}"]),
            "Solution :\n\n" + lst([f"e^x = {k} ⇔ x = ln({k}) ≈ {dec(log(k), 3)}.",
                                    f"L'équation a un sens pour x + {a} > 0, soit x > {M}{a}. Alors x + {a} = {b} ⇔ x = {b - a}, valeur bien supérieure à {M}{a}.",
                                    f"La fonction ln est croissante : e^x ≥ {k} ⇔ x ≥ ln({k}). Ensemble des solutions : [ln({k}) ; +∞[."]))


def integrale(v):
    a, b, c = [(3, 2, 1), (6, -4, 5), (4, 3, -2)][v]
    Fp = [F(a, 3), F(b, 2), F(c), 0]
    val = F(a, 3) + F(b, 2) + c
    assert sum(Fp[:3]) == val
    return (f"Soit f la fonction définie sur ℝ par f(x) = {poly([a, b, c])}.\n\n" + lst(["Déterminer une primitive F de f sur ℝ.", "Calculer l'intégrale I = ∫₀¹ f(x) dx."]),
            "Solution :\n\n" + lst([f"F(x) = {poly([F(a, 3), F(b, 2), c, 0])}.", f"I = F(1) {M} F(0) = {n(val)} {M} 0 = {n(val)}."]))


def diffeq(v):
    a, b, y0, x1 = [(F(2), 0, 3, 1), (F(-1, 2), 0, 4, 2), (F(2), 4, 1, 1)][v]
    C = F(y0) + F(b) / a
    part = -F(b) / a
    y = lambda x: float(C) * exp(float(a) * x) + float(part)
    assert abs(y(0) - y0) < 1e-12
    cst = f" {'+' if part > 0 else M} {n(abs(part))}" if b else ""
    ea = lambda k: f"e^({ax(k)})" if F(k).denominator != 1 or True else ""
    rel = f"y' = {n(a) if a.denominator == 1 else '(' + n(a) + ')'}y" + (f" + {b}" if b else "")
    ex1 = F(a * x1)
    ex1s = f"e^{n(ex1)}" if ex1 >= 0 and ex1.denominator == 1 else f"e^({n(ex1)})"
    gen = (f"Les solutions de y' = ay sont les fonctions y(x) = C e^(ax). " if not b else
           f"Une solution constante est y = {M}b/a = {n(part)} ; les solutions sont y(x) = C e^({ax(a)}){cst}. ")
    return (f"On considère le problème : {rel}, avec y(0) = {y0}.\n\n"
            + lst(["Déterminer la solution y de ce problème.", f"Calculer y({x1}) (valeur approchée à 10⁻² près)."]),
            "Solution :\n\n" + lst([gen + f"La condition y(0) = {y0} donne C = {n(C)}. Donc y(x) = {n(C) if C != 1 else ''}e^({ax(a)}){cst}.",
                                    f"y({x1}) = {n(C)}{ex1s}{cst} ≈ {dec(y(x1), 2)}."]))


def espace(v):
    (a, b, c, d), A = [((2, -1, 3, -5), (1, 0, 1)), ((1, 2, -1, -3), (2, 1, 3)), ((3, -2, 1, -4), (1, -1, -1))][v]
    val = a * A[0] + b * A[1] + c * A[2] + d
    eq = lin([(a, "x"), (b, "y"), (c, "z")], d) + " = 0"
    check = f"{n(a)}×{par(A[0])}{sg(b)[:3]}{n(abs(b))}×{par(A[1])}{sg(c)[:3]}{n(abs(c))}×{par(A[2])}{sg(d)} = {n(val)}"
    qs = ["Donner un vecteur normal au plan P.", f"Le point A({n(A[0])} ; {n(A[1])} ; {n(A[2])}) appartient-il à P ?", "Donner une représentation paramétrique de la droite D perpendiculaire à P passant par A."]
    ss = [f"Un vecteur normal est n({n(a)} ; {n(b)} ; {n(c)}).",
          f"{check}" + (" : A appartient à P." if val == 0 else f" ≠ 0 : A n'appartient pas à P."),
          f"D est dirigée par n : x = {par_t(A[0], a)}, y = {par_t(A[1], b)}, z = {par_t(A[2], c)}, avec t ∈ ℝ."]
    if val != 0:
        qs.append("Calculer la distance du point A au plan P.")
        ss.append(f"d(A, P) = |{n(val)}|/√({a * a} + {b * b} + {c * c}) = {abs(val)}/√{a * a + b * b + c * c} ≈ {dec(abs(val) / sqrt(a * a + b * b + c * c), 3)}.")
    return (f"L'espace est muni d'un repère orthonormé. Le plan P a pour équation {eq}.\n\n" + lst(qs), "Solution :\n\n" + lst(ss))


def complexes(v):
    (a, b), (c, d) = [((1, 2), (3, -1)), ((-2, 3), (1, 1)), ((3, -4), (2, 1))][v]
    z1, z2 = complex(a, b), complex(c, d)
    den = c * c + d * d
    qr, qi = F(a * c + b * d, den), F(b * c - a * d, den)
    assert abs(z1 * z2 - complex(a * c - b * d, a * d + b * c)) < 1e-12 and abs(z1 / z2 - complex(float(qr), float(qi))) < 1e-12
    m = a * a + b * b
    return (f"On considère les nombres complexes z₁ = {cx(a, b)} et z₂ = {cx(c, d)}.\n\n"
            + lst(["Calculer z₁ + z₂ et z₁ × z₂.", "Calculer le module de z₁.", "Écrire le quotient z₁ / z₂ sous forme algébrique."]),
            "Solution :\n\n" + lst([f"z₁ + z₂ = {cx(a + c, b + d)} et z₁ × z₂ = {cx(a * c - b * d, a * d + b * c)}.",
                                    f"|z₁| = √({par(a)}² + {par(b)}²) = {radeq(m)}.",
                                    f"z₁ / z₂ = z₁ × conj(z₂) / |z₂|² = ({cx(a, b)})({cx(c, -d)}) / {den} = {cx(qr, qi)}."]))


def binom_t(v):
    nn, p_, k = [(10, 0.3, 3), (8, 0.5, 4), (12, 0.2, 2)][v]
    pk = comb(nn, k) * p_ ** k * (1 - p_) ** (nn - k)
    p1 = 1 - (1 - p_) ** nn
    return (f"Un test comporte {nn} questions indépendantes ; pour chacune, la probabilité de répondre correctement au hasard est {dec(p_, 1)}. On note X le nombre de bonnes réponses.\n\n"
            + lst(["Justifier que X suit une loi binomiale dont on précisera les paramètres.", f"Calculer P(X = {k}) à 10⁻⁴ près.", "Calculer la probabilité d'obtenir au moins une bonne réponse (à 10⁻⁴ près).", "Calculer E(X)."]),
            "Solution :\n\n" + lst([f"On répète {nn} fois la même épreuve de Bernoulli (succès de probabilité {dec(p_, 1)}) de façon indépendante : X suit B({nn} ; {dec(p_, 1)}).",
                                    f"P(X = {k}) = C({nn},{k}) × {dec(p_, 1)}^{k} × {dec(1 - p_, 1)}^{nn - k} ≈ {dec(pk, 4)}.", f"P(X ≥ 1) = 1 {M} {dec(1 - p_, 1)}^{nn} ≈ {dec(p1, 4)}.", f"E(X) = {nn} × {dec(p_, 1)} = {dec(nn * p_, 1)}."]))


def denombrement(v):
    w, h, k, j = [(6, 4, 3, 2), (7, 5, 4, 2), (8, 6, 5, 3)][v]
    tot, ex, al = comb(w + h, k), comb(w, j) * comb(h, k - j), comb(w + h, k) - comb(h, k)
    return (f"Un comité de {k} personnes est choisi parmi {w + h} candidats : {w} femmes et {h} hommes.\n\n"
            + lst(["Combien de comités différents peut-on former ?", f"Combien de comités comportent exactement {j} femmes ?", "Combien de comités comportent au moins une femme ?"]),
            "Solution :\n\n" + lst([f"C({w + h},{k}) = {tot}.", f"C({w},{j}) × C({h},{k - j}) = {comb(w, j)} × {comb(h, k - j)} = {ex}.", f"Total {M} comités sans femme = {tot} {M} C({h},{k}) = {tot} {M} {comb(h, k)} = {al}."]))


def synthese(v):
    a, expo2 = [(1, 1), (2, 1), (1, 2)][v]
    if v < 2:
        fx = "x e^(−x)" if a == 1 else "x e^(−2x)"
        x0, fm = F(1, a), 1 / (a * e)
        return (f"**Problème.** Soit f la fonction définie sur ℝ par f(x) = {fx}.\n\n"
                + lst(["Déterminer la limite de f en −∞, puis en +∞ (on admettra que x e^(−x) → 0 quand x → +∞)." if a == 1 else "Déterminer la limite de f en −∞, puis en +∞ (on admettra que x e^(−2x) → 0 quand x → +∞).",
                       "Calculer f'(x) et dresser le tableau de variations de f.", "En déduire que f admet un maximum et donner sa valeur exacte, puis une valeur approchée à 10⁻³ près."]),
                "Solution :\n\n" + lst([f"En −∞ : x → {M}∞ et e^(−{'' if a == 1 else '2'}x) → +∞, donc f(x) → {M}∞. En +∞ : f(x) → 0.",
                                        f"f'(x) = e^(−{'' if a == 1 else '2'}x) {M} {'' if a == 1 else '2'}x e^(−{'' if a == 1 else '2'}x) = (1 {M} {'' if a == 1 else '2'}x)e^(−{'' if a == 1 else '2'}x). Elle est positive pour x < {n(x0)} et négative ensuite : "
                                        f"f est croissante sur ]{M}∞ ; {n(x0)}] et décroissante sur [{n(x0)} ; +∞[.",
                                        f"f admet un maximum en x = {n(x0)} : f({n(x0)}) = {'' if a == 1 else '(1/2)'}e^(−1) = {'1/e' if a == 1 else '1/(2e)'} ≈ {dec(fm, 3)}."]))
    return ("**Problème.** Soit f la fonction définie sur ℝ par f(x) = x² e^(−x).\n\n"
            + lst(["Déterminer la limite de f en −∞ (on admettra que x² e^(−x) → 0 quand x → +∞ pour la limite en +∞).", "Montrer que f'(x) = x(2 − x)e^(−x).", "Dresser le tableau de variations de f.", "Préciser les extremums locaux (valeurs exactes puis approchées à 10⁻³ près)."]),
            "Solution :\n\n" + lst([f"En −∞ : x² → +∞ et e^(−x) → +∞, donc f(x) → +∞. En +∞ : f(x) → 0.", "f'(x) = 2x e^(−x) − x² e^(−x) = x(2 − x)e^(−x).",
                                    f"e^(−x) > 0 : f' a le signe de x(2 {M} x). f est décroissante sur ]{M}∞ ; 0], croissante sur [0 ; 2], décroissante sur [2 ; +∞[.",
                                    f"Minimum local f(0) = 0 ; maximum local f(2) = 4e^(−2) ≈ {dec(4 * exp(-2), 3)}."]))


# ───────────── Familles complémentaires (au moins 2 thèmes par séquence et par classe) ─────────────
def vecteurs(v):
    (a, b), (c, d), extra = [((2, 3), (1, -4), None), ((-3, 6), (2, -4), None), ((4, -2), (-6, 3), 6)][v]
    det = a * d - b * c
    qs = ["Calculer les coordonnées de u + v et de 2u − v.", "Les vecteurs u et v sont-ils colinéaires ? Justifier."]
    ss = [f"u + v a pour coordonnées ({n(a + c)} ; {n(b + d)}) et 2u {M} v a pour coordonnées ({n(2 * a - c)} ; {n(2 * b - d)}).",
          f"Déterminant : {n(a)}×{par(d)} {M} {par(b)}×{par(c)} = {n(det)}. " + ("Il est nul : u et v sont colinéaires." if det == 0 else "Il n'est pas nul : u et v ne sont pas colinéaires.")]
    if extra:
        k = F(-b * extra, a) * 0 + F(extra * a * 0 + (-(a * extra)), -b)  # k tel que a*extra - b*k = 0  ->  k = a*extra/b
        k = F(a * extra, b)
        assert a * extra - b * k == 0
        qs.append(f"Déterminer le réel k tel que u et w(k ; {extra}) soient colinéaires.")
        ss.append(f"u et w colinéaires ⇔ {n(a)}×{extra} {M} {par(b)}×k = 0 ⇔ k = {n(k)}.")
    return (f"Dans un repère orthonormé, on considère les vecteurs u({n(a)} ; {n(b)}) et v({n(c)} ; {n(d)}).\n\n" + lst(qs), "Solution :\n\n" + lst(ss))


def systemes(v):
    a, b, e, c, d, f = [(1, 1, 3, 1, -1, 1), (2, 3, 12, 1, -1, 1), (3, -2, 4, 5, 4, 14)][v]
    det = a * d - b * c
    x, y = F(e * d - b * f, det), F(a * f - c * e, det)
    assert a * x + b * y == e and c * x + d * y == f
    eq = lambda p_, q_, r_: f"{lin([(p_, 'x'), (q_, 'y')])} = {n(r_)}"
    by = ("" if abs(b) == 1 else n(abs(b))) + "y"
    return (f"**Système d'équations.** Résoudre dans ℝ² le système suivant, en éliminant une inconnue par combinaison linéaire :\n\n"
            f"- (L1) {eq(a, b, e)}\n- (L2) {eq(c, d, f)}",
            "Solution :\n\n"
            f"- On élimine y : (L1)×{par(d)} {M} (L2)×{par(b)} donne {n(det)}x = {n(e * d - b * f)}, d'où x = {n(x)}.\n"
            f"- En reportant dans (L1) : {n(a)}×{par(x)} {'+' if b > 0 else M} {by.replace('y', '')}{'y'} = {n(e)}, d'où y = {n(y)}.\n"
            f"- Vérification dans (L2) : {n(c)}×{par(x)} {'+' if d > 0 else M} {abs(d)}×{par(y)} = {n(c * x + d * y)} ✓.\n\n"
            f"Conclusion : (x ; y) = ({n(x)} ; {n(y)}).")


def inverse(v):
    a1, a2, c = [(2, 4, 5), (F(1, 3), 3, 10), (5, 2, F(1, 4))][v]
    a1, a2, c = F(a1), F(a2), F(c)
    small, big = sorted([a1, a2])
    return (f"Soit f la fonction inverse définie sur ]0 ; +∞[ par f(x) = 1/x.\n\n"
            + lst([f"Calculer f({n(a1)}) et f({n(a2)}).", f"Déterminer l'antécédent de {n(c)} par f.", f"Comparer f({n(small)}) et f({n(big)}). Que peut-on en déduire pour le sens de variation de f ?"]),
            "Solution :\n\n" + lst([f"f({n(a1)}) = {n(1 / a1)} et f({n(a2)}) = {n(1 / a2)}.", f"f(x) = {n(c)} ⇔ 1/x = {n(c)} ⇔ x = {n(1 / c)}.",
                                    f"f({n(small)}) = {n(1 / small)} > f({n(big)}) = {n(1 / big)} alors que {n(small)} < {n(big)} : l'ordre est inversé, ce qui illustre que f est strictement décroissante sur ]0 ; +∞[."]))


def droite(v):
    A, B, C = [((1, 2), (3, 6), (4, 8)), ((-1, 3), (2, -3), (3, -4)), ((0, 5), (4, 2), (8, -1))][v]
    m = F(B[1] - A[1], B[0] - A[0])
    p_ = A[1] - m * A[0]
    assert B[1] == m * B[0] + p_
    inside = C[1] == m * C[0] + p_
    P = lambda t: f"({n(t[0])} ; {n(t[1])})"
    mx = poly([m, p_]).replace("(", "(").replace(")", ")")
    return (f"Dans un repère orthonormé, on considère les points A{P(A)}, B{P(B)} et C{P(C)}.\n\n"
            + lst(["Calculer le coefficient directeur de la droite (AB).", "Déterminer une équation réduite de (AB).", "Le point C appartient-il à la droite (AB) ?"]),
            "Solution :\n\n" + lst([f"m = (y_B {M} y_A)/(x_B {M} x_A) = ({n(B[1])} {M} {par(A[1])})/({n(B[0])} {M} {par(A[0])}) = {n(m)}.",
                                    f"y = {mx} : en effet, A appartient à la droite, donc {n(A[1])} = {n(m)}×{par(A[0])} + p, d'où p = {n(p_)}.",
                                    f"Pour x = {n(C[0])} : {n(m)}×{par(C[0])} + {par(p_)} = {n(m * C[0] + p_)} " + ("= " + n(C[1]) + " : C appartient à (AB)." if inside else f"≠ {n(C[1])} : C n'appartient pas à (AB).")]))


def suite_def(v):
    a, b, c = [(1, 3, 0), (3, 0, -2), (-2, 0, 10)][v]
    u = lambda k: a * k * k + b * k + c
    diff = [2 * a, a + b]
    assert all(u(k + 1) - u(k) == diff[0] * k + diff[1] for k in range(10))
    pos = all(diff[0] * k + diff[1] > 0 for k in range(10))
    neg = all(diff[0] * k + diff[1] < 0 for k in range(10))
    assert pos or neg
    return (f"Soit (u_n) la suite définie pour tout entier naturel n par u_n = {poly([a, b, c], 'n')}.\n\n"
            + lst(["Calculer u₀, u₁ et u₂.", "Exprimer u_{n+1} − u_n en fonction de n.", "En déduire le sens de variation de la suite (u_n)."]),
            "Solution :\n\n" + lst([f"u₀ = {n(u(0))}, u₁ = {n(u(1))}, u₂ = {n(u(2))}.", f"u_{{n+1}} {M} u_n = {poly([diff[0], diff[1]], 'n')}.",
                                    f"Pour tout n ≥ 0, {poly([diff[0], diff[1]], 'n')} est {'strictement positif' if pos else 'strictement négatif'} : la suite (u_n) est strictement {'croissante' if pos else 'décroissante'}."]))


def deriv_prod(v):
    a_, p_, q_ = [(1, 2, -3), (-2, 3, 1), (4, -1, 2)][v]
    f = lambda x: (x * x + a_) * (p_ * x + q_)
    coefs = [3 * p_, 2 * q_, a_ * p_]
    for x in range(-3, 4):
        h = 1e-6
        assert abs((f(x + h) - f(x - h)) / (2 * h) - (coefs[0] * x * x + coefs[1] * x + coefs[2])) < 1e-4
    fp1 = sum(coefs)
    return (f"Soit f la fonction définie sur ℝ par f(x) = (x² {'+' if a_ > 0 else M} {abs(a_)})({poly([p_, q_])}).\n\n"
            + lst(["En utilisant la formule de dérivation d'un produit, calculer f'(x).", "Calculer f'(1)."]),
            "Solution :\n\n" + lst([f"f = u×v avec u(x) = x² {'+' if a_ > 0 else M} {abs(a_)} et v(x) = {poly([p_, q_])} ; u'(x) = 2x et v'(x) = {n(p_)}. "
                                    f"f'(x) = u'v + uv' = 2x({poly([p_, q_])}) + {par(p_)}(x² {'+' if a_ > 0 else M} {abs(a_)}) = {poly(coefs)}.",
                                    f"f'(1) = {n(coefs[0])} + {par(coefs[1])} + {par(coefs[2])} = {n(fp1)}."]))


def suite_geo_p(v):
    u0, q, k, m_ = [(2, 3, 4, 5), (5, 2, 5, 6), (81, F(1, 3), 3, 4)][v]
    u0, q = F(u0), F(q)
    uk = u0 * q ** k
    S = sum(u0 * q ** i for i in range(m_ + 1))
    assert S == u0 * (1 - q ** (m_ + 1)) / (1 - q)
    return (f"Soit (u_n) la suite géométrique de premier terme u₀ = {n(u0)} et de raison q = {n(q)}.\n\n"
            + lst(["Exprimer u_n en fonction de n.", f"Calculer u_{k}.", f"Calculer S = u₀ + u₁ + … + u_{m_}."]),
            "Solution :\n\n" + lst([f"u_n = u₀ × q^n = {n(u0)} × ({n(q)})^n.", f"u_{k} = {n(u0)} × ({n(q)})^{k} = {n(uk)}.",
                                    f"S = u₀ × (1 {M} q^{m_ + 1})/(1 {M} q) = {n(u0)} × (1 {M} ({n(q)})^{m_ + 1})/(1 {M} {par(q)}) = {n(S)}."]))


def suite_lim(v):
    num, den, n0, lim = [((2, 1), (1, 3), 0, 2), ((3, 0, 1), (1, 1, 0), 1, 3), ((4, 7), (2, 1), 0, 2)][v]
    pol = lambda cs, k: sum(F(c) * k ** (len(cs) - 1 - i) for i, c in enumerate(cs))
    u = lambda k: pol(num, k) / pol(den, k)
    assert abs(float(u(10 ** 6)) - lim) < 1e-3
    deg = len(num) - 1
    nd = "n²" if deg == 2 else "n"
    f_num, f_den = poly(list(num), "n"), poly(list(den), "n")
    return (f"Soit (u_n) la suite définie pour tout entier n ≥ {n0} par u_n = ({f_num})/({f_den}).\n\n"
            + lst([f"Calculer u_{n0} et u_{n0 + 1}.", "Déterminer la limite de (u_n) en factorisant numérateur et dénominateur par le terme de plus haut degré."]),
            "Solution :\n\n" + lst([f"u_{n0} = {n(u(n0))} et u_{n0 + 1} = {n(u(n0 + 1))}.",
                                    f"On factorise par {nd} au numérateur et au dénominateur : u_n = ({n(num[0])} + termes qui tendent vers 0)/({n(den[0])} + termes qui tendent vers 0). "
                                    f"Les termes en 1/n et 1/n² tendent vers 0, donc u_n tend vers {n(num[0])}/{n(den[0])} = {n(lim)}."]))


def vec_espace(v):
    A, B, C = [((1, 2, 3), (3, -1, 4), (5, -4, 5)), ((0, 1, -2), (2, 3, 0), (1, 2, 1)), ((-1, 0, 2), (1, 2, 6), (2, 3, 8))][v]
    AB = tuple(B[i] - A[i] for i in range(3))
    AC = tuple(C[i] - A[i] for i in range(3))
    k = None
    for i in range(3):
        if AB[i] != 0:
            k = F(AC[i], AB[i])
            break
    aligned = all(AC[i] == k * AB[i] for i in range(3))
    nn = sum(c * c for c in AB)
    T = lambda t: "(" + " ; ".join(n(c) for c in t) + ")"
    return (f"L'espace est muni d'un repère orthonormé. On considère les points A{T(A)}, B{T(B)} et C{T(C)}.\n\n"
            + lst(["Calculer les coordonnées du vecteur AB, puis la distance AB.", "Les points A, B et C sont-ils alignés ?"]),
            "Solution :\n\n" + lst([f"AB a pour coordonnées {T(AB)} et AB = √({' + '.join(par(c) + '²' for c in AB)}) = {radeq(nn)}.",
                                    f"AC a pour coordonnées {T(AC)}. " + (f"On a AC = {n(k)} × AB : les vecteurs sont colinéaires, donc A, B et C sont alignés." if aligned
                                                                         else "Les coordonnées de AC et AB ne sont pas proportionnelles : les vecteurs ne sont pas colinéaires, donc A, B et C ne sont pas alignés.")]))


# (classe, partie, séquence, constructeur, spécialités par variante)
AUCUNE, MATHS, PC = "SPECIAL:Aucune", "Mathématiques", "Physique-Chimie"
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
NIVEAUX = ["Facile", "Moyen", "Difficile"]


def exercices() -> list:
    out = []
    for classe, partie, seq, build in FAMILLES:
        for v in range(3):
            sujet, corrige = build(v)
            if build is diffeq:
                specs = [MATHS, PC]
            elif classe != "Seconde" and v == 2:
                specs = [MATHS]                       # variante la plus difficile : enseignement de spécialité
            else:
                specs = [AUCUNE]
            out.append({"classe": classe, "partie": partie, "session": seq, "niveau": NIVEAUX[v], "sujet": sujet, "corrige": corrige,
                        "specialites": specs, "tag": seq is not None and (v == 2 or (v == 1 and seq in (3, 6)))})
    return out
