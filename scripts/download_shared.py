"""
Télécharge un fichier depuis un lien de partage SharePoint/OneDrive via Microsoft Graph.

Usage :
    python scripts/download_shared.py "https://...sharepoint.com/:x:/s/.../XXXX?e=YYY"
    python scripts/download_shared.py "<url>" --out "samples/mon_fichier.xlsx"

Utilise l'API Graph /shares (mode app-only, mêmes identifiants que l'app).
Ensuite, importez le fichier téléchargé avec scripts/import_excel.py.
"""
import argparse
import base64
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

import requests  # noqa: E402
from app.graph import GRAPH, GraphError, client  # noqa: E402


def share_id(url: str) -> str:
    """Encode une URL de partage au format attendu par Graph (/shares/{id})."""
    b64 = base64.urlsafe_b64encode(url.encode("utf-8")).decode("ascii").rstrip("=")
    return "u!" + b64


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("url", help="Lien de partage SharePoint/OneDrive")
    ap.add_argument("--out", help="Chemin de sortie (défaut : samples/<nom du fichier>)")
    args = ap.parse_args()

    sid = share_id(args.url)
    headers = client._headers()  # déclenche l'authentification

    print("→ Résolution du lien de partage…")
    meta = requests.get(f"{GRAPH}/shares/{sid}/driveItem", headers=headers, timeout=30)
    if meta.status_code >= 400:
        raise GraphError(f"Graph {meta.status_code} : {meta.text}")
    info = meta.json()
    name = info.get("name", "fichier_partage.xlsx")
    size = info.get("size", 0)
    print(f"   fichier : {name} ({size} octets)")

    out = Path(args.out) if args.out else (Path(__file__).resolve().parent.parent / "samples" / name)
    out.parent.mkdir(parents=True, exist_ok=True)

    print("→ Téléchargement…")
    content = requests.get(f"{GRAPH}/shares/{sid}/driveItem/content", headers=headers, timeout=120)
    if content.status_code >= 400:
        raise GraphError(f"Graph {content.status_code} : {content.text}")
    out.write_bytes(content.content)
    print(f"✅ Enregistré : {out}")
    print(f"\nImportez-le ensuite avec :")
    print(f'   python scripts/import_excel.py "{out}" --site "Côte d\'Ivoire"')


if __name__ == "__main__":
    try:
        main()
    except GraphError as e:
        print("❌", e)
        sys.exit(1)
