"""
Suivi Matériel VPMI — API + interface web.

Lancer en local :
    uvicorn app.main:app --reload
Puis ouvrir http://127.0.0.1:8000
"""
from __future__ import annotations

import secrets
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .config import settings
from .graph import GraphError, client
from .schema import FIELD_BY_INTERNAL, FIELDS, INTERNAL_NAMES

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(title="Suivi Matériel VPMI", docs_url=None, redoc_url=None)


# ---------------- Anti-cache (toujours servir la dernière version) ----------------
@app.middleware("http")
async def no_cache(request: Request, call_next):
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    return response


# ---------------- Sécurité (mot de passe optionnel) ----------------
def check_auth(request: Request) -> None:
    """Protection simple par mot de passe (en-tête X-App-Password)."""
    if not settings.app_password:
        return
    provided = request.headers.get("X-App-Password", "")
    if not secrets.compare_digest(provided, settings.app_password):
        raise HTTPException(status_code=401, detail="Mot de passe incorrect")


# ---------------- Gestion des erreurs Graph ----------------
@app.exception_handler(GraphError)
async def graph_error_handler(request: Request, exc: GraphError) -> JSONResponse:
    return JSONResponse(status_code=502, content={"detail": str(exc)})


# ---------------- API ----------------
@app.get("/api/config")
def get_config() -> dict[str, Any]:
    """Métadonnées pour l'interface : champs, statut de config, protection."""
    return {
        "fields": FIELDS,
        "configured": settings.configured,
        "missing": settings.missing(),
        "list_name": settings.list_name,
        "password_required": bool(settings.app_password),
    }


@app.post("/api/login")
def login(payload: dict[str, str]) -> dict[str, bool]:
    """Vérifie le mot de passe (si activé)."""
    if not settings.app_password:
        return {"ok": True}
    if secrets.compare_digest(payload.get("password", ""), settings.app_password):
        return {"ok": True}
    raise HTTPException(status_code=401, detail="Mot de passe incorrect")


def _clean_fields(payload: dict[str, Any]) -> dict[str, Any]:
    """Ne garde que les colonnes connues et ignore les valeurs vides."""
    out: dict[str, Any] = {}
    for name in INTERNAL_NAMES:
        if name in payload:
            val = payload[name]
            if val == "" or val is None:
                continue
            out[name] = val
    return out


@app.get("/api/materiels", dependencies=[Depends(check_auth)])
def list_materiels() -> list[dict[str, Any]]:
    return client.list_items()


def _check_required(fields: dict[str, Any]) -> None:
    """Vérifie les champs obligatoires définis dans le schéma."""
    missing = [f["internal"] for f in FIELDS if f.get("required") and not fields.get(f["internal"])]
    if missing:
        labels = ", ".join(FIELD_BY_INTERNAL[m]["label"] for m in missing)
        raise HTTPException(status_code=400, detail=f"Champ(s) obligatoire(s) : {labels}.")


@app.post("/api/materiels", dependencies=[Depends(check_auth)])
def create_materiel(payload: dict[str, Any]) -> dict[str, Any]:
    fields = _clean_fields(payload)
    _check_required(fields)
    return client.create_item(fields)


@app.post("/api/materiels/bulk", dependencies=[Depends(check_auth)])
def create_materiels_bulk(payload: list[dict[str, Any]]) -> dict[str, Any]:
    """Crée plusieurs matériels en une fois. Renvoie le nombre créé et les erreurs."""
    created: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    for i, raw in enumerate(payload):
        fields = _clean_fields(raw)
        try:
            _check_required(fields)
            created.append(client.create_item(fields))
        except HTTPException as exc:
            errors.append({"ligne": i + 1, "detail": exc.detail})
        except GraphError as exc:
            errors.append({"ligne": i + 1, "detail": str(exc)})
    return {"created": len(created), "errors": errors}


@app.put("/api/materiels/{item_id}", dependencies=[Depends(check_auth)])
def update_materiel(item_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    fields = _clean_fields(payload)
    return client.update_item(item_id, fields)


@app.delete("/api/materiels/{item_id}", dependencies=[Depends(check_auth)])
def delete_materiel(item_id: str) -> dict[str, bool]:
    client.delete_item(item_id)
    return {"ok": True}


@app.get("/api/health")
def health() -> dict[str, Any]:
    """Vérifie la connexion à SharePoint."""
    try:
        client.reset_cache()
        site = client.site_id()
        lst = client.list_id()
        return {"ok": True, "site_id": site[:20] + "…", "list_ok": bool(lst)}
    except GraphError as exc:
        return {"ok": False, "error": str(exc)}


# ---------------- Frontend ----------------
@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
