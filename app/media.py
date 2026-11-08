"""Images des énoncés (schémas de Newman/Fischer, figures…) : validation par le CONTENU réel, SVG assaini."""
import base64
import os
import re
import uuid

from .errors import ApiError

MAX_OCTETS = int(float(os.environ.get("EXAMGEN_MAX_MEDIA_MB", "2")) * 1024 * 1024)
ID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
SVG_INTERDIT = re.compile(rb"<script|javascript:|<foreignobject|<iframe|<embed|<object|<!entity|\bon[a-z]+\s*=|(?:xlink:)?href\s*=\s*[\"']\s*(?:https?:|//|data:text)", re.I)


def detecter(data: bytes) -> str:
    """Type MIME d'après les premiers octets ; lève ApiError si format non autorisé ou dangereux."""
    if len(data) == 0:
        raise ApiError(422, "MEDIA_VIDE", "Fichier vide")
    if len(data) > MAX_OCTETS:
        raise ApiError(413, "MEDIA_TROP_GROS", "Image trop volumineuse (max %d Mo)" % (MAX_OCTETS // (1024 * 1024)))
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data[:4] == b"GIF8":
        return "image/gif"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    tete = data.lstrip(b"\xef\xbb\xbf \t\r\n")[:400].lower()
    if (tete.startswith(b"<svg") or (tete.startswith(b"<?xml") and b"<svg" in data[:2000].lower())):
        if SVG_INTERDIT.search(data):
            raise ApiError(422, "SVG_DANGEREUX", "SVG refusé : script, lien externe ou gestionnaire d'événement détecté")
        return "image/svg+xml"
    raise ApiError(415, "MEDIA_FORMAT", "Formats acceptés : PNG, JPEG, GIF, WebP, SVG")


def nouvel_id() -> str:
    return str(uuid.uuid4())


def encoder(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def decoder(b64: str) -> bytes:
    try:
        return base64.b64decode(b64, validate=True)
    except Exception:
        raise ApiError(422, "MEDIA_BASE64", "Données d'image invalides")
