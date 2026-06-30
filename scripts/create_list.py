"""
Crée automatiquement la Liste SharePoint "Suivi Materiel" avec toutes les colonnes.

Usage :
    python scripts/create_list.py

Prérequis : le fichier .env doit être rempli (voir README).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

from app.config import settings          # noqa: E402
from app.graph import GRAPH, GraphError, client  # noqa: E402
from app.schema import FIELDS            # noqa: E402


def column_definition(field: dict) -> dict:
    """Convertit une définition de schéma en colonne SharePoint (format Graph)."""
    col = {"name": field["internal"], "displayName": field["label"]}
    t = field["type"]
    if t == "text":
        col["text"] = {}
    elif t == "note":
        col["text"] = {"allowMultipleLines": True}
    elif t == "number":
        col["number"] = {}
    elif t == "currency":
        col["currency"] = {"locale": "fr-FR"}
    elif t == "dateTime":
        col["dateTime"] = {"format": "dateOnly"}
    elif t == "choice":
        col["choice"] = {"choices": field["choices"], "allowTextEntry": True}
    else:
        col["text"] = {}
    return col


def main() -> None:
    missing = settings.missing()
    if missing:
        print("❌ Configuration .env incomplète. Manquant :", ", ".join(missing))
        sys.exit(1)

    print(f"→ Connexion au site {settings.hostname}{settings.site_path} …")
    site_id = client.site_id()
    print(f"   site OK ({site_id[:30]}…)")

    # Liste déjà existante ?
    url = f"{GRAPH}/sites/{site_id}/lists"
    existing = client._request("GET", url, params={
        "$filter": f"displayName eq '{settings.list_name}'", "$select": "id,displayName"
    }).json().get("value", [])

    if existing:
        list_id = existing[0]["id"]
        print(f"ℹ️  La liste '{settings.list_name}' existe déjà — ajout des colonnes manquantes.")
    else:
        print(f"→ Création de la liste '{settings.list_name}' …")
        body = {
            "displayName": settings.list_name,
            "list": {"template": "genericList"},
        }
        created = client._request("POST", url, json=body).json()
        list_id = created["id"]
        print("   liste créée ✅")

    # Colonnes existantes
    cols_url = f"{GRAPH}/sites/{site_id}/lists/{list_id}/columns"
    have = {c["name"] for c in client._request("GET", cols_url).json().get("value", [])}

    for f in FIELDS:
        if f["internal"] in have:
            print(f"   = colonne {f['internal']} déjà présente")
            continue
        try:
            client._request("POST", cols_url, json=column_definition(f))
            print(f"   + colonne {f['internal']} ({f['label']}) créée")
        except GraphError as e:
            print(f"   ⚠️  {f['internal']} : {e}")

    print("\n✅ Terminé. La base de données SharePoint est prête.")
    print("   Lancez l'application :  uvicorn app.main:app  puis ouvrez http://127.0.0.1:8000")


if __name__ == "__main__":
    try:
        main()
    except GraphError as e:
        print("❌", e)
        sys.exit(1)
