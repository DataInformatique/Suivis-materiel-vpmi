# 📦 Suivi Matériel VPMI

Application web simple et élégante pour le suivi du matériel de l'entreprise.
La **base de données est une Liste SharePoint** : aucune base à installer, vos données
restent dans votre environnement Microsoft 365.

- **Backend** : Python / FastAPI (un seul processus)
- **Données** : Liste SharePoint via Microsoft Graph (mode « app-only »)
- **Interface** : page web moderne (recherche, filtres, statistiques, ajout/modif/suppression, export CSV)

---

## 🗺️ Vue d'ensemble (3 étapes)

1. **Configurer Azure AD** (enregistrer l'application) → récupérer 3 valeurs
2. **Remplir le fichier `.env`** + **créer la Liste SharePoint** (script automatique)
3. **Lancer l'application** (en local ou dans le cloud)

---

## 1️⃣ Configuration Azure AD (à faire une seule fois)

> Vous avez les droits admin Microsoft 365, c'est donc rapide.

1. Allez sur **https://portal.azure.com** → **Microsoft Entra ID** (ex « Azure AD ») → **Inscriptions d'applications** → **Nouvelle inscription**.
2. Nom : `Suivi Materiel VPMI`. Laissez le reste par défaut → **Enregistrer**.
3. Sur la page de l'app, notez :
   - **ID d'application (client)** → `AZURE_CLIENT_ID`
   - **ID de l'annuaire (tenant)** → `AZURE_TENANT_ID`
4. Menu **Certificats & secrets** → **Nouveau secret client** → copiez immédiatement la **Valeur** → `AZURE_CLIENT_SECRET`
   *(la valeur ne sera plus jamais affichée après).*
5. Menu **API autorisées** → **Ajouter une autorisation** → **Microsoft Graph** → **Autorisations d'application** →
   cochez **`Sites.ReadWrite.All`** → **Ajouter**.
6. Cliquez sur **Accorder le consentement administrateur pour VPMI** ✅ (bouton en haut de la liste).

> 🔒 *Plus restrictif (optionnel) :* utilisez `Sites.Selected` puis accordez l'accès à un seul site
> via PowerShell/Graph. `Sites.ReadWrite.All` est plus simple pour démarrer.

---

## 2️⃣ Installation & création de la Liste

```bash
# Dans le dossier "Suivis materiel"
python -m venv .venv
# Windows :
.venv\Scripts\activate
# Mac/Linux :
source .venv/bin/activate

pip install -r requirements.txt
```

Copiez `.env.example` en **`.env`** et remplissez :

| Variable | Où la trouver |
|---|---|
| `AZURE_TENANT_ID` | Azure → vue d'ensemble de l'app |
| `AZURE_CLIENT_ID` | Azure → vue d'ensemble de l'app |
| `AZURE_CLIENT_SECRET` | Azure → Certificats & secrets (la *Valeur*) |
| `SHAREPOINT_HOSTNAME` | ex. `vpmi.sharepoint.com` |
| `SHAREPOINT_SITE_PATH` | ex. `/sites/Informatique` (vide = site racine) |
| `SHAREPOINT_LIST_NAME` | ex. `Suivi Materiel` |
| `APP_PASSWORD` | *(optionnel)* mot de passe d'accès à l'app |

Vérifiez la connexion, puis créez la Liste automatiquement :

```bash
python scripts/check.py          # teste la config et la connexion
python scripts/create_list.py    # crée la Liste + toutes les colonnes
```

### (Optionnel) Importer votre inventaire Excel existant

L'import gère **le format réel des fichiers VPMI** (.xlsx ou .csv) :

- détecte les sections **« MATERIEL ATTRIBUER »** et **« NON ATTRIBUE (EN STOCK) »**
  → remplit automatiquement la colonne **Statut** (Attribué / En stock) ;
- reporte la **catégorie** (ORDINATEUR, CLE WIFI…) écrite en colonne A « au fil de l'eau » ;
- ignore les lignes **TOTAL** et les lignes vides ;
- tolère les en-têtes abîmés (ex. `MARQUES+B6:M7`) ;
- extrait le **N° de série** quand il est noté dans le modèle (`SN ...`).

```bash
# Aperçu (n'écrit rien) — à faire en premier :
python scripts/import_excel.py "samples\INVENTAIRE MATERIEL ... .csv" --dry-run

# Import réel, en taguant le site/pays du fichier :
python scripts/import_excel.py "C:\chemin\inventaire.xlsx" --site "Côte d'Ivoire"
python scripts/import_excel.py "inventaire_cameroun.xlsx" --site "Cameroun"
```

Chaque fichier d'inventaire correspondant à un pays, utilisez `--site` pour le marquer.
Les correspondances de colonnes sont dans [`app/schema.py`](app/schema.py) (clé `excel`).

---

## 3️⃣ Lancer l'application

### En local (le plus simple)
- **Windows** : double-cliquez sur **`start.bat`**
- **Mac/Linux** : `./start.sh`
- ou manuellement : `uvicorn app.main:app`

Puis ouvrez **http://127.0.0.1:8000** 🎉

### Dans le cloud (accessible partout)

Le projet contient un `Dockerfile` et un `Procfile` — déployable tel quel sur :

- **Render / Railway** : « New Web Service » → connectez le dépôt Git → ajoutez les variables
  d'environnement (mêmes clés que `.env`) → déployez. Aucune commande à écrire.
- **Azure** (cohérent avec M365) : *App Service* (Python) ou *Container Apps* avec le `Dockerfile`.
  Renseignez les variables d'environnement dans la configuration de l'app.

> ⚠️ En cloud, ne committez **jamais** le `.env` (il est dans `.gitignore`).
> Mettez les secrets dans les variables d'environnement du service.
> Activez `APP_PASSWORD` pour protéger l'accès public.

---

## 🧩 Personnaliser les champs

Tout est centralisé dans **[`app/schema.py`](app/schema.py)** : ajoutez/retirez des colonnes,
modifiez les listes de choix (catégories, statuts, sites…). Relancez ensuite
`python scripts/create_list.py` pour ajouter les nouvelles colonnes à SharePoint.
L'interface s'adapte automatiquement (formulaire, filtres, export).

---

## 🛠️ Dépannage

| Problème | Solution |
|---|---|
| `Échec de l'authentification Azure AD` | Vérifiez `AZURE_TENANT_ID` / `CLIENT_ID` / `CLIENT_SECRET`. Le secret expire-t-il ? |
| `Liste ... introuvable` | Lancez `python scripts/create_list.py`, vérifiez `SHAREPOINT_LIST_NAME`. |
| `403 / Access denied` | L'autorisation `Sites.ReadWrite.All` n'a pas reçu le **consentement admin**. |
| Site introuvable | Vérifiez `SHAREPOINT_HOSTNAME` et `SHAREPOINT_SITE_PATH`. |

Diagnostic rapide : `python scripts/check.py`
État de connexion en direct : `http://127.0.0.1:8000/api/health`

---

## 📁 Structure

```
Suivis materiel/
├─ app/
│  ├─ main.py        API FastAPI + service du frontend
│  ├─ graph.py       Client Microsoft Graph (auth + CRUD)
│  ├─ schema.py      ⭐ Définition des colonnes (source unique)
│  ├─ config.py      Lecture du .env
│  └─ static/        Interface web (index.html + app.js)
├─ scripts/
│  ├─ create_list.py Crée la Liste SharePoint
│  ├─ import_excel.py Importe un Excel existant
│  └─ check.py       Teste la configuration
├─ requirements.txt  Dépendances Python
├─ .env.example      Modèle de configuration
├─ Dockerfile        Déploiement cloud
├─ start.bat / start.sh  Démarrage en un clic
└─ README.md
```
