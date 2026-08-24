# StreamLocal 🎬

**Une plateforme pour créateurs locaux qui permet de publier et
monétiser des vidéos courtes, mettant en lumière les talents du
pays.**

Projet réalisé par **Ravi Junior Tchoudjouen** dans le cadre d'un
projet de soutenance — catégorie *Média / Créatif* (sujet n°56).

StreamLocal reprend le concept d'une plateforme de vidéos courtes
façon TikTok : fil d'actualité vertical plein écran, likes,
commentaires, abonnements, partages — avec en plus un vrai système
de **monétisation des créateurs** basé sur les vues qualifiées, un
**portefeuille numérique**, des **retraits Mobile Money simulés**,
et un **panel d'administration** complet pour piloter la plateforme.

---

## 📋 Sommaire

- [Fonctionnalités](#-fonctionnalités)
- [Stack technique](#-stack-technique)
- [Structure du projet](#-structure-du-projet)
- [Prérequis](#-prérequis)
- [Installation](#-installation)
- [Configuration (.env)](#-configuration-env)
- [Lancer le projet](#-lancer-le-projet)
- [Créer un compte administrateur](#-créer-un-compte-administrateur)
- [Base de données](#-base-de-données)
- [Routes de l'application](#-routes-de-lapplication)
- [Le système de monétisation](#-le-système-de-monétisation)
- [Panel administrateur](#-panel-administrateur)
- [Sécurité](#-sécurité)
- [Limites connues](#-limites-connues--pistes-daméliorations)
- [Auteur](#-auteur)

---

## ✨ Fonctionnalités

### Côté utilisateur

- **Authentification** : inscription, connexion, déconnexion,
  mots de passe hashés (Werkzeug)
- **Fil d'actualité** (`/feed`) façon TikTok : défilement vertical
  plein écran avec `scroll-snap`, autoplay/pause automatique selon
  la vidéo visible à l'écran, son coupé par défaut avec bouton
  dédié, barre de progression de lecture
- **Publication de vidéos** avec titre, description et catégorie
- **Likes** — avec liste consultable de *qui* a aimé une vidéo, et
  animation de like au double-tap sur la vidéo (comme TikTok)
- **Commentaires** — visibles par tous, avec pseudo et avatar de
  l'auteur du commentaire
- **Abonnements** (follow / unfollow) entre créateurs
- **Partages** de vidéos
- **Recherche** (`/search`) de créateurs et de vidéos par mot-clé
- **Notifications** en temps réel (like, commentaire, abonnement,
  monétisation) avec compteur de non-lues, précisant systématiquement
  *quelle vidéo* est concernée
- **Profil personnel** (`/profile`) : statistiques (vidéos, abonnés,
  abonnements, total de likes reçus), vidéos aimées, commentaires
  reçus des autres utilisateurs sur ses propres vidéos
- **Profil public** (`/user/<id>`) consultable par tout le monde

### Côté créateur / monétisation

- **Système de vues qualifiées** : une vue ne rapporte de l'argent
  au créateur que si l'utilisateur a regardé la vidéo au moins
  **60 secondes**, avec verrouillage SQL (`FOR UPDATE`) pour éviter
  tout double paiement
- **Portefeuille numérique** (solde disponible, en attente, total
  gagné, total retiré)
- **Dashboard de monétisation** (`/monetization`) : statut du compte
  (non éligible / éligible / actif / suspendu), conditions
  d'éligibilité avec barres de progression (abonnés, vues, vidéos,
  ancienneté du compte)
- **Retraits Mobile Money simulés** (`/withdraw`) : MTN Mobile Money
  ou Orange Money, avec historique des retraits
  (`/withdrawals`)

### Administration

- **Connexion administrateur séparée** (`/admin/login`), totalement
  distincte de la connexion classique des utilisateurs
- **Tableau de bord** : statistiques globales de la plateforme
- **Gestion des paramètres de monétisation** : l'admin peut modifier
  en direct les conditions d'éligibilité (abonnés, vues, vidéos,
  ancienneté minimum), le montant minimum de retrait, et **le
  montant généré par 1000 vues qualifiées**
- **Gestion des comptes** : liste de tous les utilisateurs avec
  recherche, et pour chacun :
  - activation/suspension manuelle de la monétisation (indépendamment
    des conditions automatiques)
  - activation/désactivation du compte (bannissement)

---

## 🛠 Stack technique

| Composant       | Technologie                              |
|-----------------|-------------------------------------------|
| Backend         | Python 3 / Flask 3.1                      |
| Base de données | MySQL (via `mysql-connector-python`, **pas** de SQLAlchemy) |
| Authentification| Sessions Flask + hash Werkzeug            |
| Frontend        | HTML / Jinja2 / CSS / JavaScript natif (pas de framework JS) |
| Variables d'env.| `python-dotenv`                           |

Aucun ORM n'est utilisé : toutes les requêtes SQL sont écrites à la
main, avec des requêtes **paramétrées** (`%s`) pour se protéger des
injections SQL.

---

## 📁 Structure du projet

```
Stream_local/
├── app.py                     # Toute la logique Flask (routes, vues)
├── db.py                      # Connexion MySQL (mysql-connector-python)
├── requirements.txt
├── .env                       # Variables d'environnement (à créer)
├── .gitignore
│
├── static/
│   ├── css/
│   │   └── style.css          # Toutes les feuilles de style
│   ├── js/
│   │   └── app.js
│   ├── images/
│   └── videos/
│
├── uploads/
│   └── videos/                # Vidéos envoyées par les créateurs
│
└── templates/
    ├── base.html               # Layout commun (navbar) + navbar admin séparée
    ├── index.html               # Page d'accueil
    ├── login.html / register.html
    ├── feed.html                 # Fil d'actualité façon TikTok
    ├── upload.html                # Publication de vidéo
    ├── profile.html                # Profil personnel
    ├── public_profile.html          # Profil public d'un autre créateur
    ├── search.html                   # Recherche
    ├── notifications.html             # Notifications
    ├── monetization.html               # Dashboard monétisation
    ├── withdraw.html / withdrawals.html # Retraits
    ├── admin_login.html                  # Connexion admin séparée
    ├── admin_dashboard.html               # Tableau de bord admin
    ├── admin_settings.html                 # Paramètres de monétisation
    ├── admin_accounts.html                  # Liste des comptes
    └── admin_account_detail.html             # Détail + contrôle d'un compte
```

---

## ✅ Prérequis

- Python 3.10 ou supérieur
- MySQL (via XAMPP, WAMP, MAMP, ou une installation autonome)
- PyCharm (ou tout autre IDE) — recommandé pour ce projet

---

## ⚙️ Installation

**1. Récupérer le projet et créer un environnement virtuel**

```bash
cd Stream_local
python -m venv .venv
```

Active-le :

```bash
# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

**2. Installer les dépendances**

```bash
pip install -r requirements.txt
```

**3. Créer la base de données**

Dans phpMyAdmin (ou en ligne de commande MySQL), crée une base
`streamlocal_db`, puis importe le fichier `streamlocal_db.sql`
fourni (onglet **Importer** dans phpMyAdmin).

---

## 🔐 Configuration (.env)

Crée un fichier `.env` à la racine du projet (à côté de `app.py`) :

```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=
DB_NAME=streamlocal_db
SECRET_KEY=change-moi-avec-une-vraie-cle-secrete
```

⚠️ Ne jamais partager ce fichier ni le pousser sur GitHub — il
contient les identifiants de ta base de données. Vérifie qu'il est
bien listé dans `.gitignore`.

---

## ▶️ Lancer le projet

Depuis PyCharm : lance simplement `app.py`.

En ligne de commande :

```bash
python app.py
```

L'application est accessible sur :
**http://127.0.0.1:5000**

---

## 👑 Créer un compte administrateur

Aucun compte admin n'existe par défaut. Pour en créer un :

**1. Génère un hash de mot de passe** (dans une console Python,
via PyCharm par exemple) :

```python
from werkzeug.security import generate_password_hash
print(generate_password_hash("TonMotDePasseAdmin"))
```

**2. Insère le compte dans phpMyAdmin** (onglet SQL) :

```sql
INSERT INTO users
    (username, email, password_hash, is_active, is_admin)
VALUES
    ('admin', 'admin@streamlocal.com', 'COLLE_LE_HASH_ICI', 1, 1);
```

**3. Connecte-toi** sur `http://127.0.0.1:5000/admin/login` avec cet
email et ce mot de passe.

Cette page est volontairement séparée de la connexion classique
(`/login`) : un compte admin ne peut pas se connecter en tant
qu'utilisateur normal, et inversement.

---

## 🗄️ Base de données

Tables principales utilisées activement par l'application :

| Table                    | Rôle |
|---------------------------|------|
| `users`                    | Comptes utilisateurs (créateurs + admins) |
| `videos`                    | Vidéos publiées |
| `likes`                      | Likes sur les vidéos |
| `comments`                    | Commentaires |
| `followers`                     | Relations d'abonnement |
| `shares`                          | Partages de vidéos |
| `views` / `video_views`            | Vues et suivi du temps de visionnage |
| `notifications`                     | Notifications utilisateur |
| `categories`                         | Catégories de vidéos |
| `creator_wallets`                     | Portefeuille réel de chaque créateur |
| `creator_earnings`                     | Historique des gains |
| `monetization_accounts`                 | Statut de monétisation par créateur |
| `monetization_settings`                  | Taux de rémunération (XAF / 1000 vues) |
| `admin_settings`                          | Seuils d'éligibilité, retrait minimum |
| `withdrawal_requests`                      | Demandes de retrait |

> Le fichier `streamlocal_db.sql` contient quelques tables
> historiques non utilisées par la version actuelle du code
> (`wallets`, `monetization`, `withdrawals`, `creator_monetization`)
> — conservées pour ne pas casser d'éventuelles données existantes,
> mais qui peuvent être supprimées sans impact si tu repars d'une
> base propre.

---

## 🌐 Routes de l'application

<details>
<summary>Voir la liste complète des routes</summary>

| Route | Méthodes | Description |
|-------|----------|--------------|
| `/` | GET | Accueil |
| `/register` | GET, POST | Inscription |
| `/login` | GET, POST | Connexion utilisateur |
| `/logout` | GET | Déconnexion |
| `/profile` | GET | Profil personnel |
| `/user/<id>` | GET | Profil public d'un créateur |
| `/feed` | GET | Fil d'actualité |
| `/search` | GET | Recherche |
| `/upload` | GET, POST | Publier une vidéo |
| `/uploads/videos/<filename>` | GET | Servir les fichiers vidéo |
| `/api/videos/<id>/like` | POST | Aimer / retirer un like |
| `/api/videos/<id>/likes` | GET | Liste des personnes ayant aimé |
| `/api/users/<id>/follow` | POST | Suivre / ne plus suivre |
| `/api/videos/<id>/view` | POST | Enregistrer une vue |
| `/api/views/<id>/watch` | POST | Mettre à jour la durée de visionnage |
| `/api/views/<id>/qualify` | POST | Qualifier une vue (≥ 60s) |
| `/api/videos/<id>/share` | POST | Partager une vidéo |
| `/api/videos/<id>/comments` | GET, POST | Lire / ajouter un commentaire |
| `/api/comments/<id>` | DELETE | Supprimer un commentaire |
| `/monetization` | GET | Dashboard de monétisation |
| `/withdraw` | GET, POST | Demander un retrait |
| `/withdrawals` | GET | Historique des retraits |
| `/api/monetization/check` | GET | Vérifier l'éligibilité |
| `/notifications` | GET | Notifications |
| `/api/notifications/<id>/read` | POST | Marquer comme lu |
| `/api/notifications/read-all` | POST | Tout marquer comme lu |
| `/admin/login` | GET, POST | Connexion administrateur |
| `/admin` | GET | Tableau de bord admin |
| `/admin/settings` | GET, POST | Paramètres de monétisation |
| `/admin/accounts` | GET | Liste des comptes |
| `/admin/accounts/<id>` | GET | Détail d'un compte |
| `/admin/accounts/<id>/monetization` | POST | Modifier le statut de monétisation |
| `/admin/accounts/<id>/toggle-active` | POST | Activer / désactiver un compte |

</details>

---

## 💰 Le système de monétisation

1. Un utilisateur regarde une vidéo dans le feed.
2. Le temps de visionnage est suivi côté client (JavaScript) et
   envoyé régulièrement au serveur.
3. Dès que le temps de visionnage atteint **60 secondes**, la vue
   est **qualifiée** : le serveur vérifie (avec un verrou SQL
   `FOR UPDATE`) qu'elle n'a pas déjà été payée, puis crédite le
   créateur selon le taux configuré par l'administrateur
   (par défaut **500 XAF pour 1000 vues qualifiées**, soit 0,50 XAF
   par vue).
4. Le montant est ajouté au portefeuille du créateur
   (`creator_wallets`) et un enregistrement est créé dans
   `creator_earnings`.
5. Un créateur devient **éligible** à la monétisation lorsqu'il
   atteint les seuils définis par l'administrateur (abonnés, vues,
   vidéos publiées, ancienneté du compte).
6. L'administrateur peut **activer manuellement** la monétisation
   d'un compte (même s'il ne remplit pas encore toutes les
   conditions), ou la **suspendre** à tout moment avec un motif.

---

## 🛠️ Panel administrateur

Accessible uniquement via `/admin/login` (jamais via la connexion
classique), avec un compte dédié (`is_admin = 1` dans la table
`users`).

- **Tableau de bord** — nombre d'utilisateurs, de vidéos, de comptes
  monétisés / éligibles / suspendus, total versé aux créateurs
- **Paramètres** — modification en direct des seuils d'éligibilité
  et du taux de rémunération par vue
- **Comptes** — recherche et vue d'ensemble de tous les utilisateurs
- **Détail d'un compte** — statistiques complètes, statut de
  monétisation modifiable manuellement, activation/désactivation du
  compte

---

## 🔒 Sécurité

Ce qui est déjà en place :

- Mots de passe hashés avec Werkzeug (`generate_password_hash` /
  `check_password_hash`)
- Requêtes SQL **paramétrées** partout (protection contre les
  injections SQL)
- Fichiers uploadés passés par `secure_filename()` + nom généré en
  UUID (protection contre le path traversal)
- Extensions vidéo autorisées limitées (`mp4`, `mov`, `avi`, `mkv`,
  `webm`)
- Taille maximale d'upload limitée à 200 Mo
  (`MAX_CONTENT_LENGTH`)
- Routes protégées par décorateurs `@login_required` /
  `@admin_required`
- Connexion administrateur strictement séparée de la connexion
  utilisateur

À connaître avant une mise en production réelle (au-delà du cadre
de ce projet de soutenance) :

- **Pas de protection CSRF** sur les formulaires
- **Pas de "mot de passe oublié"**
- Les routes `/test-db` et `/test-tables` exposent la structure de
  la base de données publiquement — à supprimer ou protéger avant
  toute mise en ligne
- La `SECRET_KEY` par défaut dans le code est faible — toujours en
  définir une forte via `.env`

---

## ⚠️ Limites connues / pistes d'améliorations

- Le champ `duration` des vidéos n'est pas encore calculé
  automatiquement à l'upload
- Pas encore de formulaire pour modifier son profil (bio, photo)
  après inscription
- Certaines tables SQL historiques ne sont plus utilisées et
  pourraient être nettoyées dans une future version

---

## 👤 Auteur

**Ravi Junior Tchoudjouen**
Projet StreamLocal — Catégorie Média / Créatif (sujet n°56)
