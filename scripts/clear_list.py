"""
Vide la Liste SharePoint "Suivi Materiel" (supprime tous les matériels).
⚠️ Action irréversible. Demande confirmation, sauf avec --yes.

Usage :
    python scripts/clear_list.py          # demande confirmation
    python scripts/clear_list.py --yes    # sans confirmation (scripts)
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

from app.graph import GraphError, client  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--yes", action="store_true", help="Ne pas demander de confirmation")
    args = ap.parse_args()

    items = client.list_items()
    print(f"→ {len(items)} matériel(s) dans la liste.")
    if not items:
        print("Rien à supprimer.")
        return

    if not args.yes:
        rep = input(f"Supprimer DÉFINITIVEMENT ces {len(items)} matériel(s) ? (oui/non) : ")
        if rep.strip().lower() not in ("oui", "o", "yes", "y"):
            print("Annulé.")
            return

    deleted = 0
    for it in items:
        try:
            client.delete_item(it["id"])
            deleted += 1
            if deleted % 20 == 0:
                print(f"   … {deleted} supprimés")
        except GraphError as e:
            print("   ⚠️", e)
    print(f"✅ {deleted} matériel(s) supprimé(s).")


if __name__ == "__main__":
    try:
        main()
    except GraphError as e:
        print("❌", e)
        sys.exit(1)
