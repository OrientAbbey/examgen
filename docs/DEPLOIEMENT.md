# Déploiement gratuit

*Offres vérifiées le 06/11/2026 (documentation Render + comparatifs 2026). Les conditions gratuites changent souvent : revérifiez avant de vous engager.*

## Quel hébergeur ?

L'application stocke ses données dans **SQLite** (un fichier). Il lui faut donc un **disque persistant**.

| Option | Coût | Données conservées ? | Quand la choisir |
|---|---|---|---|
| **A. VM « Always Free »** (Oracle Cloud, Google Cloud e2-micro) | 0 € (carte bancaire demandée pour vérification) | **Oui** (disque de la VM) | **Recommandé** : usage réel avec élèves/enseignants |
| **B. Render (plan gratuit)** | 0 € | **Banque : oui** (restaurée depuis Git). **Historique d'unicité + journal : non** (perdus à chaque redémarrage) | Démo rapide, pas de carte nécessaire pour tester |
| C. Votre PC | 0 € | Oui | Essai local : `python -m app` |

Points d'attention :
- **Render gratuit** : mise en veille après 15 min sans trafic (réveil ≈ 1 min), disque éphémère, pas de disque persistant.
- **Oracle** : peut récupérer une instance gratuite restée très inactive plusieurs jours → gardez les sauvegardes JSON hors de la VM.
- **Google e2-micro** : gratuit uniquement dans certaines régions américaines (us-west1, us-central1, us-east1), 1 Go de sortie/mois.
- Fly.io n'a plus d'offre gratuite pour les nouveaux comptes.

## Option A — VM persistante + HTTPS automatique (Docker Compose)

1. Créez une VM **Ubuntu 22.04/24.04** (Oracle Always Free ou Google e2-micro) et notez son IP publique.
2. Ouvrez les ports **80 et 443** (règles de sécurité réseau du fournisseur ; sur Oracle, vérifiez aussi `iptables`).
3. Obtenez un nom de domaine gratuit pointant sur l'IP (ex. un sous-domaine DuckDNS). Sans domaine, laissez `DOMAIN=localhost` : seul l'accès par tunnel SSH fonctionnera.
4. Sur la VM :
   ```bash
   curl -fsSL https://get.docker.com | sh && sudo usermod -aG docker $USER   # puis reconnectez-vous
   git clone <votre-depot> examgen && cd examgen          # ou : git clone examgen.bundle examgen
   cp .env.example .env && nano .env                       # EXAMGEN_ADMIN_TOKEN (openssl rand -hex 24) et DOMAIN
   docker compose up -d --build
   ```
5. Vérifiez : `https://VOTRE_DOMAINE/healthz` → `{"status":"ok"}`, puis ouvrez `/admin` avec votre jeton.
6. Chargez votre banque : Administration → *Import / Export*.

Mise à jour : `git pull && docker compose up -d --build` (le volume `data` conserve la base).
Journaux : `docker compose logs -f app`.

**Sauvegardes** : un export JSON quotidien est écrit dans le volume (`/data/backups`, 14 jours). Récupérez-le :
`docker compose cp app:/data/backups ./sauvegardes`. Restauration : *Import / Export → Remplacer*.

## Option B — Render (gratuit, données éphémères)

1. Poussez le dépôt sur GitHub (privé possible).
2. Placez votre banque dans **`bootstrap/banque.json`** (export depuis l'admin) et committez : elle est rechargée automatiquement à chaque démarrage si la base est vide. Pour essayer avec des données fictives : copiez `bootstrap/demo-banque.json` en `banque.json`.
3. Render → *New* → *Blueprint* → sélectionnez le dépôt (`render.yaml` est détecté). Le jeton admin est généré : lisez-le dans *Environment* (`EXAMGEN_ADMIN_TOKEN`).
4. Au premier accès après une veille, patientez ≈ 1 minute.

Conséquences : toute modification faite dans l'admin (nouveaux exercices) est **perdue au redémarrage** tant qu'elle n'est pas réexportée dans `bootstrap/banque.json`. Ce mode convient à une banque stable, éditée hors ligne.

## Variables d'environnement

| Variable | Défaut | Rôle |
|---|---|---|
| `EXAMGEN_ADMIN_TOKEN` | généré (affiché au démarrage) | Jeton de l'administration. **Obligatoire** si `EXAMGEN_ENV=production` (cas du Dockerfile) |
| `EXAMGEN_DB` | `examgen.db` (`/data/examgen.db` en Docker) | Fichier SQLite |
| `EXAMGEN_BOOTSTRAP_FILE` | `bootstrap/banque.json` | Banque chargée si la base est vide |
| `EXAMGEN_BACKUP_DIR` | *(désactivé)* | Dossier des sauvegardes JSON quotidiennes |
| `EXAMGEN_TRUST_PROXY` | `0` | `1` derrière Caddy / un PaaS (IP réelle, cookie `Secure`) |
| `EXAMGEN_GEN_PER_MIN` | `30` | Générations max / minute / IP |
| `HOST`, `PORT` | `127.0.0.1`, `8000` | Écoute (`0.0.0.0` en Docker ; `PORT` imposé par certains PaaS) |

## Sécurité en ligne

HTTPS automatique (Caddy), cookie utilisateur `Secure` + HSTS, en-têtes CSP restrictifs, jeton admin comparé en temps constant, blocage temporaire après 10 jetons erronés (5 min, par IP), limitation de débit sur la génération, Markdown sans HTML brut, conteneur non-root.
**Non couvert** : comptes utilisateurs individuels (identité = cookie anonyme), double authentification admin, figures et courbes, plusieurs serveurs en parallèle (SQLite).

## Dépannage

- *« Illegal instruction » au lancement* (processeur ancien sans AVX2) : remplacez `polars` par `polars-lts-cpu` dans `requirements.txt`.
- *Admin « Trop d'essais »* : attendez 5 min, ou redémarrez l'application.
- *HTTPS non émis* : le domaine doit pointer sur l'IP et les ports 80/443 être ouverts avant `docker compose up`.
