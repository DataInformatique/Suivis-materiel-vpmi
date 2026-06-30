# 🚀 Déployer sur Render (accessible partout, gratuit)

L'application est déjà préparée : `render.yaml`, `Procfile`, `requirements.txt`,
et un dépôt Git local avec un premier commit (le `.env` secret est **exclu**).

---

## Étape 1 — Mettre le code sur GitHub

1. Créez un compte sur **https://github.com** (gratuit) si besoin.
2. **New repository** → nom : `suivi-materiel-vpmi` → cochez **Private** →
   *ne cochez rien d'autre* (pas de README) → **Create repository**.
3. Dans le dossier `Suivis materiel`, ouvrez un terminal et lancez
   (remplacez `VOTRE-COMPTE`) :

   ```bash
   git branch -M main
   git remote add origin https://github.com/VOTRE-COMPTE/suivi-materiel-vpmi.git
   git push -u origin main
   ```

   GitHub demandera votre identifiant (connexion via le navigateur).

---

## Étape 2 — Créer le service sur Render

1. Allez sur **https://render.com** → **Get Started** → connectez-vous **avec GitHub**.
2. **New +** → **Blueprint**.
3. Sélectionnez le dépôt `suivi-materiel-vpmi`. Render lit `render.yaml`
   et propose le service **suivi-materiel-vpmi** → **Apply**.

---

## Étape 3 — Renseigner les variables (secrets)

Render vous demande les variables marquées « sync: false ». Collez :

| Variable | Valeur |
|---|---|
| `AZURE_TENANT_ID` | `38d67a57-acde-49b6-9641-fd204a93bc6f` |
| `AZURE_CLIENT_ID` | `6fe8b485-dcac-4c63-b963-c08579d8e0c1` |
| `AZURE_CLIENT_SECRET` | **⚠️ un NOUVEAU secret** (voir encadré) |
| `SHAREPOINT_HOSTNAME` | `vpmi28.sharepoint.com` |
| `SHAREPOINT_SITE_PATH` | `/sites/Serviceinformatique` |
| `APP_PASSWORD` | un mot de passe de votre choix |

> 🔒 **Régénérez le secret Azure** avant de déployer : il a circulé en clair.
> Azure → Inscriptions d'applications → Suivi Materiel VPMI → *Certificats & secrets*
> → **Nouveau secret client** → copiez la **Valeur** → mettez-la dans `AZURE_CLIENT_SECRET`
> (sur Render **et** dans votre `.env` local). Supprimez l'ancien secret.

---

## Étape 4 — Déployer

Cliquez **Create / Apply**. Render installe et démarre l'app (2–4 min).
Vous obtenez une adresse du type **https://suivi-materiel-vpmi.onrender.com**.
Ouvrez-la, saisissez votre `APP_PASSWORD` → vos 39 matériels s'affichent. 🎉

À chaque fois que vous ferez `git push`, Render redéploie automatiquement.

---

## À savoir

- **Offre gratuite** : l'app « s'endort » après ~15 min sans visite ; la 1ʳᵉ ouverture
  suivante prend ~40 s (réveil). Pour qu'elle reste toujours active : offre payante
  Render (~7 $/mois).
- **Aucune modification Azure** nécessaire pour l'URL (l'app utilise l'authentification
  « app-only », sans redirection).
- Les données restent dans **SharePoint** : Render ne stocke rien.
