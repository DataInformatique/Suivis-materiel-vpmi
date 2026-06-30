"""
Client Microsoft Graph — authentification "app-only" + CRUD sur une Liste SharePoint.

La Liste SharePoint sert de base de données : chaque "item" de la liste
est un matériel. On lit/écrit via l'API Microsoft Graph.
"""
from __future__ import annotations

import threading
import time
from typing import Any

import msal
import requests

from .config import settings

GRAPH = "https://graph.microsoft.com/v1.0"
SCOPE = ["https://graph.microsoft.com/.default"]


class GraphError(Exception):
    """Erreur renvoyée par l'API Graph, avec un message lisible."""


class GraphClient:
    """Petit client Graph avec cache du token, de l'ID de site et de l'ID de liste."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._token: str | None = None
        self._token_exp: float = 0.0
        self._site_id: str | None = None
        self._list_id: str | None = None
        self._app: msal.ConfidentialClientApplication | None = None

    def _ensure_app(self) -> msal.ConfidentialClientApplication:
        """Crée l'application MSAL à la demande (pas à l'import du module)."""
        if self._app is None:
            if not settings.tenant_id or not settings.client_id or not settings.client_secret:
                raise GraphError(
                    "Configuration Azure AD incomplète : "
                    + ", ".join(settings.missing() or ["voir .env"])
                )
            self._app = msal.ConfidentialClientApplication(
                client_id=settings.client_id,
                authority=f"https://login.microsoftonline.com/{settings.tenant_id}",
                client_credential=settings.client_secret,
            )
        return self._app

    # ---------- Authentification ----------
    def _get_token(self) -> str:
        with self._lock:
            if self._token and time.time() < self._token_exp - 60:
                return self._token
            result = self._ensure_app().acquire_token_for_client(scopes=SCOPE)
            if "access_token" not in result:
                desc = result.get("error_description", result.get("error", "inconnue"))
                raise GraphError(f"Échec de l'authentification Azure AD : {desc}")
            self._token = result["access_token"]
            self._token_exp = time.time() + int(result.get("expires_in", 3600))
            return self._token

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._get_token()}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _request(self, method: str, url: str, **kwargs: Any) -> requests.Response:
        # On ne retente que les lectures (GET) : retenter une écriture pourrait créer des doublons.
        retriable = method.upper() == "GET"
        last_exc: Exception | None = None
        for attempt in range(3):
            try:
                resp = requests.request(method, url, headers=self._headers(), timeout=30, **kwargs)
            except (requests.ConnectionError, requests.Timeout) as exc:
                last_exc = exc
                if retriable and attempt < 2:
                    time.sleep(0.6 * (attempt + 1))
                    continue
                raise GraphError(f"Connexion à Graph échouée : {exc}")
            # Erreurs transitoires (limite de débit / indispo) : on retente les lectures
            if resp.status_code in (429, 500, 502, 503, 504) and retriable and attempt < 2:
                time.sleep(0.8 * (attempt + 1))
                continue
            if resp.status_code >= 400:
                try:
                    msg = resp.json().get("error", {}).get("message", resp.text)
                except Exception:
                    msg = resp.text
                raise GraphError(f"Graph {resp.status_code} ({method} {url}) : {msg}")
            return resp
        raise GraphError(f"Graph injoignable après plusieurs tentatives : {last_exc}")

    # ---------- Résolution site / liste ----------
    def site_id(self) -> str:
        if self._site_id:
            return self._site_id
        path = settings.site_path.strip("/")
        if path:
            url = f"{GRAPH}/sites/{settings.hostname}:/{path}"
        else:
            url = f"{GRAPH}/sites/{settings.hostname}"
        data = self._request("GET", url).json()
        self._site_id = data["id"]
        return self._site_id

    def list_id(self) -> str:
        if self._list_id:
            return self._list_id
        url = f"{GRAPH}/sites/{self.site_id()}/lists"
        params = {"$filter": f"displayName eq '{settings.list_name}'", "$select": "id,displayName"}
        items = self._request("GET", url, params=params).json().get("value", [])
        if not items:
            raise GraphError(
                f"Liste SharePoint '{settings.list_name}' introuvable. "
                "Lancez 'python scripts/create_list.py' pour la créer."
            )
        self._list_id = items[0]["id"]
        return self._list_id

    def reset_cache(self) -> None:
        self._site_id = None
        self._list_id = None

    # ---------- CRUD items ----------
    def list_items(self) -> list[dict[str, Any]]:
        """Retourne tous les matériels (id + champs)."""
        url = f"{GRAPH}/sites/{self.site_id()}/lists/{self.list_id()}/items"
        params = {"expand": "fields", "$top": "200"}
        out: list[dict[str, Any]] = []
        while url:
            data = self._request("GET", url, params=params).json()
            for it in data.get("value", []):
                row = dict(it.get("fields", {}))
                row["id"] = it["id"]
                row["_created"] = it.get("createdDateTime")
                row["_modified"] = it.get("lastModifiedDateTime")
                out.append(row)
            url = data.get("@odata.nextLink")
            params = None  # nextLink contient déjà les paramètres
        return out

    def create_item(self, fields: dict[str, Any]) -> dict[str, Any]:
        url = f"{GRAPH}/sites/{self.site_id()}/lists/{self.list_id()}/items"
        data = self._request("POST", url, json={"fields": fields}).json()
        row = dict(data.get("fields", {}))
        row["id"] = data["id"]
        return row

    def update_item(self, item_id: str, fields: dict[str, Any]) -> dict[str, Any]:
        url = f"{GRAPH}/sites/{self.site_id()}/lists/{self.list_id()}/items/{item_id}/fields"
        data = self._request("PATCH", url, json=fields).json()
        row = dict(data)
        row["id"] = item_id
        return row

    def delete_item(self, item_id: str) -> None:
        url = f"{GRAPH}/sites/{self.site_id()}/lists/{self.list_id()}/items/{item_id}"
        self._request("DELETE", url)


# Instance partagée
client = GraphClient()
