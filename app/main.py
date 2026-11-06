import asyncio
import hmac
import os
import secrets
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Body, Depends, FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles

from . import bank_io, db, render, repo, service
from .errors import ApiError
from .ratelimit import Limiter
from .models import ClasseIn, ExerciceIn, GenerateIn, NomIn, PartieIn, ReglagesIn

STATIC = Path(__file__).parent / "static"


def create_app(db_path: Optional[str] = None, admin_token: Optional[str] = None) -> FastAPI:
    db_path = db_path or os.environ.get("EXAMGEN_DB", "examgen.db")
    token_given = admin_token or os.environ.get("EXAMGEN_ADMIN_TOKEN")
    token = token_given or secrets.token_urlsafe(16)

    if os.environ.get("EXAMGEN_ENV") == "production" and not token_given:
        raise RuntimeError("EXAMGEN_ADMIN_TOKEN est obligatoire en production (EXAMGEN_ENV=production).")
    backup_dir = os.environ.get("EXAMGEN_BACKUP_DIR")

    boot = db.connect(db_path)
    db.init(boot)
    bank_io.bootstrap_if_empty(boot, os.environ.get("EXAMGEN_BOOTSTRAP_FILE", "bootstrap/banque.json"))
    boot.close()

    async def purge_loop():
        while True:
            def run():
                c = db.connect(db_path)
                try:
                    service.purge_history(c)
                    if backup_dir:
                        bank_io.backup_to_dir(c, backup_dir)
                finally:
                    c.close()
            await asyncio.to_thread(run)
            await asyncio.sleep(24 * 3600)

    @asynccontextmanager
    async def lifespan(app):
        if not token_given:
            print(f"[examgen] Jeton admin généré (définir EXAMGEN_ADMIN_TOKEN pour le fixer) : {token}")
        task = asyncio.create_task(purge_loop())
        yield
        task.cancel()

    app = FastAPI(title="Générateur d'épreuves", lifespan=lifespan)
    app.state.db_path, app.state.admin_token = db_path, token
    app.state.gen_limiter = Limiter(int(os.environ.get("EXAMGEN_GEN_PER_MIN", "30")), 60)
    app.state.admin_fail = Limiter(10, 300)    # 10 jetons erronés / 5 min / IP

    # ───────── transversal ─────────
    @app.exception_handler(ApiError)
    async def _api_error(_, e: ApiError):
        return JSONResponse({"code": e.code, "message": e.message, **e.extra}, status_code=e.status)

    @app.middleware("http")
    async def _uid_and_headers(request: Request, call_next):
        uid = request.cookies.get("uid")
        new = not uid or len(uid) > 64
        request.state.uid = str(uuid.uuid4()) if new else uid
        resp = await call_next(request)
        https = request.url.scheme == "https"
        if new:
            resp.set_cookie("uid", request.state.uid, max_age=10 * 365 * 86400, httponly=True, samesite="lax", secure=https)
        if https:
            resp.headers["Strict-Transport-Security"] = "max-age=31536000"
        resp.headers["Content-Security-Policy"] = "default-src 'self'; style-src 'self' 'unsafe-inline'; frame-ancestors 'none'"
        resp.headers["X-Content-Type-Options"] = "nosniff"
        resp.headers["Referrer-Policy"] = "no-referrer"
        return resp

    def get_db(request: Request):
        conn = db.connect(request.app.state.db_path)
        try:
            yield conn
        finally:
            conn.close()

    def admin_required(request: Request):
        given = request.headers.get("x-admin-token", "")
        ip = request.client.host if request.client else "?"
        if request.app.state.admin_fail.blocked(ip):
            raise ApiError(429, "RATE_LIMIT", "Trop d'essais, réessayez plus tard")
        if not hmac.compare_digest(given.encode(), request.app.state.admin_token.encode()):
            request.app.state.admin_fail.add(ip)
            raise ApiError(401, "UNAUTHORIZED", "Jeton administrateur requis")

    # ───────── pages ─────────
    @app.get("/", include_in_schema=False)
    def index():
        return FileResponse(STATIC / "index.html")

    @app.get("/admin", include_in_schema=False)
    def admin_page():
        return FileResponse(STATIC / "admin.html")

    app.mount("/static", StaticFiles(directory=STATIC), name="static")

    def _exam(gid, conn, corrige, autoprint):
        g = service.get_generation(conn, gid)
        if g is None:
            return Response("Épreuve introuvable", status_code=404, media_type="text/plain; charset=utf-8")
        return HTMLResponse(render.exam_page(g, corrige=corrige, autoprint=autoprint))

    @app.get("/epreuve/{gid}", include_in_schema=False)
    def epreuve(gid: str, print: int = 0, conn=Depends(get_db)):
        return _exam(gid, conn, False, bool(print))

    @app.get("/epreuve/{gid}/corrige", include_in_schema=False)
    def corrige(gid: str, print: int = 0, conn=Depends(get_db)):
        return _exam(gid, conn, True, bool(print))

    # ───────── module utilisateur ─────────
    @app.get("/api/meta")
    def meta(conn=Depends(get_db)):
        return {
            "matieres": [{"id": m["id"], "nom": m["nom"]} for m in repo.list_matieres(conn)],
            "classes": [{"id": c["id"], "nom": c["nom"], "specialiteObligatoire": c["specialiteObligatoire"]}
                        for c in repo.list_classes(conn)],
            "specialites": [{"id": s["id"], "nom": s["nom"]} for s in repo.list_specialites(conn)],
        }

    @app.get("/healthz", include_in_schema=False)
    def healthz(conn=Depends(get_db)):
        conn.execute("SELECT 1").fetchone()
        return {"status": "ok"}

    @app.post("/api/generate")
    def generate(data: GenerateIn, request: Request, conn=Depends(get_db)):
        if not request.app.state.gen_limiter.allow(request.client.host if request.client else "?"):
            raise ApiError(429, "RATE_LIMIT", "Trop de requêtes")
        g = service.generate_exam(conn, request.state.uid, data)
        gid = g["id"]
        # Silence total (cahier 2.2 / 4.m) : aucune indication sur l'état de l'épreuve (complète ou non).
        return {"id": gid, "exercices": [{"numero": i, "sujetHtml": render.md(e["sujet"])}
                                         for i, e in enumerate(g["contenu"], 1)],
                "urls": {"epreuve": f"/epreuve/{gid}", "imprimer": f"/epreuve/{gid}?print=1",
                         "corrige": f"/epreuve/{gid}/corrige"}}

    # ───────── module administrateur ─────────
    adm = APIRouter(prefix="/api/admin", dependencies=[Depends(admin_required)])

    @adm.get("/ping")
    def ping():
        return {"ok": True}

    @adm.get("/matieres")
    def l_mat(conn=Depends(get_db)): return repo.list_matieres(conn)

    @adm.post("/matieres", status_code=201)
    def c_mat(d: NomIn, conn=Depends(get_db)): return repo.create_matiere(conn, d.nom)

    @adm.put("/matieres/{id}")
    def u_mat(id: str, d: NomIn, conn=Depends(get_db)): return repo.rename_matiere(conn, id, d.nom)

    @adm.delete("/matieres/{id}", status_code=204)
    def d_mat(id: str, reassignTo: Optional[str] = None, reassignPartieId: Optional[str] = None, conn=Depends(get_db)):
        repo.delete_matiere(conn, id, reassignTo, reassignPartieId)

    @adm.get("/parties")
    def l_par(matiereId: Optional[str] = None, conn=Depends(get_db)): return repo.list_parties(conn, matiereId)

    @adm.post("/parties", status_code=201)
    def c_par(d: PartieIn, conn=Depends(get_db)): return repo.create_partie(conn, d)

    @adm.put("/parties/{id}")
    def u_par(id: str, d: PartieIn, conn=Depends(get_db)): return repo.update_partie(conn, id, d)

    @adm.delete("/parties/{id}", status_code=204)
    def d_par(id: str, reassignTo: Optional[str] = None, conn=Depends(get_db)):
        repo.delete_partie(conn, id, reassignTo)

    @adm.get("/classes")
    def l_cla(conn=Depends(get_db)): return repo.list_classes(conn)

    @adm.post("/classes", status_code=201)
    def c_cla(d: ClasseIn, conn=Depends(get_db)): return repo.create_classe(conn, d)

    @adm.put("/classes/{id}")
    def u_cla(id: str, d: ClasseIn, conn=Depends(get_db)): return repo.update_classe(conn, id, d)

    @adm.delete("/classes/{id}", status_code=204)
    def d_cla(id: str, reassignTo: Optional[str] = None, conn=Depends(get_db)):
        repo.delete_classe(conn, id, reassignTo)

    @adm.get("/specialites")
    def l_spe(conn=Depends(get_db)): return repo.list_specialites(conn)

    @adm.post("/specialites", status_code=201)
    def c_spe(d: NomIn, conn=Depends(get_db)): return repo.create_specialite(conn, d.nom)

    @adm.put("/specialites/{id}")
    def u_spe(id: str, d: NomIn, conn=Depends(get_db)): return repo.rename_specialite(conn, id, d.nom)

    @adm.delete("/specialites/{id}", status_code=204)
    def d_spe(id: str, reassignTo: Optional[str] = None, conn=Depends(get_db)):
        repo.delete_specialite(conn, id, reassignTo)

    @adm.get("/exercices")
    def l_exo(q: Optional[str] = None, matiereId: Optional[str] = None, partieId: Optional[str] = None,
              classeId: Optional[str] = None, session: Optional[str] = None,
              limit: int = 100, offset: int = 0, conn=Depends(get_db)):
        return repo.list_exercices(conn, q, matiereId, partieId, classeId, session, limit, offset)

    @adm.get("/exercices/{id}")
    def g_exo(id: str, conn=Depends(get_db)): return repo.get_exercice(conn, id)

    @adm.post("/exercices", status_code=201)
    def c_exo(d: ExerciceIn, conn=Depends(get_db)): return repo.create_exercice(conn, d)

    @adm.put("/exercices/{id}")
    def u_exo(id: str, d: ExerciceIn, conn=Depends(get_db)): return repo.update_exercice(conn, id, d)

    @adm.delete("/exercices/{id}", status_code=204)
    def d_exo(id: str, conn=Depends(get_db)): repo.delete_exercice(conn, id)

    @adm.get("/export")
    def export(conn=Depends(get_db)):
        return JSONResponse(bank_io.export_bank(conn),
                            headers={"Content-Disposition": 'attachment; filename="banque.json"'})

    @adm.post("/import")
    def imp(doc=Body(...), mode: str = "fusionner", conn=Depends(get_db)):
        return bank_io.import_bank(conn, doc, mode)

    @adm.get("/journal")
    def journal(type: Optional[str] = None, limit: int = 100, offset: int = 0, conn=Depends(get_db)):
        return repo.list_journal(conn, type, limit, offset)

    @adm.get("/reglages")
    def g_reg(conn=Depends(get_db)): return repo.get_reglages(conn)

    @adm.put("/reglages")
    def u_reg(d: ReglagesIn, conn=Depends(get_db)): return repo.set_reglages(conn, d.retentionJours)

    @adm.post("/purge")
    def purge(conn=Depends(get_db)): return {"supprimes": service.purge_history(conn)}

    app.include_router(adm)
    return app
