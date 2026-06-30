"""
Schéma de la Liste SharePoint "Suivi Materiel".

Source UNIQUE de vérité pour :
  - les colonnes affichées/éditées dans l'application,
  - la création automatique de la Liste (scripts/create_list.py),
  - l'import de l'inventaire Excel existant (scripts/import_excel.py).

Adapté au format réel de VPMI (inventaire matériel informatique du personnel) :
catégorie, marque, modèle, quantité, état, accessoires, utilisateur, site, remarque.

Chaque champ a un "nom interne" (clé technique côté SharePoint/Graph)
et un libellé affiché dans l'interface.
"""

# Choix prédéfinis (modifiables librement — la saisie libre reste possible)
CATEGORIES = [
    "Ordinateur", "Tablette", "Téléphone", "Écran", "Imprimante", "Clé WiFi",
    "Carte mémoire", "Serveur", "Réseau", "Onduleur", "Accessoire", "Autre",
]
ETATS = [
    "En cours d'utilisation", "Fonctionne", "En réparation",
    "Endommagé", "Perdu", "Hors service",
]
# Statut = attribué à quelqu'un, ou en stock, ou réformé
STATUTS = ["Attribué", "En stock", "Réformé"]
SITES = [
    "Chartres", "Côte d'Ivoire", "Sénégal", "Guadeloupe",
    "Martinique", "Guyane",
]

# Définition des colonnes.
#   internal : nom interne SharePoint (sans espaces ni accents)
#   label    : libellé affiché dans l'interface
#   type     : text | note | number | currency | dateTime | choice
#   choices  : liste de valeurs (uniquement pour type "choice")
#   required : champ obligatoire dans le formulaire
#   excel    : en-têtes possibles dans l'Excel d'origine (pour l'import)
FIELDS = [
    {"internal": "Categorie",   "label": "Catégorie",        "type": "choice",   "choices": CATEGORIES, "required": True,  "excel": ["Catégorie", "Categorie", "Type", "Materiel", "Matériel"]},
    {"internal": "Marque",      "label": "Marque",           "type": "text",     "required": True,  "excel": ["Marque", "Marques", "MARQUES"]},
    {"internal": "Modele",      "label": "Modèle",           "type": "text",     "required": False, "excel": ["Modèle", "Modele", "Models", "Model", "MODELS"]},
    {"internal": "NumeroSerie", "label": "N° de série",      "type": "text",     "required": False, "excel": ["N° de série", "Numéro de série", "Serial", "SN"]},
    {"internal": "Quantite",    "label": "Quantité",         "type": "number",   "required": False, "excel": ["Quantité", "Quantite", "Qté", "Qte", "QUANTITE"]},
    {"internal": "Etat",        "label": "État",             "type": "choice",   "choices": ETATS,    "required": False, "excel": ["État", "Etat", "Condition"]},
    {"internal": "Statut",      "label": "Statut",           "type": "choice",   "choices": STATUTS,  "required": False, "excel": ["Statut", "Status"]},
    {"internal": "Accessoires", "label": "Accessoires",      "type": "text",     "required": False, "excel": ["Accessoires", "Accessoire", "ACCESSOIRE", "ACCESSOIRES"]},
    {"internal": "Utilisateur", "label": "Utilisateur",      "type": "text",     "required": False, "excel": ["Utilisateur", "UTILISATEUR", "Affecté à", "Employé", "Personnel"]},
    {"internal": "Site",        "label": "Site / Pays",      "type": "choice",   "choices": SITES,    "required": False, "excel": ["Site", "Pays", "Localisation", "Lieu", "Agence"]},
    {"internal": "DateAchat",   "label": "Date d'achat",     "type": "dateTime", "required": False, "excel": ["Date d'achat", "Date achat", "Date d'acquisition"]},
    {"internal": "PrixAchat",   "label": "Prix d'achat",     "type": "currency", "required": False, "excel": ["Prix d'achat", "Prix achat", "Prix", "Coût", "Montant"]},
    {"internal": "Fournisseur", "label": "Fournisseur",      "type": "text",     "required": False, "excel": ["Fournisseur", "Vendeur"]},
    {"internal": "Remarque",    "label": "Remarque",         "type": "note",     "required": False, "excel": ["Remarque", "Remarques", "Commentaire", "Commentaires", "Note", "Notes"]},
]

# Accès rapide
FIELD_BY_INTERNAL = {f["internal"]: f for f in FIELDS}
INTERNAL_NAMES = [f["internal"] for f in FIELDS]
