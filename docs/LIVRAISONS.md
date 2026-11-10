# Livraisons

Chaîne de branches (une branche = un commit au-dessus de la précédente), du plus ancien au plus récent :

| Branche | Commit | Contenu | Bundle |
|---|---|---|---|
| `main` | `fe34b34` | commit racine | `examgen.bundle` (n°01, avec la suivante) |
| `feat/examgen-v4.11` | `b60a163` | générateur, administration, tests | `examgen.bundle` (n°01) |
| `feat/deploiement` | `938b6c7` | Docker, Caddy, Render, sécurité, sauvegardes | `examgen-deploiement.bundle` (n°02) |
| `fix/banque-demo` | `14ce006` | banque réaliste, tirage avec retentative | `examgen-banque-reelle.bundle` (n°03) |
| `feat/formules` | `3c59ee7` | formules KaTeX, chimie mhchem, aperçu en direct | `examgen-formules.bundle` (n°04) |
| `feat/chimie-structures` | `d96a48d` | structures (développée, topologique, Cram), Lewis, images | `examgen-05-chimie-structures-images.bundle` (n°05) |
| `feat/assistant-ia` | *(ce commit)* | assistant IA, couverture de la banque | `examgen-06-assistant-ia.bundle` (n°06) |

Appliquer un bundle :

```bash
git bundle verify ../examgen-06-assistant-ia.bundle
git fetch ../examgen-06-assistant-ia.bundle feat/assistant-ia:feat/assistant-ia
git checkout feat/assistant-ia
```

Règle de nommage : `examgen-NN-sujet.bundle`, NN croissant : deux livraisons n'ont jamais le même nom (un fichier de même nom en remplacerait un autre).
