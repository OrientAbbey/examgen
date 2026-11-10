# Assistant IA

L'assistant est **facultatif** : il est désactivé tant qu'aucun fournisseur n'est configuré, et l'application fonctionne exactement comme avant.
Il n'est branché sur aucun service particulier : vous choisissez le fournisseur (modèle local gratuit ou service en ligne).

## Ce qu'il fait

**Pour l'administrateur** (éditeur d'exercice, panneau « ✨ Assistant IA », et onglet *Couverture*)

| Action | Résultat |
|---|---|
| Générer un exercice | Énoncé + corrigé d'après la matière, la partie, les classes, la spécialité, la séquence, le niveau et une consigne libre. Un exercice de la banque sert de modèle de style. |
| Vérifier le corrigé | L'assistant refait les calculs, liste les erreurs et propose un corrigé corrigé. |
| Normaliser (LaTeX) | Réécrit les notations selon les règles (LaTeX, virgule décimale, unités, chimie) **sans changer le fond** : utile pour convertir une ancienne banque. |
| Variantes | 2 à 5 variantes (autres valeurs numériques), corrigés recalculés. |
| Suggérer niveau / séquence | Niveau, séquence, partie, classes, tag Examen. Les identifiants proposés sont revalidés contre la base. |
| Réparer la syntaxe | Proposé automatiquement quand une formule d'une proposition est invalide. |
| Couverture | Tableau classe × partie × séquence ; les cases sous 3 exercices sont des lacunes. Un clic ouvre l'éditeur prérempli, où l'assistant peut rédiger l'exercice. |

**Pour l'utilisateur** (page de génération, si l'assistant est ouvert au public)

- *Décrivez l'épreuve souhaitée* : « une épreuve de maths niveau moyen pour la Terminale, séquence 3 » **remplit le formulaire**. L'utilisateur vérifie puis clique lui-même sur Générer : l'assistant ne tire jamais d'exercices à sa place (le tirage reste l'algorithme du cahier des charges).
- *Barème et durée* : proposition de barème sur 20 points et de durée pour l'épreuve générée.

Tout ce que produit l'assistant est un **brouillon**. Rien n'est enregistré sans clic de l'administrateur.

## Configuration

| Variable | Rôle |
|---|---|
| `EXAMGEN_LLM_MODEL` | Nom du modèle chez le fournisseur (**obligatoire**) |
| `EXAMGEN_LLM_BASE_URL` | URL de l'API (obligatoire en mode `openai`) |
| `EXAMGEN_LLM_API_KEY` | Clé d'API (obligatoire en mode `anthropic`, facultative pour un modèle local) |
| `EXAMGEN_LLM_PROVIDER` | `openai` (défaut : tout service compatible `/chat/completions`) ou `anthropic` |
| `EXAMGEN_LLM_TIMEOUT` / `EXAMGEN_LLM_MAX_TOKENS` | Délai (90 s) et longueur maximale de réponse (3000 jetons) |
| `EXAMGEN_LLM_JSON_MODE` | `1` si votre serveur accepte `response_format: json_object` (facultatif) |
| `EXAMGEN_AI_PUBLIC` | `0` pour réserver l'assistant à l'administration (défaut `1`) |
| `EXAMGEN_AI_PUBLIC_PER_MIN` / `EXAMGEN_AI_ADMIN_PER_MIN` | Appels par minute et par IP (10 / 30) |

Exemples :

```bash
# Modèle local gratuit avec Ollama (https://ollama.com) : télécharger un modèle, puis
EXAMGEN_LLM_BASE_URL=http://localhost:11434/v1  EXAMGEN_LLM_MODEL=<nom-du-modèle-téléchargé>  python -m app

# Service en ligne compatible OpenAI (URL, clé et nom de modèle fournis par le service)
EXAMGEN_LLM_BASE_URL=https://…/v1  EXAMGEN_LLM_API_KEY=…  EXAMGEN_LLM_MODEL=…  python -m app

# API Anthropic
EXAMGEN_LLM_PROVIDER=anthropic  EXAMGEN_LLM_API_KEY=…  EXAMGEN_LLM_MODEL=<modèle>  python -m app
```

Vérification : *Administration → Réglages → Tester la connexion*.

Choix du fournisseur :
- **Un modèle local** (Ollama, LM Studio…) est gratuit et garde les données chez vous, mais demande une machine capable de l'exécuter : sur un PC modeste, préférez un petit modèle (qualité limitée en mathématiques) ou un service en ligne. Les VM gratuites d'hébergement n'ont en général pas assez de ressources pour un modèle utile.
- **Un service en ligne** : plusieurs proposent une offre gratuite limitée ; les conditions changent, vérifiez-les. Les textes d'exercices quittent alors votre serveur.
- En Docker, pour joindre un Ollama installé sur l'hôte : `EXAMGEN_LLM_BASE_URL=http://host.docker.internal:11434/v1` (déjà autorisé par `docker-compose.yml`).

## Données transmises au fournisseur

- Actions d'administration : le texte du sujet et du corrigé en cours d'édition, les noms de matière, partie, classes, spécialité, un exemple d'exercice de la banque, et la consigne saisie.
- Page utilisateur : le texte de la demande (600 caractères maximum) et la liste des noms de matières, classes et spécialités ; pour le barème, le texte des exercices de l'épreuve.
- **Jamais** : la clé d'API (elle ne quitte pas le serveur, n'apparaît ni dans les réponses ni dans le journal), le jeton administrateur, l'identifiant des utilisateurs, l'historique.

## Sécurité et fiabilité

- Désactivé par défaut ; clé uniquement dans l'environnement du serveur.
- Les contenus transmis (exercices, demande de l'utilisateur) sont balisés comme **données** et le modèle reçoit l'ordre de ne jamais leur obéir. Surtout, **tout ce qu'il renvoie est revalidé** : identifiants contre la base, séquences et difficultés contre les valeurs permises, nombres du barème bornés, total recalculé côté serveur. Une demande piégée ne peut donc rien faire d'autre que remplir un formulaire.
- Les textes d'exercices sont échangés en sections (`=== SUJET ===`, `=== CORRIGE ===`…) et non en JSON : dans un JSON, les `\frac`, `\times` ou `\neq` du LaTeX seraient silencieusement déformés en saut de page, tabulation ou saut de ligne.
- Contrôles automatiques de chaque proposition : « Solution : » en tête du corrigé, symboles Unicode mathématiques, dollars non appariés, formules hors `$…$`, structures SMILES invalides, puis formules invalides détectées dans le navigateur (avec réparation guidée).
- Limites de débit par IP ; une relance automatique sur erreur 429/5xx ; une relance si le format de réponse n'est pas respecté.
- Chaque appel est tracé dans le journal (`AI_ACTION` : action, durée, erreur éventuelle), sans contenu ni secret.

## Limites à connaître

- Un modèle peut se tromper, surtout en calcul : *Vérifier le corrigé* est un **deuxième avis**, pas une preuve. Relisez toujours avant d'enregistrer.
- Les petits modèles locaux respectent parfois mal le format (erreur `AI_BAD_RESPONSE`) : réessayez ou changez de modèle.
- L'assistant ne produit pas d'images ; pour les schémas, utilisez le bouton 🖼 de l'éditeur.
- Je n'ai pu tester qu'avec un **faux fournisseur local** (`tests/fake_llm.py`, protocoles OpenAI et Anthropic) : le circuit complet est vérifié, pas la qualité des réponses d'un vrai modèle.

## Codes d'erreur

`AI_DESACTIVE` non configuré · `AI_PUBLIC_DESACTIVE` réservé à l'administration · `AI_UPSTREAM` le fournisseur a répondu une erreur HTTP · `AI_INDISPONIBLE` fournisseur injoignable ou trop lent ·
`AI_BAD_RESPONSE` réponse inexploitable (après relance) · `RATE_LIMIT` trop d'appels.

## Tester sans fournisseur

```bash
python tests/fake_llm.py 8781 &       # faux fournisseur : réponses de démonstration déterministes
EXAMGEN_LLM_BASE_URL=http://127.0.0.1:8781/v1 EXAMGEN_LLM_MODEL=demo python -m app
```
(`bash e2e/run.sh` le fait automatiquement.)
