# Écrire des formules (mathématiques, chimie, physique)

Les énoncés et corrigés sont en **Markdown** ; les formules s'écrivent en **LaTeX entre dollars** et sont mises en forme
par KaTeX (embarqué dans l'application : aucun accès internet requis), à l'écran comme à l'impression.
Dans l'éditeur d'exercice, un **aperçu en direct** s'affiche sous chaque zone de texte, et un encart **Aide** donne les exemples ci-dessous avec leur rendu.

| Je veux | J'écris | On obtient |
|---|---|---|
| formule dans une phrase | `$u_1$` | u₁ |
| formule centrée sur sa ligne | `$$\int_0^1 x\,\mathrm{d}x$$` | formule sur sa propre ligne |
| indice (un caractère / plusieurs) | `$u_1$`, `$u_{n+1}$` | u₁, uₙ₊₁ |
| exposant | `$x^2$`, `$10^{-4}$` | x², 10⁻⁴ |
| exponentielle (e droit) | `$\mathrm{e}^{2x}$` | e²ˣ |
| fraction, racine | `$\frac{a}{b}$`, `$\sqrt{14}$` | a/b (empilée), √14 |
| ensembles | `$\R$`, `$\N$`, `$\Z$`, `$\Q$`, `$\C$` | ℝ, ℕ, ℤ, ℚ, ℂ |
| intervalle | `$[0\,;\,+\infty[$` | [0 ; +∞[ |
| virgule décimale française | `$0{,}368$` | 0,368 (sans espace parasite) |
| vecteur | `$\vec{u}$`, `$\overrightarrow{AB}$` | u⃗, AB⃗ |
| combinaison, somme, limite | `$\binom{n}{k}$`, `$\sum_{k=0}^{n}$`, `$\lim_{x \to +\infty}$` | C(n,k), Σ, lim |
| système d'équations | `$$\begin{cases} x + y = 3 \\ x - y = 1 \end{cases}$$` | accolade |

## Chimie et unités (extension mhchem)

| Je veux | J'écris | On obtient |
|---|---|---|
| formule moléculaire | `$\ce{H2O}$`, `$\ce{C6H12O6}$` | H₂O, C₆H₁₂O₆ |
| ion | `$\ce{SO4^2-}$`, `$\ce{Na+}$`, `$\ce{H3O+}$` | SO₄²⁻, Na⁺, H₃O⁺ |
| équation de réaction | `$\ce{CH4 + 2O2 -> CO2 + 2H2O}$` | flèche et indices automatiques |
| état physique | `$\ce{NaCl(s) -> Na+(aq) + Cl-(aq)}$` | (s), (aq) |
| équilibre | `$\ce{H3O+ + HO- <=> 2H2O}$` | ⇌ |
| unité | `$\pu{mol.L-1}$`, `$\pu{m.s-1}$`, `$\pu{km.h-1}$` | mol·L⁻¹, m·s⁻¹, km·h⁻¹ |
| valeur avec unité | `$36{,}0\,\pu{g}$`, `$2{,}4 \times 10^{5}\,\pu{J}$` | 36,0 g ; 2,4 × 10⁵ J |
| concentration | `$[\ce{H3O+}] = 1{,}0 \times 10^{-3}\,\pu{mol.L-1}$` | [H₃O⁺] = … |

## À savoir

- **Ne pas écrire** `u_1` ou `x^2` en dehors des dollars : ce serait du texte brut. Un `$` isolé (« 5 $ ») reste du texte ; pour un `$` littéral, écrire `\$`.
- Le texte dans une formule : `$x \text{ ou } y$`. Les mots hors formule restent en dehors des dollars.
- Les `_` et `*` à l'intérieur d'une formule ne sont **jamais** interprétés comme du Markdown (italique/gras).
- Raccourcis disponibles partout : `\R`, `\N`, `\Z`, `\Q`, `\C` (fichier `app/static/katex/macros.js`).
- Non géré : figures et courbes (insérer une image n'est pas prévu), tableaux de variations (utiliser un tableau Markdown ou `\begin{array}`).
- Vérification : `pytest` contrôle chaque formule de la banque de démonstration avec le même KaTeX que le navigateur ; une syntaxe invalide fait échouer le test.
- Licence : KaTeX et mhchem sont sous licence MIT (`app/static/katex/LICENSE`).
