# Banque de démarrage

Si la base est **vide** au démarrage et que `bootstrap/banque.json` existe, la banque y est importée
(mode « remplacer »). Indispensable sur les hébergeurs à disque éphémère (Render, Koyeb) : à chaque redémarrage,
votre banque est restaurée depuis le dépôt Git.

- Pour garder votre vraie banque : Administration → *Import / Export* → *Télécharger banque.json*, déposez-le ici
  sous le nom `banque.json`, puis committez.
- `demo-banque.json` : banque fictive de démonstration. Pour l'essayer : copiez-la en `banque.json`.
