"""Jeu de démonstration : python -m app.seed [chemin.db] [--json fichier.json]
Banque de mathématiques RÉALISTE (voir app/demo_bank.py) : 87 exercices avec énoncés et corrigés calculés."""
import argparse
import json

from . import bank_io, db, demo_bank, repo
from .models import ClasseIn, ExerciceIn, PartieIn

PARTIES = ["Algèbre", "Analyse", "Géométrie", "Probabilités et statistiques"]


def main(path: str = "examgen.db") -> None:
    conn = db.connect(path)
    db.init(conn)
    if conn.execute("SELECT COUNT(*) FROM matieres").fetchone()[0]:
        print("Base non vide : seed ignoré.")
        return
    maths = repo.create_matiere(conn, "Mathématiques")
    parties = {nom: repo.create_partie(conn, PartieIn(matiereId=maths["id"], nom=nom, ordre=i + 1))
               for i, nom in enumerate(PARTIES)}
    sec = repo.create_classe(conn, ClasseIn(nom="Seconde"))
    pre = repo.create_classe(conn, ClasseIn(nom="Première", classePrecedenteId=sec["id"], specialiteObligatoire=True))
    ter = repo.create_classe(conn, ClasseIn(nom="Terminale", classePrecedenteId=pre["id"], aExamen=True, specialiteObligatoire=True))
    classes = {"Seconde": sec, "Première": pre, "Terminale": ter}
    specs = {nom: repo.create_specialite(conn, nom) for nom in (demo_bank.MATHS, demo_bank.PC)}
    for e in demo_bank.exercices():
        repo.create_exercice(conn, ExerciceIn(
            sujet=e["sujet"], corrige=e["corrige"],
            affectations=[{"matiereId": maths["id"], "partieId": parties[e["partie"]]["id"]}],
            classeIds=[classes[e["classe"]]["id"]],
            specialiteIds=[s if s == demo_bank.AUCUNE else specs[s]["id"] for s in e["specialites"]],
            session=e["session"], niveauIntrinseque=e["niveau"], tagExamen=e["tag"]))
    print(f"Seed terminé : 1 matière, 4 parties, 3 classes, 2 spécialités, {len(demo_bank.exercices())} exercices.")


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
