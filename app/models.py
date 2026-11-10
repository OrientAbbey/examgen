from typing import Annotated, Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

AUCUNE = "SPECIAL:Aucune"
Niveau = Literal["Facile", "Moyen", "Difficile"]


def _nom(v: str) -> str:
    v = v.strip()
    if not v:
        raise ValueError("nom vide")
    return v


class NomIn(BaseModel):
    nom: Annotated[str, Field(max_length=200)]
    _v = field_validator("nom")(_nom)


class PartieIn(BaseModel):
    matiereId: str
    nom: Annotated[str, Field(max_length=200)]
    ordre: int = 0
    _v = field_validator("nom")(_nom)


class ClasseIn(BaseModel):
    nom: Annotated[str, Field(max_length=200)]
    classePrecedenteId: Optional[str] = None
    aExamen: bool = False
    specialiteObligatoire: bool = False
    _v = field_validator("nom")(_nom)


class Affectation(BaseModel):
    matiereId: str
    partieId: str


class ExerciceIn(BaseModel):
    sujet: Annotated[str, Field(min_length=1)]
    corrige: Annotated[str, Field(min_length=1)]
    affectations: Annotated[list[Affectation], Field(min_length=1)]
    classeIds: Annotated[list[str], Field(min_length=1)]
    specialiteIds: Annotated[list[str], Field(min_length=1)]
    session: Optional[Annotated[int, Field(ge=1, le=6)]] = None
    niveauIntrinseque: Niveau
    tagExamen: bool = False

    @model_validator(mode="after")
    def _coherence(self):
        if self.tagExamen and self.session is None:
            raise ValueError("tagExamen impossible pour une session vide (3.1 / 4.h)")
        if len({a.matiereId for a in self.affectations}) != len(self.affectations):
            raise ValueError("une seule partie par matière")
        if not self.sujet.strip() or not self.corrige.strip():
            raise ValueError("sujet et corrigé sont indissociables et non vides")
        return self


class GenerateIn(BaseModel):
    matiereId: str
    classeId: str
    specialiteId: Optional[str] = None
    session: Optional[str] = None      # None | "1".."6" | "EXAMEN" | "EXAMEN_BLANC"
    difficulte: Niveau


class ReglagesIn(BaseModel):
    retentionJours: Optional[Annotated[int, Field(ge=1)]] = None


class PreviewIn(BaseModel):
    markdown: Annotated[str, Field(max_length=50000)]


class AiParametresIn(BaseModel):
    texte: Annotated[str, Field(min_length=3, max_length=600)]


class AiEpreuveIn(BaseModel):
    action: Literal["bareme"]


class AiExerciceIn(BaseModel):
    action: Literal["generer", "verifier", "convertir", "reparer", "variantes", "metadonnees"]
    matiereId: Optional[str] = None
    partieId: Optional[str] = None
    classeIds: list[str] = Field(default_factory=list, max_length=10)
    specialiteId: Optional[str] = None
    session: Optional[Annotated[int, Field(ge=1, le=6)]] = None
    niveau: Optional[Niveau] = None
    consigne: Annotated[str, Field(max_length=1500)] = ""
    nbQuestions: Annotated[int, Field(ge=1, le=8)] = 3
    n: Annotated[int, Field(ge=1, le=5)] = 3
    sujet: Annotated[str, Field(max_length=12000)] = ""
    corrige: Annotated[str, Field(max_length=12000)] = ""
    erreurs: list[Annotated[str, Field(max_length=300)]] = Field(default_factory=list, max_length=20)

    @model_validator(mode="after")
    def _requis(self):
        if self.action == "generer":
            if not self.matiereId or not (self.partieId or self.consigne.strip()):
                raise ValueError("generer : matière et (partie ou consigne) requises")
        elif not self.sujet.strip():
            raise ValueError("%s : le sujet est requis" % self.action)
        if self.action in ("verifier", "variantes") and not self.corrige.strip():
            raise ValueError("%s : le corrigé est requis" % self.action)
        if self.action == "reparer" and not self.erreurs:
            raise ValueError("reparer : la liste des erreurs est requise")
        return self
