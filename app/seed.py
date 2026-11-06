"""Données de démonstration : python -m app.seed [chemin.db]  (contenu fictif, pour essayer l'interface)."""
import argparse
import json
import random

from . import bank_io, db, repo
from .models import ClasseIn, ExerciceIn, PartieIn


def main(path: str = "examgen.db") -> None:
    conn = db.connect(path)
    db.init(conn)
    if conn.execute("SELECT COUNT(*) FROM matieres").fetchone()[0]:
        print("Base non vide : seed ignoré.")
        return
    R = random.Random(42)
    maths = repo.create_matiere(conn, "Mathématiques")
    parties = [repo.create_partie(conn, PartieIn(matiereId=maths["id"], nom=n, ordre=i + 1))
               for i, n in enumerate(["Algèbre", "Analyse", "Géométrie", "Probabilités"])]
    sec = repo.create_classe(conn, ClasseIn(nom="Seconde"))
    pre = repo.create_classe(conn, ClasseIn(nom="Première", classePrecedenteId=sec["id"], specialiteObligatoire=True))
    ter = repo.create_classe(conn, ClasseIn(nom="Terminale", classePrecedenteId=pre["id"], aExamen=True, specialiteObligatoire=True))
    specs = [repo.create_specialite(conn, n) for n in ("Mathématiques", "SVT")]
    for i in range(120):
        classe = R.choice([sec, pre, ter, ter])
        spec = ["SPECIAL:Aucune"] if classe is sec else [R.choice(specs)["id"]] if R.random() < .6 else ["SPECIAL:Aucune"]
        seq = R.choice([None, 1, 2, 3, 4, 5, 6])
        p = R.choice(parties)
        repo.create_exercice(conn, ExerciceIn(
            sujet=f"**Exercice de démonstration #{i}** ({classe['nom']}, {p['nom']})\n\nCalculer f(x) = x² + {i} puis commenter.",
            corrige=f"Corrigé de démonstration #{i} : voir le cours.",
            affectations=[{"matiereId": maths["id"], "partieId": p["id"]}], classeIds=[classe["id"]],
            specialiteIds=spec, session=seq, niveauIntrinseque=R.choice(["Facile", "Moyen", "Difficile"]),
            tagExamen=bool(seq) and R.random() < .35))
    print("Seed terminé : 1 matière, 4 parties, 3 classes, 2 spécialités, 120 exercices.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Données de démonstration")
    ap.add_argument("db", nargs="?", default="examgen.db")
    ap.add_argument("--json", help="exporte aussi la banque dans ce fichier (ex. bootstrap/banque.json)")
    a = ap.parse_args()
    main(a.db)
    if a.json:
        c = db.connect(a.db)
        with open(a.json, "w", encoding="utf-8") as f:
            json.dump(bank_io.export_bank(c), f, ensure_ascii=False, indent=1)
        print("Export :", a.json)
