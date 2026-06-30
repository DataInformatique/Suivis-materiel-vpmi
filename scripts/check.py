"""Vérifie la configuration et la connexion à SharePoint. Usage : python scripts/check.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

from app.config import settings          # noqa: E402
from app.graph import GraphError, client  # noqa: E402

missing = settings.missing()
if missing:
    print("❌ .env incomplet — manquant :", ", ".join(missing))
    sys.exit(1)
print("✅ .env complet")

try:
    print("→ Authentification Azure AD…")
    client._get_token()
    print("✅ Token obtenu")
    print(f"→ Résolution du site {settings.hostname}{settings.site_path}…")
    print("✅ Site :", client.site_id())
    print(f"→ Recherche de la liste '{settings.list_name}'…")
    print("✅ Liste :", client.list_id())
    n = len(client.list_items())
    print(f"✅ Connexion OK — {n} matériel(s) dans la liste.")
except GraphError as e:
    print("❌", e)
    sys.exit(1)
