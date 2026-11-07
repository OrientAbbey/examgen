"""Jeu de démonstration : python -m app.seed [chemin.db] [--json fichier.json]
Deux matières réalistes (voir app/demo_bank.py) : Mathématiques (114 exercices) et Physique-Chimie (24 exercices),
avec formules LaTeX (indices, exposants, fractions, formules chimiques, unités) et corrigés calculés."""
import argparse
import json

from . import bank_io, db, demo_bank, repo
from .models import ClasseIn, ExerciceIn, PartieIn

PARTIES = {"Mathématiques": ["Algèbre", "Analyse", "Géométrie", "Probabilités et statistiques"],
           "Physique-Chimie": ["Chimie", "Physique"]}


def main(path: str = "examgen.db") -> None:
    conn = db.connect(path)
    db.init(conn)
    if conn.execute("SELECT COUNT(*) FROM matieres").fetchone()[0]:
        print("Base non vide : seed ignoré.")
        return
    matieres, parties = {}, {}
    for nom, plist in PARTIES.items():
        matieres[nom] = repo.create_matiere(conn, nom)
        for i, p in enumerate(plist):
            parties[(nom, p)] = repo.create_partie(conn, PartieIn(matiereId=matieres[nom]["id"], nom=p, ordre=i + 1))
    sec = repo.create_classe(conn, ClasseIn(nom="Seconde"))
    pre = repo.create_classe(conn, ClasseIn(nom="Première", classePrecedenteId=sec["id"], specialiteObligatoire=True))
    ter = repo.create_classe(conn, ClasseIn(nom="Terminale", classePrecedenteId=pre["id"], aExamen=True, specialiteObligatoire=True))
    classes = {"Seconde": sec, "Première": pre, "Terminale": ter}
    specs = {nom: repo.create_specialite(conn, nom) for nom in (demo_bank.MATHS, demo_bank.PC)}
    tous = demo_bank.tous()
    for e in tous:
        repo.create_exercice(conn, ExerciceIn(
            sujet=e["sujet"], corrige=e["corrige"],
            affectations=[{"matiereId": matieres[e["matiere"]]["id"], "partieId": parties[(e["matiere"], e["partie"])]["id"]}],
            classeIds=[classes[e["classe"]]["id"]],
            specialiteIds=[s if s == demo_bank.AUCUNE else specs[s]["id"] for s in e["specialites"]],
            session=e["session"], niveauIntrinseque=e["niveau"], tagExamen=e["tag"]))
    print(f"Seed terminé : 2 matières, 6 parties, 3 classes, 2 spécialités, {len(tous)} exercices.")


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
