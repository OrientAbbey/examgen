# Cahier des charges — Amendements V4.10 → V4.11

Le V4.10 se déclare « sans ambiguïté résiduelle » ; la lecture critique en a trouvé plusieurs, dont certaines **bloquantes pour l'implémentation**. Ce document liste (A) les corrections appliquées, (B) les interprétations retenues faute de précision, (C) les points qui demandent **votre arbitrage**. Le reste du V4.10 est repris tel quel.

## A. Corrections (incohérences / omissions du V4.10)

| # | Section | Problème | Correction V4.11 |
|---|---|---|---|
| 1 | 2.1 | Liste « Séquence / Session » sans *Examen blanc*, alors que 4.0 et 4.h le traitent | Valeurs : vide, Séquence 1-6, **Examen blanc**, Examen (comportement identique) |
| 2 | 2.1 | Tableau Difficulté illisible | Facile = 2, Moyen = 4, Difficile = 6 (déduit de 4.g : N = 2, 4 ou 6) |
| 3 | 3.1 / 7.2 | Un exercice peut avoir **plusieurs matières mais une seule partie** ; or une partie appartient à une seule matière (3.2.b) : les autres matières seraient inatteignables par 4.a | **Une partie par matière** (`affectations: [{matiereId, partieId}]`). Schéma JSON passé en **1.1** (`matiereIds`/`partieId` supprimés) |
| 4 | 4.a exc. 2 | « au moins ⌊N/P⌋ et au plus ⌊N/P⌋ » (deux fois la même borne) | Au moins ⌊N/P⌋, au plus ⌈N/P⌉ ; exactement N mod P parties ont l'occurrence supplémentaire |
| 5 | 4.m | Les phases 1 et 2a ne citent pas 4.a, 4.e, 4.f, 4.k : ces règles pouvaient donc être violées par la règle des 50 % | **Toutes** les contraintes s'appliquent à **chaque** phase |
| 6 | 4.d / 4.l | 4.l (exclusion des classes inférieures sans spécialité) est **entièrement neutralisée** par 4.d (Aucune prime) : règle sans effet | Fusion en une règle : exercice éligible ⇔ `Aucune ∈ spécialités` ou `spécialité de l'utilisateur ∈ spécialités`. Champ vide ⇒ exercices *Aucune* uniquement. Au moins une valeur de spécialité par exercice |
| 7 | 7.1 / 7.3 | 7.1 énumère 4 types d'événements, 7.3 en ajoute un (`INFO_HISTORY_PURGED`) ; clé `difículte` | 5 types ; clé `difficulte` |
| 8 | 4.0 | Tableau sans colonne « exercice de session vide » (décrite seulement dans les règles de lecture) | Colonne ajoutée : éligible à Examen / Examen blanc / session vide, exclu des séquences 1-6 |
| 9 | 2.2 vs §6 | « Aucun message dans aucun cas » contredit « le formulaire bloque la soumission » | Bouton **Générer inactif** tant que le formulaire est incomplet, sans message. Seule exception : panne technique (réseau / erreur 5xx) → message neutre « Service indisponible » |
| 10 | — | « Par utilisateur » (4.i) sans notion d'utilisateur ni d'authentification | Utilisateur = identifiant anonyme en cookie (10 ans). Administration protégée par jeton (`EXAMGEN_ADMIN_TOKEN`) |

## B. Interprétations retenues (à confirmer)

1. **Phase 1 (4.g)** : les N/2 exercices de la séquence exacte viennent de la **classe demandée** uniquement (jamais d'une classe inférieure), cohérent avec 4.f et 4.g.
2. **Classes inférieures et session vide** : exclues (4.c : « uniquement Seq 5-6 »), y compris en Examen.
3. **4.k Facile « encourage »** : poids ×2 pour les exercices de classes inférieures éligibles (constante `FACILE_BONUS_CLASSE_INFERIEURE`).
4. **Nombre de parties P** : calculé sur les exercices **éligibles** (pas sur les parties configurées).
5. **Tirage des parties** : aléatoire via le tirage pondéré des exercices (7.4) ; une partie riche en exercices est donc plus probable qu'une partie pauvre. Un tirage uniforme des parties est possible mais contredit la formule 7.4.
6. **Unicité** : jusqu'à 50 tirages successifs pour éviter un multiensemble déjà généré par l'utilisateur (tous paramètres confondus) ; au-delà → doublon silencieux + `UNIQUENESS_SATURATED`.
7. **Ordre d'affichage** : par ordre des parties puis ordre de tirage ; sujet et corrigé affichent « Exercice n » (même numérotation). Le contenu est **figé** à la génération (une modification ultérieure de la banque ne change pas une épreuve déjà générée).
8. **« Classes de même niveau »** (3.1) : lu comme une faculté, non comme une contrainte validée.
9. **Markdown** : HTML brut désactivé (sécurité) ; pas de rendu LaTeX pour l'instant.

## C. Points à arbitrer (non tranchés par le V4.10)

1. **4.a sans relâchement** : si une partie manque d'exercices (ex. P = 2, N = 6, une partie n'a qu'1 exercice), l'épreuve sort **incomplète (4 exercices)** alors que la banque en contient plus. Le cahier ne prévoit de relâchement que pour 4.g. Faut-il relâcher 4.a en dernier recours ?
2. **Décision 26 (2b sautée après échec de 2a)** : peut laisser 1-2 exercices de classes inférieures inutilisés alors qu'ils seraient éligibles. Voulu ?
3. **Table 7.4, ligne Moyen = 1/3/1** : asymétrique par rapport aux lignes Facile (3/2/1) et Difficile (1/2/3) ; une ligne 2/3/2 serait plus symétrique. Valeur du V4.10 conservée.
4. **Comptes utilisateurs** : l'identité par cookie perd l'historique si le cookie est effacé. Authentification réelle souhaitée ?
