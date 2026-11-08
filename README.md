# Générateur d'épreuves (cahier des charges V4.11)

Plateforme web qui assemble des épreuves uniques à partir d'une banque d'exercices individuels.
Stack légère et 100 % libre : **Python (testé en 3.12), FastAPI, SQLite, Polars** (filtres d'éligibilité), interface HTML/JS sans build.

## Démarrage

```bash
pip install -r requirements.txt
python -m app.seed            # (facultatif) données fictives de démonstration
EXAMGEN_ADMIN_TOKEN=monjeton python -m app    # http://127.0.0.1:8000  (admin : /admin)
```

Variables : `EXAMGEN_DB` (défaut `examgen.db`), `EXAMGEN_ADMIN_TOKEN` (sinon généré et affiché au démarrage), `HOST`, `PORT`.
Tests : `pip install -r requirements-dev.txt && pytest`.

## Organisation

| Fichier | Rôle |
|---|---|
| `app/generator.py` | Algorithme §4 / 7.4 (pur, sans E/S) |
| `app/service.py` | Génération, historique d'unicité, journal, purge |
| `app/repo.py` | CRUD et intégrité référentielle (blocage + réaffectation, anti-cycle) |
| `app/bank_io.py`, `app/schema/bank.schema.json` | Import/export JSON (schéma 1.1, draft-07) |
| `app/main.py` | API REST + pages (`/`, `/admin`, `/epreuve/{id}`, `/epreuve/{id}/corrige`) |
| `docs/CAHIER_V4.11_AMENDEMENTS.md` | Corrections du cahier, interprétations, points à arbitrer |

## Déploiement et tests navigateur

Guide pas à pas (VM gratuite persistante, Render, sauvegardes, sécurité) : `docs/DEPLOIEMENT.md`.
Test navigateur complet (utilisateur + administration, avec captures) : `bash e2e/run.sh` (Node 18+, Chromium embarqué téléchargé via npm).

## Formules et structures (maths, chimie)

Indices, exposants, fractions, formules moléculaires, ions, équations-bilans, unités : écrits en LaTeX entre `$…$` et rendus par KaTeX
(embarqué, hors ligne), écran et impression. Chimie : formules brutes et semi-développées, schémas de Lewis, structures dessinées
(topologique, développée, Cram) à partir d'un SMILES, images téléversées. Éditeur avec barre d'outils, aperçu en direct et aide. Guide : `docs/FORMULES.md`.

## Limites connues

Pas de compte utilisateur (cookie anonyme) ; pas de tracé de courbes (images possibles) ; interface non testée automatiquement dans un navigateur ;
SQLite (un seul serveur). Voir les points à arbitrer dans `docs/`.
