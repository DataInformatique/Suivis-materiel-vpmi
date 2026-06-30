"""
Importe l'inventaire matériel VPMI (Excel .xlsx ou CSV) dans la Liste SharePoint.

La logique d'analyse est partagée avec l'interface web (voir app/importer.py) :
sections ATTRIBUER / EN STOCK → Statut, catégorie et pays "au fil de l'eau",
en-têtes abîmés, lignes TOTAL ignorées, extraction du N° de série.

Usage :
    python scripts/import_excel.py "chemin/fichier.xlsx"
    python scripts/import_excel.py "fichier.csv" --site "Côte d'Ivoire"
    python scripts/import_excel.py "fichier.xlsx" --sheet "Feuil1" --dry-run

Lancez d'abord scripts/create_list.py.
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

from app.graph import GraphError, client          # noqa: E402
from app.importer import parse_rows, rows_from_bytes  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("file", help="Chemin du fichier (.xlsx ou .csv)")
    ap.add_argument("--sheet", help="Nom de la feuille (défaut : la première)")
    ap.add_argument("--site", help="Site/Pays par défaut (ex: \"Côte d'Ivoire\")")
    ap.add_argument("--dry-run", action="store_true", help="Aperçu sans écrire dans SharePoint")
    args = ap.parse_args()

    path = Path(args.file)
    if not path.exists():
        print("❌ Fichier introuvable :", path)
        sys.exit(1)

    print(f"→ Lecture de '{path.name}'")
    rows = rows_from_bytes(path.read_bytes(), path.name, args.sheet)
    parsed = parse_rows(rows, args.site)

    if not parsed:
        print("❌ Aucune ligne de matériel reconnue. Vérifiez le fichier / la feuille.")
        sys.exit(1)

    print(f"   {len(parsed)} matériel(s) détecté(s).")
    if args.dry_run:
        for f in parsed:
            print("   [dry-run]", {k: v for k, v in f.items() if v})
        print("\nℹ️  Aperçu uniquement (--dry-run). Rien n'a été écrit.")
        return

    created, errors = 0, 0
    for f in parsed:
        try:
            client.create_item(f)
            created += 1
            if created % 20 == 0:
                print(f"   … {created} importés")
        except GraphError as e:
            errors += 1
            print("   ⚠️", e)

    print(f"\n✅ {created} matériel(s) importé(s), {errors} erreur(s).")


if __name__ == "__main__":
    try:
        main()
    except GraphError as e:
        print("❌", e)
        sys.exit(1)
