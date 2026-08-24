# ==============================================================
# STREAMLOCAL — app.py
# ==============================================================
#
# SOMMAIRE — utilise Ctrl+F pour sauter directement à un numéro
# de ligne (Ctrl+G dans PyCharm ouvre "aller à la ligne").
#
#   CONFIGURATION & OUTILS
#     - Configuration Flask / upload vidéo .......... ligne  105
#     - allowed_video() : extensions autorisées ...... ligne  138
#     - login_required() : protège une route .......... ligne 154
#     - admin_required() : protège une route admin .... ligne 175
#     - file_too_large() : erreur upload > 200 Mo ..... ligne 211
#
#   COMPTES UTILISATEURS
#     - "/"              accueil ...................... ligne 230
#     - "/register"      inscription ................... ligne 239
#     - "/login"         connexion .................... ligne 416
#     - "/logout"        déconnexion .................. ligne 566
#     - "/profile"       mon profil ................... ligne 582
#     - "/user/<id>"     profil public d'un créateur .. ligne 868
#
#   OUTILS DE DEBUG (à protéger/supprimer avant mise en ligne)
#     - "/test-db"       test connexion MySQL ......... ligne 1141
#     - "/test-tables"   liste des tables ............. ligne 1184
#
#   FIL D'ACTUALITÉ & VIDÉOS
#     - "/feed"                      fil principal ..... ligne 1232
#     - create_notification()       fonction utilitaire  ligne 1357
#     - "/search"                    recherche .......... ligne 1434
#     - "/upload"                    publier une vidéo .. ligne 1593
#     - "/uploads/videos/<f>"        servir une vidéo ... ligne 1818
#
#   INTERACTIONS (like, follow, vues, partages, commentaires)
#     - "/api/videos/<id>/like"        aimer ........... ligne 1832
#     - "/api/users/<id>/follow"       suivre .......... ligne 1978
#     - "/api/videos/<id>/view"        vue ............. ligne 2119
#     - "/api/views/<id>/watch"        durée visionnée . ligne 2308
#     - "/api/videos/<id>/share"       partager ........ ligne 2466
#     - "/api/videos/<id>/likes"       qui a aimé ...... ligne 2579
#     - "/api/videos/<id>/comments"    lire/commenter .. ligne 2643
#     - "/api/comments/<id>"           supprimer ....... ligne 2913
#
#   MONÉTISATION (côté créateur)
#     - "/monetization"     dashboard créateur ......... ligne 3001
#     - "/withdraw"          demander un retrait ........ ligne 3625
#     - "/withdrawals"       historique des retraits .... ligne 4022
#     - get_revenue_rate()   taux de rémunération ....... ligne 4091
#     - credit_creator_for_view()  crédite le créateur .. ligne 4133
#     - qualify_view()       ⭐ qualifie une vue (≥60s),
#                              verrou anti-double-paiement  ligne 4306
#     - "/api/views/<id>/qualify"  qualifie via API ..... ligne 4800
#     - "/api/monetization/check"  ancien système,
#                                   non utilisé par l'UI .. ligne 4834
#
#   NOTIFICATIONS
#     - "/notifications"                  liste ......... ligne 5088
#     - "/api/notifications/<id>/read"    marquer lu .... ligne 5191
#     - inject_notifications_count()      compteur global
#                                          (toutes les pages) ligne 5265
#     - "/api/notifications/read-all"     tout marquer .. ligne 5321
#
#   ADMINISTRATION (connexion séparée de la connexion classique)
#     - "/admin/login"                    connexion admin  ligne 5384
#     - "/admin"                          tableau de bord  ligne 5507
#     - "/admin/settings"                 réglages ....... ligne 5615
#     - "/admin/accounts"                 liste comptes .. ligne 5799
#     - "/admin/accounts/<id>"            détail compte .. ligne 5906
#     - "/admin/accounts/<id>/monetization" ⭐ statut
#                                          manuel ......... ligne 6116
#     - "/admin/accounts/<id>/toggle-active" activer/off . ligne 6320
#
#   LANCEMENT DU SERVEUR ................................. fin du fichier
#
# ==============================================================


# --- Flask : le framework web utilisé pour toutes les routes ---
import os

from flask import (
    Flask,             # la classe principale de l'application
    render_template,   # affiche un fichier .html du dossier templates/
    request,            # contient les données envoyées par le formulaire/l'utilisateur
    redirect,            # renvoie l'utilisateur vers une autre URL
    url_for,               # construit l'URL d'une route à partir de son nom
    session,                # stocke les infos de connexion (user_id, etc.) entre les pages
    flash,                   # affiche un message temporaire (succès/erreur) sur la page suivante
    jsonify                   # transforme un dictionnaire Python en réponse JSON pour le JS
)

from functools import wraps                 # préserve le nom d'une fonction décorée (login_required, etc.)
from werkzeug.utils import secure_filename   # nettoie le nom d'un fichier uploadé (sécurité)
from flask import send_from_directory        # sert un fichier statique (ici, les vidéos uploadées)

from dotenv import load_dotenv                                        # charge les variables du fichier .env
from werkzeug.security import generate_password_hash, check_password_hash  # hash/vérifie les mots de passe

from db import get_db_connection   # notre propre fonction qui ouvre la connexion MySQL (db.py)

# ==========================================================
# CONFIGURATION
# ==========================================================

load_dotenv()  # lit le fichier .env et rend DB_HOST, DB_USER, SECRET_KEY, etc. disponibles via os.getenv()


app = Flask(__name__)  # crée l'application Flask ; __name__ aide Flask à localiser le dossier du projet

# ==========================================================
# CONFIGURATION DES VIDEOS
# ==========================================================

# Construit le chemin absolu vers streamlocal/uploads/videos,
# peu importe depuis quel dossier on lance "python app.py".
UPLOAD_FOLDER = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),  # dossier où se trouve ce fichier app.py
    "uploads",
    "videos"
)

os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # crée le dossier s'il n'existe pas encore (ne plante pas s'il existe déjà)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER  # rend ce chemin accessible partout via app.config[...]

# Taille maximale d'un upload (vidéo comprise) : 200 Mo.
# Sans cette limite, Flask accepte des fichiers de taille
# illimitée, ce qui peut saturer le disque du serveur.
app.config["MAX_CONTENT_LENGTH"] = 200 * 1024 * 1024  # 200 * 1024 * 1024 octets = 200 Mo

# Extensions vidéo acceptées à l'upload — toute autre extension sera refusée par allowed_video()
ALLOWED_VIDEO_EXTENSIONS = {
    "mp4",
    "mov",
    "avi",
    "mkv",
    "webm"
}


def allowed_video(filename):
    """
    Vérifie si le fichier est une vidéo autorisée.
    """

    return (
        "." in filename                                  # le nom de fichier doit contenir un point (sinon pas d'extension)
        and filename.rsplit(".", 1)[1].lower()             # on isole ce qu'il y a après le DERNIER point (l'extension)
        in ALLOWED_VIDEO_EXTENSIONS                         # et on vérifie qu'elle fait partie de la liste autorisée
    )


# ==========================================================
# PROTECTION DES ROUTES
# ==========================================================

def login_required(function):
    # Décorateur : on l'ajoute au-dessus d'une route avec @login_required
    # pour empêcher un visiteur non connecté d'y accéder.

    @wraps(function)  # garde le vrai nom de "function" (utile pour url_for et le débogage)
    def decorated_function(*args, **kwargs):

        if "user_id" not in session:  # "user_id" n'existe dans la session QUE si l'utilisateur est connecté

            flash(
                "Connecte-toi pour accéder à cette page.",
                "error"
            )

            return redirect(url_for("login"))  # on coupe court : direction la page de connexion

        return function(*args, **kwargs)  # utilisateur connecté : on exécute la route demandée normalement

    return decorated_function


def admin_required(function):
    """
    Réservé aux comptes administrateur
    (users.is_admin = 1).
    """

    @wraps(function)
    def decorated_function(*args, **kwargs):

        # Il faut être connecté ET avoir le statut admin en session
        # (voir /admin/login, qui est le SEUL endroit où is_admin=True est posé)
        if "user_id" not in session or not session.get("is_admin"):

            flash(
                "Connecte-toi avec un compte administrateur "
                "pour accéder à cette page.",
                "error"
            )

            return redirect(url_for("admin_login"))  # vers la connexion admin, PAS la connexion classique

        return function(*args, **kwargs)

    return decorated_function

# La clé secrète sert à signer les cookies de session Flask.
# Elle vient du fichier .env (SECRET_KEY=...) ; la valeur par
# défaut ci-dessous n'est qu'un filet de sécurité pour que
# l'app démarre même sans .env — à ne jamais utiliser en prod.
app.config["SECRET_KEY"] = os.getenv(
    "SECRET_KEY",
    "streamlocal-secret-key-change-this"
)


@app.errorhandler(413)  # 413 = code HTTP "Payload Too Large", déclenché automatiquement par MAX_CONTENT_LENGTH
def file_too_large(error):
    """
    Déclenché quand un fichier envoyé dépasse
    MAX_CONTENT_LENGTH (200 Mo).
    """

    flash(
        "Le fichier envoyé est trop volumineux "
        "(200 Mo maximum).",
        "error"
    )

    # request.referrer = la page d'où venait l'utilisateur (ex: /upload) ; sinon on retombe sur le feed
    return redirect(request.referrer or url_for("feed"))

# ==========================================================
# ACCUEIL
# ==========================================================

@app.route("/")  # page d'accueil, accessible à tout le monde (pas de @login_required)
def index():

    return render_template("index.html")  # affiche simplement le fichier templates/index.html

# ==========================================================
# INSCRIPTION
# ==========================================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":  # formulaire soumis (sinon on affiche juste la page, tout en bas)

        # .get(champ, "") évite un crash si le champ est absent ; .strip() enlève les espaces avant/après
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()  # email toujours en minuscules (cohérence)
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        # ----------------------------------------------
        # Vérifications
        # ----------------------------------------------

        if not username or not email or not password:  # champs obligatoires manquants
            flash("Tous les champs obligatoires doivent être remplis.", "error")
            return redirect(url_for("register"))  # on arrête tout et on revient au formulaire

        if len(username) < 3:  # pseudo trop court
            flash("Le nom d'utilisateur doit avoir au moins 3 caractères.", "error")
            return redirect(url_for("register"))

        if len(password) < 8:  # mot de passe trop court
            flash("Le mot de passe doit contenir au moins 8 caractères.", "error")
            return redirect(url_for("register"))

        if password != confirm_password:  # les deux champs "mot de passe" ne correspondent pas
            flash("Les mots de passe ne correspondent pas.", "error")
            return redirect(url_for("register"))

        connection = get_db_connection()  # ouvre une connexion MySQL (voir db.py)

        if connection is None:  # la connexion a échoué (mauvais identifiants, MySQL éteint, etc.)
            flash("Impossible de se connecter à la base de données.", "error")
            return redirect(url_for("register"))

        cursor = connection.cursor(dictionary=True)  # dictionary=True : résultats accessibles par nom de colonne

        try:

            # ------------------------------------------
            # Vérifier si username ou email existe
            # ------------------------------------------

            cursor.execute(
                """
                SELECT id
                FROM users
                WHERE username = %s OR email = %s
                LIMIT 1
                """,
                (username, email)  # %s = paramètres injectés proprement (protection anti-injection SQL)
            )

            existing_user = cursor.fetchone()  # None si personne ne porte déjà ce pseudo/email

            if existing_user:  # quelqu'un existe déjà avec ce pseudo OU cet email

                flash(
                    "Ce nom d'utilisateur ou cette adresse email existe déjà.",
                    "error"
                )

                return redirect(url_for("register"))

            # ------------------------------------------
            # Hash du mot de passe
            # ------------------------------------------

            # On ne stocke JAMAIS le mot de passe en clair : generate_password_hash
            # le transforme en une empreinte irréversible (via Werkzeug).
            password_hash = generate_password_hash(password)

            # ------------------------------------------
            # Création du compte
            # ------------------------------------------

            cursor.execute(
                """
                INSERT INTO users
                (
                    username,
                    email,
                    password_hash,
                    phone
                )
                VALUES (%s, %s, %s, %s)
                """,
                (
                    username,
                    email,
                    password_hash,
                    phone if phone else None  # téléphone optionnel : NULL si laissé vide
                )
            )

            connection.commit()  # valide l'INSERT en base (sans commit, rien n'est réellement enregistré)

            user_id = cursor.lastrowid  # récupère l'id auto-incrémenté que MySQL vient d'attribuer au compte


            # ------------------------------------------
            # Création du profil de monétisation
            # ------------------------------------------
            # Même remarque : table "monetization" historique, remplacée
            # par "monetization_accounts" (créée automatiquement plus tard,
            # à la première visite de /monetization).

            cursor.execute(
                """
                INSERT INTO monetization
                (
                    user_id,
                    status,
                    eligible
                )
                VALUES (%s, 'not_eligible', FALSE)
                """,
                (user_id,)
            )

            connection.commit()  # valide les deux derniers INSERT

            flash(
                "Compte créé avec succès ! Vous pouvez maintenant vous connecter.",
                "success"
            )

            return redirect(url_for("login"))  # inscription terminée : direction la page de connexion

        except Exception as error:  # n'importe quelle erreur pendant le bloc try (SQL, réseau, etc.)

            connection.rollback()  # annule toute modification partielle faite avant l'erreur

            print("Erreur inscription :", error)  # visible dans la console PyCharm, pour débogage

            flash(
                "Une erreur est survenue pendant la création du compte.",
                "error"
            )

            return redirect(url_for("register"))

        finally:  # s'exécute TOUJOURS, que tout se soit bien passé ou non

            cursor.close()      # ferme le curseur SQL
            connection.close()  # referme la connexion à MySQL (libère la ressource)

    # Requête GET (première visite de la page) : on affiche juste le formulaire vide
    return render_template("register.html")

# ==========================================================
# CONNEXION
# ==========================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email or not password:  # un des deux champs est vide

            flash(
                "Veuillez remplir tous les champs.",
                "error"
            )

            return redirect(url_for("login"))

        connection = get_db_connection()

        if connection is None:

            flash(
                "Impossible de se connecter à la base de données.",
                "error"
            )

            return redirect(url_for("login"))

        cursor = connection.cursor(dictionary=True)

        try:

            # On récupère TOUTES les infos nécessaires en une seule requête :
            # le hash pour vérifier le mot de passe, is_active pour un éventuel
            # bannissement, is_admin pour rediriger les admins ailleurs.
            cursor.execute(
                """
                SELECT
                    id,
                    username,
                    email,
                    password_hash,
                    profile_photo,
                    is_active,
                    is_admin
                FROM users
                WHERE email = %s
                LIMIT 1
                """,
                (email,)
            )

            user = cursor.fetchone()  # None si aucun compte n'a cet email

            if not user:  # email inconnu

                # Message volontairement identique à "mauvais mot de passe" plus bas :
                # ne pas révéler si c'est l'email ou le mot de passe qui est faux
                # (bonne pratique de sécurité, évite de confirmer qu'un email existe).
                flash(
                    "Email ou mot de passe incorrect.",
                    "error"
                )

                return redirect(url_for("login"))

            if not user["is_active"]:  # compte désactivé par un admin (voir /admin/accounts/<id>/toggle-active)

                flash(
                    "Ce compte est désactivé.",
                    "error"
                )

                return redirect(url_for("login"))

            # ------------------------------------------
            # Vérification du mot de passe
            # ------------------------------------------

            # check_password_hash compare le mot de passe tapé au hash stocké
            # en base (jamais l'inverse : le hash n'est jamais "déchiffré").
            if not check_password_hash(
                user["password_hash"],
                password
            ):

                flash(
                    "Email ou mot de passe incorrect.",
                    "error"
                )

                return redirect(url_for("login"))

            # ------------------------------------------
            # Les comptes admin ne se connectent pas ici
            # ------------------------------------------

            if user["is_admin"]:  # bon mot de passe, mais c'est un compte admin

                flash(
                    "Ce compte est un compte administrateur. "
                    "Connecte-toi depuis la page d'administration.",
                    "error"
                )

                return redirect(url_for("admin_login"))  # renvoyé vers la connexion admin séparée

            # ------------------------------------------
            # Création de la session
            # ------------------------------------------

            session.clear()  # supprime toute ancienne session (sécurité : évite de mélanger deux comptes)

            # Ces informations restent disponibles sur TOUTES les pages tant que
            # l'utilisateur ne se déconnecte pas (via le cookie de session Flask).
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["email"] = user["email"]
            session["is_admin"] = False  # toujours False ici, car les admins sont interceptés juste au-dessus

            flash(
                f"Bienvenue sur StreamLocal, {user['username']} !",
                "success"
            )

            return redirect(url_for("profile"))  # connexion réussie : direction le profil

        except Exception as error:

            print("Erreur connexion :", error)

            flash(
                "Une erreur est survenue.",
                "error"
            )

            return redirect(url_for("login"))

        finally:

            cursor.close()
            connection.close()

    # Requête GET : simple affichage du formulaire de connexion
    return render_template("login.html")

# ==========================================================
# DÉCONNEXION
# ==========================================================

@app.route("/logout")  # pas de @login_required : accessible même si déjà déconnecté (ne fait rien de grave dans ce cas)
def logout():

    session.clear()  # supprime toutes les infos de connexion (user_id, username, is_admin...)

    flash(
        "Vous êtes maintenant déconnecté.",
        "success"
    )

    return redirect(url_for("index"))  # retour à la page d'accueil

# ==========================================================
# PROFIL
# ==========================================================

@app.route("/profile")
def profile():

    # Vérification manuelle (équivalente à @login_required) : on préfère ici
    # gérer soi-même le cas "pas connecté" plutôt que d'utiliser le décorateur.
    if "user_id" not in session:

        flash(
            "Vous devez être connecté pour accéder à votre profil.",
            "error"
        )

        return redirect(url_for("login"))

    connection = get_db_connection()

    if connection is None:

        flash(
            "Impossible de se connecter à MySQL.",
            "error"
        )

        return redirect(url_for("index"))

    cursor = connection.cursor(dictionary=True)

    try:

        # ----------------------------------------------
        # Informations utilisateur
        # ----------------------------------------------

        cursor.execute(
            """
            SELECT
                id,
                username,
                email,
                phone,
                bio,
                profile_photo,
                created_at
            FROM users
            WHERE id = %s
            """,
            (session["user_id"],)  # l'id du compte actuellement connecté
        )

        user = cursor.fetchone()

        if not user:  # cas rare : le compte a été supprimé de la base mais la session existe encore

            session.clear()  # on nettoie la session invalide

            return redirect(url_for("login"))

        # ----------------------------------------------
        # Nombre d'abonnés
        # ----------------------------------------------

        # "followers" = combien de personnes ME suivent (following_id = moi)
        cursor.execute(
            """
            SELECT COUNT(*) AS total
            FROM followers
            WHERE following_id = %s
            """,
            (user["id"],)
        )

        followers = cursor.fetchone()["total"]

        # ----------------------------------------------
        # Nombre d'abonnements
        # ----------------------------------------------

        # "following" = combien de personnes JE suis (follower_id = moi)
        cursor.execute(
            """
            SELECT COUNT(*) AS total
            FROM followers
            WHERE follower_id = %s
            """,
            (user["id"],)
        )

        following = cursor.fetchone()["total"]

        # ----------------------------------------------
        # Nombre de vidéos
        # ----------------------------------------------

        # On ne compte que les vidéos "active" : une vidéo supprimée/masquée
        # n'est jamais réellement effacée de la base, juste changée de statut.
        cursor.execute(
            """
            SELECT COUNT(*) AS total
            FROM videos
            WHERE user_id = %s
            AND status = 'active'
            """,
            (user["id"],)
        )

        videos = cursor.fetchone()["total"]

        # ----------------------------------------------
        # Portefeuille
        #
        # IMPORTANT : on lit creator_wallets (et non
        # l'ancienne table wallets, qui n'est jamais
        # mise à jour après l'inscription). C'est
        # creator_wallets qui est réellement crédité
        # par qualify_view() / credit_creator_for_view().
        # ----------------------------------------------

        cursor.execute(
            """
            SELECT
                available_balance AS balance,
                pending_balance,
                total_earned
            FROM creator_wallets
            WHERE user_id = %s
            """,
            (user["id"],)
        )

        wallet = cursor.fetchone()

        if wallet is None:  # nouvel inscrit qui n'a encore jamais visité /monetization

            wallet = {  # valeurs par défaut à zéro, pour que le template ne plante pas
                "balance": 0,
                "pending_balance": 0,
                "total_earned": 0
            }

        # ----------------------------------------------
        # Monétisation
        #
        # IMPORTANT : on lit monetization_accounts
        # (et non l'ancienne table monetization),
        # qui est la table réellement utilisée par
        # le dashboard /monetization.
        # ----------------------------------------------

        cursor.execute(
            """
            SELECT
                status
            FROM monetization_accounts
            WHERE user_id = %s
            """,
            (user["id"],)
        )

        monetization = cursor.fetchone()

        if monetization is None:  # même logique : compte pas encore rattaché à monetization_accounts

            monetization = {
                "status": "not_eligible"
            }

        # ----------------------------------------------
        # Total de likes reçus sur toutes mes vidéos
        # ----------------------------------------------

        # On joint likes <-> videos pour ne compter que les likes
        # posés sur DES VIDÉOS M'APPARTENANT (videos.user_id),
        # peu importe qui a mis le like.
        cursor.execute(
            """
            SELECT COUNT(*) AS total
            FROM likes
            INNER JOIN videos
                ON videos.id = likes.video_id
            WHERE videos.user_id = %s
            """,
            (user["id"],)
        )

        total_likes_received = cursor.fetchone()["total"]

        # ----------------------------------------------
        # Vidéos que j'ai aimées
        # ----------------------------------------------

        cursor.execute(
            """
            SELECT
                videos.id,
                videos.title,
                videos.video_url,
                videos.thumbnail_url,
                users.id AS creator_id,
                users.username AS creator_username,
                likes.created_at AS liked_at
            FROM likes
            INNER JOIN videos
                ON videos.id = likes.video_id
            INNER JOIN users
                ON users.id = videos.user_id
            WHERE likes.user_id = %s
            AND videos.status = 'active'
            ORDER BY likes.created_at DESC
            LIMIT 12
            """,
            (user["id"],)
        )

        liked_videos = cursor.fetchall()  # jusqu'à 12 vidéos, les plus récemment aimées en premier

        # ----------------------------------------------
        # Commentaires reçus sur MES vidéos, laissés par
        # les AUTRES utilisateurs (pas mes propres
        # commentaires)
        # ----------------------------------------------

        cursor.execute(
            """
            SELECT
                comments.id,
                comments.content,
                comments.created_at,
                videos.id AS video_id,
                videos.title AS video_title,
                users.id AS commenter_id,
                users.username AS commenter_username,
                users.profile_photo AS commenter_photo
            FROM comments
            INNER JOIN videos
                ON videos.id = comments.video_id
            INNER JOIN users
                ON users.id = comments.user_id
            WHERE videos.user_id = %s
            AND comments.user_id != %s
            ORDER BY comments.created_at DESC
            LIMIT 15
            """,
            (user["id"], user["id"])  # 1er %s : mes vidéos ; 2e %s : exclut mes propres commentaires
        )

        my_comments = cursor.fetchall()

        # On transmet toutes les données préparées ci-dessus au template
        # profile.html, qui se contente de les afficher (aucune requête
        # SQL n'est faite côté HTML/Jinja).
        return render_template(
            "profile.html",
            user=user,
            followers=followers,
            following=following,
            videos=videos,
            wallet=wallet,
            monetization=monetization,
            total_likes_received=total_likes_received,
            liked_videos=liked_videos,
            my_comments=my_comments
        )

    except Exception as error:  # si une des requêtes ci-dessus échoue (ex: MySQL coupé en cours de route)

        print("Erreur profil :", error)

        flash(
            "Impossible de charger le profil.",
            "error"
        )

        return redirect(url_for("index"))

    finally:  # toujours exécuté : on referme proprement la connexion, succès ou échec

        cursor.close()
        connection.close()




# ==========================================================
# PROFIL PUBLIC D'UN UTILISATEUR
# ==========================================================

@app.route("/user/<int:user_id>")
@login_required
def public_profile(user_id):

    connection = get_db_connection()

    # ------------------------------------------------------
    # Vérifier la connexion MySQL
    # ------------------------------------------------------

    if connection is None:

        flash(
            "Impossible de se connecter à MySQL.",
            "error"
        )

        return redirect(
            url_for("feed")
        )

    cursor = connection.cursor(
        dictionary=True
    )

    try:

        # ==================================================
        # 1. INFORMATIONS DE L'UTILISATEUR
        # ==================================================

        cursor.execute(
            """
            SELECT
                id,
                username,
                bio,
                profile_photo,
                created_at
            FROM users
            WHERE id = %s
            AND is_active = 1
            LIMIT 1
            """,
            (user_id,)
        )

        user = cursor.fetchone()

        if not user:

            flash(
                "Utilisateur introuvable.",
                "error"
            )

            return redirect(
                url_for("feed")
            )

        # ==================================================
        # 2. NOMBRE D'ABONNÉS
        # ==================================================

        cursor.execute(
            """
            SELECT
                COUNT(*) AS total
            FROM followers
            WHERE following_id = %s
            """,
            (user_id,)
        )

        followers = cursor.fetchone()["total"]

        # ==================================================
        # 3. NOMBRE D'ABONNEMENTS
        # ==================================================

        cursor.execute(
            """
            SELECT
                COUNT(*) AS total
            FROM followers
            WHERE follower_id = %s
            """,
            (user_id,)
        )

        following = cursor.fetchone()["total"]

        # ==================================================
        # 4. NOMBRE DE VIDÉOS
        # ==================================================

        cursor.execute(
            """
            SELECT
                COUNT(*) AS total
            FROM videos
            WHERE user_id = %s
            AND status = 'active'
            AND visibility = 'public'
            """,
            (user_id,)
        )

        videos_count = cursor.fetchone()["total"]

        # ==================================================
        # 5. VÉRIFIER SI L'UTILISATEUR CONNECTÉ LE SUIT
        # ==================================================
        # Sert à afficher "Suivre" ou "Abonné" sur le bouton follow
        # dès le chargement de la page (sans attendre un clic).

        is_following = False

        if user_id != session["user_id"]:  # inutile de vérifier si on regarde SON PROPRE profil

            cursor.execute(
                """
                SELECT
                    id
                FROM followers
                WHERE follower_id = %s
                AND following_id = %s
                LIMIT 1
                """,
                (
                    session["user_id"],  # moi (celui qui suit potentiellement)
                    user_id               # la personne dont on regarde le profil
                )
            )

            existing_follow = cursor.fetchone()

            if existing_follow:

                is_following = True

        # ==================================================
        # 6. RÉCUPÉRER LES VIDÉOS DU PROFIL
        # ==================================================
        # Chaque (SELECT COUNT(*) ...) entre parenthèses est une
        # "sous-requête corrélée" : elle est recalculée pour CHAQUE
        # vidéo renvoyée par la requête principale, afin d'ajouter
        # son nombre de likes/commentaires/vues/partages en une
        # seule requête globale (plutôt que N requêtes séparées).

        cursor.execute(
            """
            SELECT

                videos.id,
                videos.title,
                videos.description,
                videos.video_url,
                videos.thumbnail_url,
                videos.duration,
                videos.created_at,

                (
                    SELECT COUNT(*)
                    FROM likes
                    WHERE likes.video_id = videos.id
                ) AS likes_count,

                (
                    SELECT COUNT(*)
                    FROM comments
                    WHERE comments.video_id = videos.id
                ) AS comments_count,

                (
                    SELECT COUNT(DISTINCT views.user_id)
                    FROM views
                    WHERE views.video_id = videos.id
                ) AS views_count,

                (
                    SELECT COUNT(*)
                    FROM shares
                    WHERE shares.video_id = videos.id
                ) AS shares_count

            FROM videos

            WHERE videos.user_id = %s
            AND videos.status = 'active'       -- pas les vidéos supprimées/masquées
            AND videos.visibility = 'public'   -- pas les vidéos privées

            ORDER BY videos.created_at DESC    -- les plus récentes en premier
            """,
            (user_id,)
        )

        videos = cursor.fetchall()

        # ==================================================
        # 7. VÉRIFIER S'IL S'AGIT DE SON PROPRE PROFIL
        # ==================================================
        # Utile côté template pour, par exemple, cacher le bouton
        # "Suivre" quand on regarde SA PROPRE page publique.

        is_own_profile = (
            user_id == session["user_id"]
        )

        # ==================================================
        # 8. ENVOYER LES DONNÉES À LA PAGE HTML
        # ==================================================

        return render_template(
            "public_profile.html",
            user=user,
            followers=followers,
            following=following,
            videos_count=videos_count,
            videos=videos,
            is_following=is_following,
            is_own_profile=is_own_profile
        )

    # ======================================================
    # GESTION DES ERREURS
    # ======================================================

    except Exception as error:

        print(
            "===================================="
        )

        print(
            "ERREUR PROFIL PUBLIC :"
        )

        print(error)

        print(
            "===================================="
        )

        flash(
            "Impossible de charger ce profil.",
            "error"
        )

        return redirect(
            url_for("feed")
        )

    # ======================================================
    # FERMETURE MYSQL
    # ======================================================

    finally:

        cursor.close()
        connection.close()



# ==========================================================
# TEST MYSQL
# ==========================================================
# ⚠️ Route de DEBUG créée pendant le développement, pour
# vérifier rapidement que MySQL répond. Elle est accessible
# SANS connexion (pas de @login_required) et affiche des infos
# techniques sur la base : à supprimer ou protéger avant toute
# mise en ligne réelle.

@app.route("/test-db")
def test_db():

    connection = get_db_connection()

    if connection is None:

        return """
        <h1>❌ Connexion MySQL échouée</h1>
        """

    try:

        cursor = connection.cursor()  # pas besoin de dictionary=True : une seule valeur brute suffit ici

        cursor.execute("SELECT DATABASE()")  # demande à MySQL le nom de la base actuellement utilisée

        result = cursor.fetchone()  # ex: ('streamlocal_db',)

        cursor.close()
        connection.close()

        return f"""
        <h1>✅ MySQL fonctionne !</h1>
        <p>Base connectée : <strong>{result[0]}</strong></p>
        """

    except Exception as error:

        connection.close()

        return f"""
        <h1>❌ Erreur MySQL</h1>
        <p>{error}</p>
        """

# ==========================================================
# TEST TABLES
# ==========================================================
# ⚠️ Même remarque que /test-db : route de debug qui liste
# TOUTES les tables de la base publiquement. À protéger avant
# la mise en ligne (voir CORRECTIONS.md).

@app.route("/test-tables")
def test_tables():

    connection = get_db_connection()

    if connection is None:

        return "❌ Impossible de se connecter à MySQL."

    try:

        cursor = connection.cursor()

        cursor.execute("SHOW TABLES")  # commande MySQL native : renvoie la liste des tables de la base

        tables = cursor.fetchall()  # liste de tuples, ex: [('users',), ('videos',), ...]

        cursor.close()
        connection.close()

        html = """
        <h1>Tables StreamLocal</h1>
        <ul>
        """

        for table in tables:  # on construit la page HTML "à la main" (pas de template ici)

            html += f"<li>{table[0]}</li>"  # table[0] = le nom de la table (1er élément du tuple)

        html += """
        </ul>
        """

        return html  # Flask accepte de renvoyer directement une chaîne HTML, sans passer par render_template

    except Exception as error:

        connection.close()

        return f"""
        <h1>❌ Erreur</h1>
        <p>{error}</p>
        """

# ==========================================================
# FIL VIDEO
# ==========================================================

@app.route("/feed")
@login_required  # il faut être connecté pour voir le fil d'actualité
def feed():

    connection = get_db_connection()

    if connection is None:

        flash(
            "Impossible de se connecter à MySQL.",
            "error"
        )

        return redirect(url_for("index"))

    cursor = connection.cursor(dictionary=True)

    try:

        current_user_id = session["user_id"]  # utilisé plusieurs fois ci-dessous, autant le stocker une fois

        # Cette unique requête ramène TOUT ce qu'il faut pour afficher
        # le feed façon TikTok : la vidéo, son créateur, ses statistiques
        # (likes/commentaires/vues/partages) ET l'état personnel de
        # l'utilisateur connecté vis-à-vis de cette vidéo (déjà likée ?
        # déjà abonné au créateur ?). Tout est fait en SQL pour éviter
        # de multiplier les allers-retours avec la base.
        cursor.execute(
            """
            SELECT
                videos.id,
                videos.title,
                videos.description,
                videos.video_url,
                videos.thumbnail_url,
                videos.duration,
                videos.created_at,

                users.id AS user_id,        -- l'auteur de la vidéo (pas l'utilisateur connecté)
                users.username,
                users.profile_photo,

                (
                    SELECT COUNT(*)
                    FROM likes
                    WHERE likes.video_id = videos.id
                ) AS likes_count,

                (
                    SELECT COUNT(*)
                    FROM comments
                    WHERE comments.video_id = videos.id
                ) AS comments_count,

                (
    SELECT COUNT(DISTINCT views.user_id)
    FROM views
    WHERE views.video_id = videos.id
) AS views_count,                            -- DISTINCT : une même personne ne compte qu'une fois

                (
                    SELECT COUNT(*)
                    FROM shares
                    WHERE shares.video_id = videos.id
                ) AS shares_count,

                (
                    SELECT COUNT(*)
                    FROM likes
                    WHERE likes.video_id = videos.id
                    AND likes.user_id = %s
                ) AS user_has_liked,          -- 1 si JE (utilisateur connecté) ai déjà liké, sinon 0

                (
                    SELECT COUNT(*)
                    FROM followers
                    WHERE followers.follower_id = %s
                    AND followers.following_id = videos.user_id
                ) AS user_is_following        -- 1 si je suis déjà abonné à ce créateur, sinon 0

            FROM videos

            INNER JOIN users
                ON users.id = videos.user_id  -- récupère le pseudo/photo du créateur en une seule requête

            WHERE videos.status = 'active'       -- pas les vidéos supprimées
            AND videos.visibility = 'public'     -- pas les vidéos privées

            ORDER BY videos.created_at DESC      -- les plus récentes tout en haut du feed
            """,
            (
                current_user_id,  # correspond au 1er %s (user_has_liked)
                current_user_id   # correspond au 2e %s (user_is_following)
            )
        )

        videos = cursor.fetchall()  # la liste complète de vidéos à afficher, prête pour le template

        return render_template(
            "feed.html",
            videos=videos
        )

    except Exception as error:

        print("Erreur feed :", error)

        flash(
            "Impossible de charger les vidéos.",
            "error"
        )

        return redirect(url_for("index"))

    finally:

        cursor.close()
        connection.close()



# ==========================================================
# CRÉER UNE NOTIFICATION
# ==========================================================

def create_notification(
    user_id,           # à QUI la notification est destinée
    notification_type,  # ex: "like", "comment", "follow", "monetization"
    message,              # le texte affiché (déjà entièrement rédigé par l'appelant)
    reference_id=None      # ex: l'id de la vidéo concernée (facultatif)
):
    """
    Crée une notification pour un utilisateur.
    """

    # NOTE : cette fonction n'est PAS une route (pas de @app.route).
    # C'est une fonction "utilitaire" appelée depuis d'autres routes
    # (like_video, add_comment, follow_user, admin_update_monetization...)
    # à chaque fois qu'un événement mérite de prévenir quelqu'un.

    connection = get_db_connection()

    if connection is None:
        return False  # échec silencieux : on ne bloque jamais l'action principale (ex: le like) pour ça

    cursor = connection.cursor()  # pas besoin de dictionary=True : on n'insère rien, on ne lit rien ici

    try:

        cursor.execute(
            """
            INSERT INTO notifications
            (
                user_id,
                type,
                message,
                reference_id,
                is_read
            )
            VALUES
            (
                %s,
                %s,
                %s,
                %s,
                0
            )
            """,
            (
                user_id,
                notification_type,
                message,
                reference_id
            )
        )

        connection.commit()

        return True  # la notification a bien été enregistrée

    except Exception as error:

        connection.rollback()

        print(
            "Erreur création notification :",
            error
        )

        return False

    finally:

        cursor.close()
        connection.close()



# ==========================================================
# RECHERCHE
# ==========================================================

@app.route("/search")
@login_required
def search():

    # request.args = les paramètres dans l'URL (ex: /search?q=ravi)
    # request.form (vu dans register/login) sert lui aux données de FORMULAIRE POST.
    query = request.args.get("q", "").strip()

    users = []
    videos = []

    if not query:  # aucune recherche tapée : on affiche juste la page vide, pas de requête SQL inutile
        return render_template(
            "search.html",
            query=query,
            users=users,
            videos=videos
        )

    connection = get_db_connection()

    if connection is None:

        flash(
            "Impossible de se connecter à MySQL.",
            "error"
        )

        return redirect(url_for("feed"))

    cursor = connection.cursor(dictionary=True)

    try:

        # ==================================================
        # RECHERCHE DES UTILISATEURS
        # ==================================================

        # Le symbole % de LIKE veut dire "n'importe quels caractères" :
        # "%ravi%" trouve "ravi_junior", "monravioli", etc. (recherche partielle).
        search_pattern = f"%{query}%"

        cursor.execute(
            """
            SELECT
                id,
                username,
                profile_photo,
                bio
            FROM users
            WHERE is_active = 1        -- pas les comptes désactivés par l'admin
            AND username LIKE %s
            ORDER BY username ASC
            LIMIT 20                   -- on plafonne le nombre de résultats affichés
            """,
            (search_pattern,)
        )

        users = cursor.fetchall()

        # ==================================================
        # RECHERCHE DES VIDÉOS
        # ==================================================

        cursor.execute(
            """
            SELECT
                videos.id,
                videos.title,
                videos.description,
                videos.video_url,
                videos.thumbnail_url,
                videos.created_at,

                users.id AS user_id,
                users.username,
                users.profile_photo,

                categories.name AS category_name,

                (
                    SELECT COUNT(*)
                    FROM likes
                    WHERE likes.video_id = videos.id
                ) AS likes_count,

                (
                    SELECT COUNT(*)
                    FROM comments
                    WHERE comments.video_id = videos.id
                ) AS comments_count,

                (
                    SELECT COUNT(DISTINCT views.user_id)
                    FROM views
                    WHERE views.video_id = videos.id
                ) AS views_count

            FROM videos

            INNER JOIN users
                ON users.id = videos.user_id     -- INNER : une vidéo a TOUJOURS un créateur

            LEFT JOIN categories
                ON categories.id = videos.category_id  -- LEFT : une vidéo peut ne PAS avoir de catégorie

            WHERE videos.status = 'active'
            AND videos.visibility = 'public'

            AND (                                 -- correspond au titre, OU à la description, OU à la catégorie
                videos.title LIKE %s
                OR videos.description LIKE %s
                OR categories.name LIKE %s
            )

            ORDER BY videos.created_at DESC

            LIMIT 50
            """,
            (
                search_pattern,  # 1er %s → title
                search_pattern,  # 2e %s  → description
                search_pattern   # 3e %s  → categories.name
            )
        )

        videos = cursor.fetchall()

        return render_template(
            "search.html",
            query=query,
            users=users,
            videos=videos
        )

    except Exception as error:

        print(
            "Erreur recherche :",
            error
        )

        flash(
            "Une erreur est survenue pendant la recherche.",
            "error"
        )

        return redirect(url_for("feed"))

    finally:

        cursor.close()
        connection.close()


# ==========================================================
# PUBLICATION D'UNE VIDEO
# ==========================================================

@app.route("/upload", methods=["GET", "POST"])
@login_required
def upload_video():

    if request.method == "POST":

        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        category_id = request.form.get("category_id")  # peut être vide (catégorie facultative)

        # request.files (et pas request.form) : c'est ici que Flask range
        # les FICHIERS envoyés via un <input type="file"> du formulaire.
        video_file = request.files.get("video")

        # ----------------------------------------------
        # Vérification du fichier
        # ----------------------------------------------

        if not video_file or video_file.filename == "":  # aucun fichier sélectionné

            flash(
                "Veuillez sélectionner une vidéo.",
                "error"
            )

            return redirect(url_for("upload_video"))

        if not allowed_video(video_file.filename):  # extension non autorisée (voir ALLOWED_VIDEO_EXTENSIONS)

            flash(
                "Format vidéo non autorisé.",
                "error"
            )

            return redirect(url_for("upload_video"))

        # ----------------------------------------------
        # Nom sécurisé
        # ----------------------------------------------

        # secure_filename() nettoie le nom d'origine (enlève les espaces,
        # accents, "../" etc.) pour empêcher un nom de fichier malveillant
        # d'écrire en dehors du dossier prévu (path traversal).
        filename = secure_filename(video_file.filename)

        # Ajouter l'ID utilisateur pour éviter
        # certaines collisions de noms

        import uuid  # génère un identifiant unique quasi impossible à deviner/reproduire

        extension = filename.rsplit(".", 1)[1].lower()  # récupère juste l'extension (ex: "mp4")

        # On IGNORE volontairement le nom d'origine du fichier et on le
        # remplace entièrement : plus sûr (pas de nom en double, pas de
        # caractères piégés) et ça évite qu'un visiteur devine l'URL
        # d'une vidéo à partir de son nom d'origine.
        filename = (
            f"{session['user_id']}_"   # préfixe : qui a uploadé (utile pour le débogage)
            f"{uuid.uuid4().hex}."      # identifiant unique aléatoire
            f"{extension}"
        )

        filepath = os.path.join(
            app.config["UPLOAD_FOLDER"],  # streamlocal/uploads/videos/
            filename
        )

        video_file.save(filepath)  # écrit réellement le fichier sur le disque du serveur

        # ----------------------------------------------
        # URL de la vidéo
        # ----------------------------------------------

        # C'est cette URL qui sera stockée en base et utilisée dans les
        # balises <video src="..."> côté HTML (voir route uploaded_video juste après).
        video_url = f"/uploads/videos/{filename}"

        connection = get_db_connection()

        if connection is None:

            flash(
                "Impossible de se connecter à MySQL.",
                "error"
            )

            return redirect(url_for("upload_video"))

        cursor = connection.cursor()  # pas de dictionary=True : on ne lit rien ici, juste un INSERT

        try:

            # ------------------------------------------
            # Catégorie
            # ------------------------------------------

            if category_id:  # le champ n'était pas vide

                try:
                    category_id = int(category_id)  # doit être un nombre (l'id de la catégorie)
                except ValueError:
                    category_id = None  # valeur invalide envoyée : on l'ignore plutôt que de planter

            else:

                category_id = None  # champ laissé vide par l'utilisateur → NULL en base

            # ------------------------------------------
            # Enregistrer la vidéo
            # ------------------------------------------

            cursor.execute(
                """
                INSERT INTO videos
                (
                    user_id,
                    category_id,
                    title,
                    description,
                    video_url,
                    status,
                    visibility
                )
                VALUES
                (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    'active',
                    'public'
                )
                """,
                (
                    session["user_id"],  # le créateur = l'utilisateur connecté
                    category_id,
                    title,
                    description,
                    video_url
                )
            )

            connection.commit()

            flash(
                "🎉 Ta vidéo a été publiée !",
                "success"
            )

            return redirect(url_for("feed"))  # publication réussie : direction le fil d'actualité

        except Exception as error:

            connection.rollback()

            # Supprimer le fichier si l'insertion échoue
            # (sinon on aurait une vidéo orpheline sur le disque,
            # sans aucune ligne en base pour la retrouver).

            if os.path.exists(filepath):
                os.remove(filepath)

            print("Erreur publication :", error)

            flash(
                "Impossible de publier la vidéo.",
                "error"
            )

            return redirect(url_for("upload_video"))

        finally:

            cursor.close()
            connection.close()

    # ----------------------------------------------
    # Récupérer les catégories
    # ----------------------------------------------
    # (Requête GET : première visite de la page, on affiche
    # le formulaire avec la liste déroulante des catégories.)

    connection = get_db_connection()

    if connection is None:

        return "Erreur de connexion MySQL."

    cursor = connection.cursor(dictionary=True)

    try:

        cursor.execute(
            """
            SELECT
                id,
                name
            FROM categories
            ORDER BY name
            """
        )

        categories = cursor.fetchall()

        return render_template(
            "upload.html",
            categories=categories
        )

    finally:

        cursor.close()
        connection.close()


# ==========================================================
# SERVIR LES VIDEOS
# ==========================================================
# Cette route permet au navigateur d'accéder à un fichier vidéo
# uploadé (ex: /uploads/videos/3_ab12cd34....mp4). Sans elle, les
# fichiers du dossier uploads/videos/ ne seraient pas accessibles
# depuis le web — Flask ne sert pas automatiquement n'importe quel
# dossier par sécurité, il faut une route dédiée.

@app.route("/uploads/videos/<filename>")
def uploaded_video(filename):

    # send_from_directory : fonction Flask qui sert un fichier de façon
    # sécurisée (empêche par exemple filename="../../app.py" de fonctionner).
    return send_from_directory(
        app.config["UPLOAD_FOLDER"],
        filename
    )

# ==========================================================
# LIKE / UNLIKE
# ==========================================================

@app.route("/api/videos/<int:video_id>/like", methods=["POST"])
@login_required
def like_video(video_id):
    # Cette route est une API : appelée en JavaScript via fetch() depuis
    # feed.html (clic sur le cœur), pas en visitant une URL dans le
    # navigateur. Elle répond en JSON, pas avec une page HTML.

    connection = get_db_connection()

    if connection is None:
        return {"success": False, "message": "Erreur MySQL"}, 500  # 500 = code HTTP "erreur serveur"

    cursor = connection.cursor(dictionary=True)

    try:

        # On vérifie d'abord si CET utilisateur a DÉJÀ liké CETTE vidéo,
        # pour savoir s'il faut ajouter le like ou le retirer ("toggle").
        cursor.execute(
            """
            SELECT id
            FROM likes
            WHERE user_id = %s
            AND video_id = %s
            """,
            (session["user_id"], video_id)
        )

        existing_like = cursor.fetchone()

        if existing_like:  # le like existe déjà → on le retire (unlike)

            cursor.execute(
                """
                DELETE FROM likes
                WHERE user_id = %s
                AND video_id = %s
                """,
                (session["user_id"], video_id)
            )

            liked = False  # utilisé plus bas dans la réponse JSON, pour que le JS mette à jour le bouton


        else:  # pas encore liké → on l'ajoute

            cursor.execute(
                """
                INSERT INTO likes
                (user_id, video_id)
                VALUES (%s, %s)
                """,
                (session["user_id"], video_id)
            )

            liked = True

            # ==================================================
            # RÉCUPÉRER LE PROPRIÉTAIRE DE LA VIDÉO
            # ==================================================
            # (uniquement nécessaire ici, dans le cas "nouveau like",
            # pour lui envoyer une notification — pas utile en cas d'unlike)

            cursor.execute(
                """
                SELECT
                    user_id,
                    title
                FROM videos
                WHERE id = %s
                LIMIT 1
                """,
                (video_id,)
            )

            video_owner = cursor.fetchone()

            if (
                    video_owner
                    and video_owner["user_id"] != session["user_id"]  # on ne se notifie pas soi-même
            ):

                if video_owner["title"]:  # la vidéo a un titre : on le mentionne dans le message

                    message = (
                        f"@{session['username']} a aimé "
                        f"ta vidéo « {video_owner['title']} »."
                    )

                else:  # pas de titre : message générique pour éviter des guillemets vides « »

                    message = (
                        f"@{session['username']} a aimé "
                        f"ta vidéo."
                    )

                create_notification(
                    video_owner["user_id"],  # destinataire : le créateur de la vidéo
                    "like",
                    message,
                    video_id
                )

        connection.commit()  # valide le DELETE ou l'INSERT ci-dessus (+ la notification si créée)

        # On recompte le nombre total de likes APRÈS la modification,
        # pour renvoyer un chiffre à jour au JavaScript (affiché sous le cœur).
        cursor.execute(
            """
            SELECT COUNT(*) AS total
            FROM likes
            WHERE video_id = %s
            """,
            (video_id,)
        )

        likes_count = cursor.fetchone()["total"]

        return {
            "success": True,
            "liked": liked,           # true/false : le JS bascule la classe CSS "liked" du bouton
            "likes_count": likes_count  # nombre à afficher à côté du cœur
        }

    except Exception as error:

        connection.rollback()

        print("Erreur like :", error)

        return {
            "success": False,
            "message": "Impossible de modifier le like."
        }, 500

    finally:

        cursor.close()
        connection.close()


# ==========================================================
# SUIVRE / NE PLUS SUIVRE
# ==========================================================

@app.route(
    "/api/users/<int:user_id>/follow",
    methods=["POST"]
)
@login_required
def follow_user(user_id):
    # user_id = la personne qu'on veut suivre/ne plus suivre
    # session["user_id"] = moi, celui qui clique sur le bouton

    if user_id == session["user_id"]:  # empêche de s'auto-suivre

        return {
            "success": False,
            "message": "Tu ne peux pas te suivre toi-même."
        }, 400  # 400 = code HTTP "requête invalide"

    connection = get_db_connection()

    if connection is None:

        return {
            "success": False,
            "message": "Erreur MySQL."
        }, 500

    cursor = connection.cursor(dictionary=True)

    try:

        # Même logique de "toggle" que pour like_video() :
        # on vérifie d'abord si la relation existe déjà.
        cursor.execute(
            """
            SELECT id
            FROM followers
            WHERE follower_id = %s
            AND following_id = %s
            """,
            (
                session["user_id"],  # celui qui suit
                user_id                # celui qui est suivi
            )
        )

        existing_follow = cursor.fetchone()

        if existing_follow:  # déjà abonné → on se désabonne

            cursor.execute(
                """
                DELETE FROM followers
                WHERE follower_id = %s
                AND following_id = %s
                """,
                (
                    session["user_id"],
                    user_id
                )
            )

            following = False

        else:  # pas encore abonné → on s'abonne

            cursor.execute(
                """
                INSERT INTO followers
                (
                    follower_id,
                    following_id
                )
                VALUES (%s, %s)
                """,
                (
                    session["user_id"],
                    user_id
                )
            )

            following = True

            # ==============================================
            # NOTIFICATION DU NOUVEL ABONNÉ
            #
            # IMPORTANT : ce bloc doit rester DANS le
            # else (donc uniquement lors d'un follow).
            # Avant, il était exécuté aussi lors d'un
            # unfollow, ce qui envoyait une notification
            # incorrecte.
            # ==============================================

            if user_id != session["user_id"]:  # toujours vrai ici (déjà vérifié plus haut), sécurité en plus
                create_notification(
                    user_id,                    # destinataire : la personne qu'on vient de suivre
                    "follow",
                    f"@{session['username']} a commencé à te suivre.",
                    session["user_id"]           # reference_id : ici, l'id de celui qui suit
                )

        connection.commit()

        # Recompte le nombre total d'abonnés APRÈS la modification,
        # pour que le JS affiche un chiffre à jour.
        cursor.execute(
            """
            SELECT COUNT(*) AS total
            FROM followers
            WHERE following_id = %s
            """,
            (user_id,)
        )

        followers_count = cursor.fetchone()["total"]

        return {
            "success": True,
            "following": following,           # true/false : le JS met à jour le texte du bouton
            "followers_count": followers_count
        }

    except Exception as error:

        connection.rollback()

        print("Erreur follow :", error)

        return {
            "success": False,
            "message": "Impossible de modifier l'abonnement."
        }, 500

    finally:

        cursor.close()
        connection.close()


# ==========================================================
# VUE
# ==========================================================

@app.route(
    "/api/videos/<int:video_id>/view",
    methods=["POST"]
)
@login_required
def video_view(video_id):
    # Appelée en JS dès qu'une vidéo apparaît à l'écran dans le feed
    # (voir l'IntersectionObserver de feed.html). C'est le point de
    # départ du système de monétisation : chaque vue est enregistrée
    # ici, puis "qualifiée" plus tard si le visionnage dure 60s (voir
    # qualify_view() dans la section MONÉTISATION plus bas).

    connection = get_db_connection()

    if connection is None:
        return jsonify({
            "success": False,
            "message": "Erreur de connexion MySQL"
        }), 500

    cursor = connection.cursor(dictionary=True)

    try:

        user_id = session["user_id"]

        # ==================================================
        # VÉRIFIER QUE LA VIDÉO EXISTE
        # ==================================================

        cursor.execute(
            """
            SELECT id
            FROM videos
            WHERE id = %s
            AND status = 'active'
            AND visibility = 'public'
            LIMIT 1
            """,
            (video_id,)
        )

        video = cursor.fetchone()

        if not video:  # vidéo supprimée/privée/inexistante : on arrête tout de suite

            return jsonify({
                "success": False,
                "message": "Vidéo introuvable"
            }), 404


        # ==================================================
        # CHERCHER SI CET UTILISATEUR A DÉJÀ VU LA VIDÉO
        # ==================================================
        # But : ne créer qu'UNE SEULE ligne "views" par (utilisateur,
        # vidéo), même si l'utilisateur revoit la vidéo plusieurs fois
        # (scroll qui remonte, rafraîchissement de page, etc.).

        cursor.execute(
            """
            SELECT
                id,
                watch_duration,
                completed
            FROM views
            WHERE user_id = %s
            AND video_id = %s
            LIMIT 1
            """,
            (
                user_id,
                video_id
            )
        )

        existing_view = cursor.fetchone()


        # ==================================================
        # SI LA VUE EXISTE DÉJÀ
        # ==================================================

        if existing_view:  # déjà vue avant : on ne recrée rien, on réutilise le même view_id

            view_id = existing_view["id"]

            counted = False  # sert de signal au JS : "ce n'est pas une nouvelle vue"


        # ==================================================
        # SINON CRÉER UNE NOUVELLE VUE
        # ==================================================

        else:  # première fois que CET utilisateur voit CETTE vidéo

            cursor.execute(
                """
                INSERT INTO views
                (
                    user_id,
                    video_id,
                    watch_duration,
                    completed,
                    ip_address
                )
                VALUES
                (
                    %s,
                    %s,
                    0,
                    0,
                    %s
                )
                """,
                (
                    user_id,
                    video_id,
                    request.remote_addr  # adresse IP de l'utilisateur (conservée à titre indicatif)
                )
            )

            view_id = cursor.lastrowid  # id de la ligne "views" qu'on vient de créer

            counted = True

            connection.commit()  # on valide tout de suite (avant même de savoir si elle sera qualifiée)


        # ==================================================
        # COMPTER LES UTILISATEURS UNIQUES
        # ==================================================
        # DISTINCT : si un même utilisateur avait plusieurs lignes
        # (normalement impossible ici), il ne compterait qu'une fois.

        cursor.execute(
            """
            SELECT COUNT(DISTINCT user_id) AS total
            FROM views
            WHERE video_id = %s
            """,
            (video_id,)
        )

        views_count = cursor.fetchone()["total"]


        return jsonify({

            "success": True,

            "counted": counted,   # le JS s'en sert pour savoir si le compteur de vues doit être incrémenté à l'écran

            "view_id": view_id,   # réutilisé ensuite par update_watch_duration() / qualify_view()

            "views_count": views_count

        })


    except Exception as error:

        connection.rollback()

        print(
            "ERREUR ENREGISTREMENT VUE :",
            error
        )

        return jsonify({

            "success": False,

            "message": str(error)

        }), 500


    finally:

        cursor.close()

        connection.close()


# ==========================================================
# DURÉE DE VISIONNAGE
# ==========================================================

@app.route(
    "/api/views/<int:view_id>/watch",
    methods=["POST"]
)
@login_required
def update_watch_duration(view_id):
    # Appelée régulièrement en JS (toutes les quelques secondes) pendant
    # qu'une vidéo est en train d'être regardée, pour signaler au serveur
    # "voilà où on en est du visionnage". C'est ici que la bascule vers
    # une vue QUALIFIÉE (rémunérée) se déclenche, dès que 60s sont atteintes.

    connection = get_db_connection()

    if connection is None:
        return jsonify({
            "success": False,
            "message": "Erreur de connexion MySQL"
        }), 500

    cursor = connection.cursor(dictionary=True)

    try:

        data = request.get_json(silent=True) or {}  # lit le JSON envoyé par fetch() ; {} si absent/invalide

        try:
            watch_duration = int(
                data.get("watch_duration", 0)  # durée envoyée par le JS, en secondes
            )
        except (TypeError, ValueError):  # valeur reçue non convertible en entier (donnée corrompue/malveillante)
            watch_duration = 0

        # Empêcher les valeurs négatives
        if watch_duration < 0:
            watch_duration = 0

        # Limite de sécurité
        if watch_duration > 86400:  # 86400s = 24h : personne ne regarde une vidéo aussi longtemps, donc suspect
            watch_duration = 86400

        # ==================================================
        # RÉCUPÉRER LA VUE
        # ==================================================

        cursor.execute(
            """
            SELECT
                id,
                user_id,
                video_id,
                watch_duration,
                completed
            FROM views
            WHERE id = %s
            LIMIT 1
            """,
            (view_id,)
        )

        view = cursor.fetchone()

        if not view:  # id de vue inexistant (ex: appel avec un id inventé)

            return jsonify({
                "success": False,
                "message": "Vue introuvable"
            }), 404

        # ==================================================
        # VÉRIFIER QUE LA VUE APPARTIENT À L'UTILISATEUR
        # ==================================================
        # Sécurité : empêche un utilisateur d'appeler cette route avec
        # l'id de la vue de QUELQU'UN D'AUTRE pour manipuler ses données.

        if view["user_id"] != session["user_id"]:

            return jsonify({
                "success": False,
                "message": "Cette vue ne vous appartient pas"
            }), 403  # 403 = code HTTP "accès interdit"

        # ==================================================
        # NE JAMAIS DIMINUER LA DURÉE
        # ==================================================
        # max(...) : si le JS envoie par erreur une durée plus petite que
        # celle déjà enregistrée (ex: la vidéo a été relancée depuis le
        # début), on garde la plus grande valeur connue plutôt que de
        # "reculer" — la durée de visionnage ne doit jamais régresser.

        new_duration = max(
            int(view["watch_duration"] or 0),
            watch_duration
        )

        # ==================================================
        # 60 SECONDES ATTEINTES
        # ==================================================

        if new_duration >= 60:  # seuil officiel de "vue qualifiée" (rémunérable) de StreamLocal
            # La fonction qualify_view() s'occupe de :
            # - vérifier si la vue a déjà été payée
            # - créer le revenu
            # - créditer le portefeuille
            # - mettre completed = 1

            result = qualify_view(
                view_id,
                new_duration
            )

            print(
                "RESULTAT MONETISATION :",
                result
            )

            return jsonify({
                "success": True,
                "watch_duration": new_duration,
                "completed": 1,
                "monetization": result  # détail renvoyé au JS (utile pour du débogage côté navigateur aussi)
            })

        # ==================================================
        # MOINS DE 60 SECONDES
        # ==================================================
        # On se contente de mettre à jour la durée connue, sans
        # déclencher de rémunération (pas encore atteint le seuil).

        cursor.execute(
            """
            UPDATE views
            SET watch_duration = %s
            WHERE id = %s
            """,
            (
                new_duration,
                view_id
            )
        )

        connection.commit()

        return jsonify({
            "success": True,
            "watch_duration": new_duration,
            "completed": 0
        })

    finally:  # pas de bloc "except" ici : une erreur inattendue remonterait telle quelle (page d'erreur Flask)

        cursor.close()
        connection.close()


# ==========================================================
# PARTAGE
# ==========================================================

@app.route(
    "/api/videos/<int:video_id>/share",
    methods=["POST"]
)
@login_required
def share_video(video_id):
    # Contrairement au like ou au follow, un partage n'est PAS un
    # "toggle" : chaque clic ajoute une nouvelle ligne dans "shares"
    # (on peut partager plusieurs fois la même vidéo, pas de retrait possible).

    connection = get_db_connection()

    if connection is None:

        return {
            "success": False
        }, 500

    cursor = connection.cursor(dictionary=True)

    # ==================================================
    # PROPRIÉTAIRE DE LA VIDÉO
    # ==================================================
    # Récupéré AVANT le bloc try : si video_owner est None (vidéo
    # inexistante), le INSERT plus bas échouera proprement à cause
    # de la contrainte de clé étrangère, et sera intercepté par le except.

    cursor.execute(
        """
        SELECT
            user_id
        FROM videos
        WHERE id = %s
        LIMIT 1
        """,
        (video_id,)
    )

    video_owner = cursor.fetchone()

    try:


        cursor.execute(
            """
            INSERT INTO shares
            (
                user_id,
                video_id
            )
            VALUES (%s, %s)
            """,
            (
                session["user_id"],
                video_id
            )
        )

        connection.commit()

        # ==================================================
        # NOTIFICATION DU PARTAGE
        # ==================================================

        if (
                video_owner
                and video_owner["user_id"] != session["user_id"]  # pas de notif si on partage sa propre vidéo
        ):
            create_notification(
                video_owner["user_id"],
                "share",
                f"@{session['username']} a partagé ta vidéo.",
                video_id
            )

        # Recompte le nombre total de partages APRÈS l'ajout,
        # pour renvoyer un chiffre à jour au JavaScript.
        cursor.execute(
            """
            SELECT COUNT(*) AS total
            FROM shares
            WHERE video_id = %s
            """,
            (video_id,)
        )

        shares_count = cursor.fetchone()["total"]

        return {
            "success": True,
            "shares_count": shares_count
        }

    except Exception as error:  # ex: video_id inexistant → la clé étrangère de "shares" rejette l'INSERT

        connection.rollback()

        print("Erreur partage :", error)

        return {
            "success": False
        }, 500

    finally:

        cursor.close()
        connection.close()


# ==========================================================
# LISTE DES PERSONNES AYANT AIMÉ UNE VIDÉO
# ==========================================================

@app.route(
    "/api/videos/<int:video_id>/likes",
    methods=["GET"]
)
@login_required
def get_video_likes(video_id):
    # Appelée en JS quand on clique sur le chiffre à côté du cœur
    # dans le feed (voir feed.html, modale "Aimé par") : renvoie la
    # liste de TOUS les utilisateurs ayant aimé cette vidéo.

    connection = get_db_connection()

    if connection is None:
        return {
            "success": False,
            "message": "Erreur MySQL"
        }, 500

    cursor = connection.cursor(dictionary=True)

    try:

        cursor.execute(
            """
            SELECT
                users.id AS user_id,
                users.username,
                users.profile_photo,
                likes.created_at
            FROM likes
            INNER JOIN users
                ON users.id = likes.user_id  -- récupère pseudo/photo de chaque personne qui a liké
            WHERE likes.video_id = %s
            ORDER BY likes.created_at DESC   -- le like le plus récent en premier
            """,
            (video_id,)
        )

        likes = cursor.fetchall()

        return {
            "success": True,
            "likes": likes  # liste de dictionnaires {user_id, username, profile_photo, created_at}
        }

    except Exception as error:

        print("Erreur récupération likes :", error)

        return {
            "success": False,
            "message": "Impossible de récupérer les likes."
        }, 500

    finally:

        cursor.close()
        connection.close()


# ==========================================================
# COMMENTAIRES
# ==========================================================

@app.route(
    "/api/videos/<int:video_id>/comments",
    methods=["GET"]
)
@login_required
def get_comments(video_id):
    # Appelée en JS à l'ouverture de la modale commentaires (feed.html) :
    # renvoie TOUS les commentaires d'une vidéo, visibles par n'importe
    # quel visiteur — pas seulement le propriétaire de la vidéo.

    connection = get_db_connection()

    if connection is None:
        return {
            "success": False,
            "message": "Erreur MySQL"
        }, 500

    cursor = connection.cursor(dictionary=True)

    try:

        cursor.execute(
            """
            SELECT
                comments.id,
                comments.content,
                comments.created_at,

                users.id AS user_id,
                users.username,
                users.profile_photo

            FROM comments

            INNER JOIN users
                ON users.id = comments.user_id  -- récupère pseudo/photo de l'AUTEUR du commentaire

            WHERE comments.video_id = %s

            ORDER BY comments.created_at DESC   -- le plus récent en premier
            """,
            (video_id,)
        )

        comments = cursor.fetchall()

        return {
            "success": True,
            "comments": comments
        }

    except Exception as error:

        print("Erreur récupération commentaires :", error)

        return {
            "success": False,
            "message": "Impossible de récupérer les commentaires."
        }, 500

    finally:

        cursor.close()
        connection.close()


# ==========================================================
# AJOUTER UN COMMENTAIRE
# ==========================================================

@app.route(
    "/api/videos/<int:video_id>/comments",
    methods=["POST"]
)
@login_required
def add_comment(video_id):

    data = request.get_json()  # lit le corps JSON envoyé par le fetch() du formulaire de commentaire

    if not data:  # aucune donnée JSON reçue (ex: mauvais Content-Type côté JS)

        return {
            "success": False,
            "message": "Données invalides."
        }, 400

    content = data.get("content", "").strip()

    if not content:  # commentaire vide (juste des espaces par exemple)

        return {
            "success": False,
            "message": "Le commentaire est vide."
        }, 400

    if len(content) > 1000:  # protection contre un commentaire démesurément long

        return {
            "success": False,
            "message": "Commentaire trop long."
        }, 400

    connection = get_db_connection()

    if connection is None:

        return {
            "success": False,
            "message": "Erreur MySQL."
        }, 500

    cursor = connection.cursor(dictionary=True)

    try:

        # Vérifier que la vidéo existe

        cursor.execute(
            """
            SELECT
               id,
               user_id,
               title
            FROM videos
            WHERE id = %s
            AND status = 'active'
            """,
            (video_id,)
        )

        video = cursor.fetchone()

        if not video:  # vidéo supprimée ou id invalide

            return {
                "success": False,
                "message": "Vidéo introuvable."
            }, 404

        # ==================================================
        # PROPRIÉTAIRE DE LA VIDÉO
        #
        # IMPORTANT : cette ligne doit être APRÈS la
        # vérification "if not video", sinon le serveur
        # plante (erreur 500) quand la vidéo n'existe pas.
        # ==================================================

        video_owner_id = video["user_id"]

        # Ajouter le commentaire

        cursor.execute(
            """
            INSERT INTO comments
            (
                user_id,
                video_id,
                content
            )
            VALUES (%s, %s, %s)
            """,
            (
                session["user_id"],  # l'auteur du commentaire = utilisateur connecté
                video_id,
                content
            )
        )

        connection.commit()

        # ==================================================
        # NOTIFICATION DU COMMENTAIRE
        # ==================================================

        if video_owner_id != session["user_id"]:  # pas de notif si on commente sa propre vidéo

            if video["title"]:  # titre présent : on le précise dans le message

                message = (
                    f"@{session['username']} a commenté "
                    f"ta vidéo « {video['title']} »."
                )

            else:  # pas de titre : message générique

                message = (
                    f"@{session['username']} a commenté "
                    f"ta vidéo."
                )

            create_notification(
                video_owner_id,
                "comment",
                message,
                video_id
            )


        comment_id = cursor.lastrowid  # id du commentaire qu'on vient de créer

        # Récupérer le commentaire créé
        # (on le relit depuis la base plutôt que de le reconstruire à la
        # main, pour être sûr d'avoir exactement les mêmes données que
        # celles qui seront affichées si la page est rechargée : pseudo,
        # photo, date de création formatée par MySQL, etc.)

        cursor.execute(
            """
            SELECT
                comments.id,
                comments.content,
                comments.created_at,

                users.id AS user_id,
                users.username,
                users.profile_photo

            FROM comments

            INNER JOIN users
                ON users.id = comments.user_id

            WHERE comments.id = %s
            """,
            (comment_id,)
        )

        comment = cursor.fetchone()

        # Nombre total de commentaires

        cursor.execute(
            """
            SELECT COUNT(*) AS total
            FROM comments
            WHERE video_id = %s
            """,
            (video_id,)
        )

        comments_count = cursor.fetchone()["total"]

        return {
            "success": True,
            "comment": comment,               # renvoyé au JS pour l'afficher immédiatement dans la modale
            "comments_count": comments_count  # pour mettre à jour le chiffre sous l'icône 💬
        }

    except Exception as error:

        connection.rollback()

        print("Erreur ajout commentaire :", error)

        return {
            "success": False,
            "message": "Impossible d'ajouter le commentaire."
        }, 500

    finally:

        cursor.close()
        connection.close()


# ==========================================================
# SUPPRIMER SON COMMENTAIRE
# ==========================================================

@app.route(
    "/api/comments/<int:comment_id>",
    methods=["DELETE"]
)
@login_required
def delete_comment(comment_id):
    # DELETE (verbe HTTP) : appelée en JS quand l'auteur d'un commentaire
    # clique sur "supprimer" sur SON PROPRE commentaire.

    connection = get_db_connection()

    if connection is None:

        return {
            "success": False
        }, 500

    cursor = connection.cursor(dictionary=True)

    try:

        # AND user_id = %s : vérifie EN MÊME TEMPS que le commentaire existe
        # ET qu'il appartient bien à l'utilisateur connecté. Empêche donc
        # quelqu'un de supprimer le commentaire de quelqu'un d'autre en
        # devinant simplement son id.
        cursor.execute(
            """
            SELECT id
            FROM comments
            WHERE id = %s
            AND user_id = %s
            """,
            (
                comment_id,
                session["user_id"]
            )
        )

        comment = cursor.fetchone()

        if not comment:  # soit le commentaire n'existe pas, soit il appartient à quelqu'un d'autre

            return {
                "success": False,
                "message": "Commentaire introuvable."
            }, 404

        # Même double condition (id + user_id) pour la suppression réelle :
        # même si la vérification ci-dessus a réussi, on la répète par
        # sécurité (défense en profondeur).
        cursor.execute(
            """
            DELETE FROM comments
            WHERE id = %s
            AND user_id = %s
            """,
            (
                comment_id,
                session["user_id"]
            )
        )

        connection.commit()

        return {
            "success": True
        }

    except Exception as error:

        connection.rollback()

        print("Erreur suppression commentaire :", error)

        return {
            "success": False,
            "message": "Impossible de supprimer le commentaire."
        }, 500

    finally:

        cursor.close()
        connection.close()


# ==========================================================
# DASHBOARD MONÉTISATION
# ==========================================================

@app.route("/monetization")
@login_required  # dashboard personnel : réservé à l'utilisateur connecté, sur SES propres statistiques
def monetization_dashboard():
    # Vue d'ensemble du statut de monétisation d'un créateur : ses
    # statistiques, s'il remplit les conditions d'éligibilité (fixées
    # par l'admin via /admin/settings), son portefeuille et son historique.

    connection = get_db_connection()

    if connection is None:
        flash(
            "Erreur de connexion à MySQL.",
            "error"
        )
        return redirect(url_for("feed"))

    cursor = connection.cursor(dictionary=True)

    try:

        user_id = session["user_id"]

        # ==================================================
        # 1. RÉCUPÉRER LES CONDITIONS DE MONÉTISATION
        # ==================================================
        # Ces seuils viennent de la table admin_settings, modifiable
        # par l'administrateur depuis /admin/settings — donc PAS codés
        # en dur ici : si l'admin change "minimum_followers", ce
        # dashboard reflète immédiatement la nouvelle valeur.

        cursor.execute(
            """
            SELECT
                setting_key,
                setting_value
            FROM admin_settings
            WHERE setting_key IN (
                'minimum_followers',
                'minimum_views',
                'minimum_videos',
                'minimum_account_age',
                'minimum_withdrawal'
            )
            """
        )

        settings_rows = cursor.fetchall()

        settings = {}  # transforme la liste de lignes SQL en dictionnaire {clé: valeur} facile à utiliser

        for row in settings_rows:

            settings[row["setting_key"]] = int(
                row["setting_value"]  # setting_value est stocké en texte (varchar) dans la table, d'où int()
            )

        # .get(clé, valeur_par_défaut) : si jamais une ligne manquait en
        # base (table vidée par erreur, etc.), on retombe sur une valeur
        # raisonnable plutôt que de planter.
        minimum_followers = settings.get(
            "minimum_followers",
            5000
        )

        minimum_views = settings.get(
            "minimum_views",
            100000
        )

        minimum_videos = settings.get(
            "minimum_videos",
            10
        )

        minimum_account_age = settings.get(
            "minimum_account_age",
            30
        )

        minimum_withdrawal = settings.get(
            "minimum_withdrawal",
            5000
        )

        # ==================================================
        # 2. INFORMATIONS DU CRÉATEUR
        # ==================================================

        cursor.execute(
            """
            SELECT
                id,
                username,
                created_at
            FROM users
            WHERE id = %s
            LIMIT 1
            """,
            (user_id,)
        )

        user = cursor.fetchone()

        if not user:  # cas rare : compte supprimé mais session encore active

            session.clear()

            return redirect(
                url_for("login")
            )

        # ==================================================
        # 3. NOMBRE D'ABONNÉS
        # ==================================================

        cursor.execute(
            """
            SELECT COUNT(*) AS total
            FROM followers
            WHERE following_id = %s
            """,
            (user_id,)
        )

        total_followers = cursor.fetchone()["total"]

        # ==================================================
        # 4. NOMBRE DE VIDÉOS
        # ==================================================

        cursor.execute(
            """
            SELECT COUNT(*) AS total
            FROM videos
            WHERE user_id = %s
            AND status = 'active'
            """,
            (user_id,)
        )

        total_videos = cursor.fetchone()["total"]

        # ==================================================
        # 5. NOMBRE TOTAL DE VUES
        #
        # Une ligne de views = une vue enregistrée.
        # ==================================================

        cursor.execute(
            """
            SELECT COUNT(*) AS total
            FROM views v
            INNER JOIN videos vid
                ON vid.id = v.video_id
            WHERE vid.user_id = %s
            """,
            (user_id,)
        )

        total_views = cursor.fetchone()["total"]

        # ==================================================
        # 6. ANCIENNETÉ DU COMPTE
        # ==================================================

        cursor.execute(
            """
            SELECT
                DATEDIFF(
                    CURDATE(),
                    DATE(created_at)
                ) AS account_age
            FROM users
            WHERE id = %s
            """,
            (user_id,)
        )

        account_age = cursor.fetchone()["account_age"] or 0

        # ==================================================
        # 7. VÉRIFICATION DES CONDITIONS
        # ==================================================
        # Chaque *_ok est un booléen (True/False) indiquant si CETTE
        # condition précise est remplie ; "eligible" n'est True QUE si
        # LES 4 conditions le sont en même temps.

        followers_ok = (
            total_followers >= minimum_followers
        )

        views_ok = (
            total_views >= minimum_views
        )

        videos_ok = (
            total_videos >= minimum_videos
        )

        account_age_ok = (
            account_age >= minimum_account_age
        )

        eligible = (
            followers_ok
            and views_ok
            and videos_ok
            and account_age_ok
        )

        # ==================================================
        # 8. RÉCUPÉRER LE COMPTE DE MONÉTISATION
        # ==================================================

        cursor.execute(
            """
            SELECT
                status,
                total_views,
                total_followers,
                eligible_at,
                activated_at,
                suspended_at,
                suspension_reason
            FROM monetization_accounts
            WHERE user_id = %s
            LIMIT 1
            """,
            (user_id,)
        )

        monetization = cursor.fetchone()

        # ==================================================
        # 9. CRÉER LE COMPTE S'IL N'EXISTE PAS
        # ==================================================
        # Un nouvel inscrit n'a pas encore de ligne dans
        # monetization_accounts : elle est créée à sa toute première
        # visite de cette page (au lieu d'être créée dès l'inscription).

        if monetization is None:

            cursor.execute(
                """
                INSERT INTO monetization_accounts
                (
                    user_id,
                    status,
                    total_views,
                    total_followers
                )
                VALUES
                (
                    %s,
                    %s,
                    %s,
                    %s
                )
                """,
                (
                    user_id,
                    "eligible"
                    if eligible
                    else "not_eligible",
                    total_views,
                    total_followers
                )
            )

            connection.commit()

        else:

            # ==============================================
            # NE PAS ÉCRASER UN COMPTE SUSPENDU
            # ==============================================
            # RÈGLE CLÉ DU SYSTÈME : "active" et "suspended" sont des
            # statuts posés MANUELLEMENT par l'administrateur (voir
            # /admin/accounts/<id>/monetization). Ce recalcul automatique
            # ne doit JAMAIS les écraser tout seul — sinon un admin qui
            # suspend un compte le verrait redevenir actif au prochain
            # calcul, ce qui rendrait la modération inutile. Seuls
            # "eligible" et "not_eligible" sont recalculés à chaque
            # visite, en fonction des vraies statistiques du moment.

            if monetization["status"] == "suspended":

                new_status = "suspended"  # on garde tel quel, décision admin prioritaire

            elif monetization["status"] == "active":

                new_status = "active"  # idem : décision admin prioritaire

            elif eligible:

                new_status = "eligible"  # calcul automatique : les 4 conditions sont réunies

            else:

                new_status = "not_eligible"  # calcul automatique : au moins une condition manque

            # ==============================================
            # METTRE À JOUR LES STATISTIQUES
            # ==============================================

            cursor.execute(
                """
                UPDATE monetization_accounts
                SET
                    total_views = %s,
                    total_followers = %s,
                    status = %s,

                    eligible_at =
                        CASE
                            WHEN %s = 1
                            AND eligible_at IS NULL
                            THEN NOW()
                            ELSE eligible_at
                        END

                WHERE user_id = %s
                """,
                (
                    total_views,
                    total_followers,
                    new_status,
                    1 if eligible else 0,  # sert uniquement à alimenter le CASE ci-dessus (SQL n'a pas de booléen Python)
                    user_id
                )
            )
            # NOTE sur le CASE ci-dessus : "eligible_at" enregistre la
            # date à laquelle le compte est devenu éligible pour la
            # TOUTE PREMIÈRE fois. On ne la modifie que si elle est
            # encore NULL (jamais atteinte avant) ET que la condition
            # est remplie maintenant — sinon on la laisse inchangée.

            connection.commit()

        # ==================================================
        # 10. RELIRE LES INFORMATIONS
        # ==================================================
        # On relit depuis la base (plutôt que de réutiliser les
        # variables Python ci-dessus) pour être certain d'avoir
        # exactement ce qui est stocké, y compris les valeurs que
        # MySQL vient de calculer (comme eligible_at via NOW()).

        cursor.execute(
            """
            SELECT
                status,
                total_views,
                total_followers,
                eligible_at,
                activated_at,
                suspended_at,
                suspension_reason
            FROM monetization_accounts
            WHERE user_id = %s
            LIMIT 1
            """,
            (user_id,)
        )

        monetization = cursor.fetchone()

        # ==================================================
        # 11. PORTEFEUILLE
        # ==================================================
        # IMPORTANT : "creator_wallets" est la VRAIE table utilisée
        # pour l'argent réel du créateur (créditée par
        # credit_creator_for_view(), voir plus bas). Ne pas confondre
        # avec l'ancienne table "wallets" (créée à l'inscription mais
        # jamais mise à jour depuis).

        cursor.execute(
            """
            SELECT
                available_balance,
                pending_balance,
                total_earned,
                total_withdrawn,
                currency
            FROM creator_wallets
            WHERE user_id = %s
            LIMIT 1
            """,
            (user_id,)
        )

        wallet = cursor.fetchone()

        # ==================================================
        # 12. CRÉER LE PORTEFEUILLE S'IL N'EXISTE PAS
        # ==================================================
        # Même logique que pour monetization_accounts : créé à la
        # première visite plutôt qu'à l'inscription.

        if wallet is None:

            cursor.execute(
                """
                INSERT INTO creator_wallets
                (
                    user_id,
                    available_balance,
                    pending_balance,
                    total_earned,
                    total_withdrawn,
                    currency
                )
                VALUES
                (
                    %s,
                    0,
                    0,
                    0,
                    0,
                    'XAF'
                )
                """,
                (user_id,)
            )

            connection.commit()

            # On construit nous-mêmes ce dictionnaire (au lieu de
            # relire la base) car on connaît déjà ces valeurs : elles
            # viennent tout juste d'être insérées, toutes à zéro.
            wallet = {

                "available_balance": 0,

                "pending_balance": 0,

                "total_earned": 0,

                "total_withdrawn": 0,

                "currency": "XAF"

            }

        # ==================================================
        # 13. REVENUS RÉCENTS
        # ==================================================
        # Historique détaillé de chaque paiement reçu (une ligne par
        # vue qualifiée payée), créé par credit_creator_for_view().

        cursor.execute(
            """
            SELECT
                id,
                video_id,
                source,
                amount,
                currency,
                description,
                status,
                created_at
            FROM creator_earnings
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT 10
            """,
            (user_id,)
        )

        earnings = cursor.fetchall()

        # ==================================================
        # 14. RETRAITS RÉCENTS
        # ==================================================

        cursor.execute(
            """
            SELECT
                id,
                amount,
                currency,
                operator,
                phone,
                status,
                payment_reference,
                deposit_id,
                created_at,
                processed_at
            FROM withdrawal_requests
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT 10
            """,
            (user_id,)
        )

        withdrawals = cursor.fetchall()

        # ==================================================
        # 15. PROGRESSION
        # ==================================================
        # Convertit chaque statistique en pourcentage (0-100) pour
        # afficher les barres de progression sur la page monetization.html
        # (ex: "3200/5000 abonnés" → 64%). min(100, ...) empêche de
        # dépasser 100% si le créateur a largement dépassé le minimum.

        progress_followers = min(
            100,
            int(
                total_followers
                / minimum_followers
                * 100
            )
        )

        progress_views = min(
            100,
            int(
                total_views
                / minimum_views
                * 100
            )
        )

        progress_videos = min(
            100,
            int(
                total_videos
                / minimum_videos
                * 100
            )
        )

        progress_age = min(
            100,
            int(
                account_age
                / minimum_account_age
                * 100
            )
        )

        # ==================================================
        # 16. ENVOYER TOUT À LA PAGE
        # ==================================================
        # Toutes les variables calculées ci-dessus sont transmises
        # d'un coup au template monetization.html.

        return render_template(

            "monetization.html",

            wallet=wallet,

            monetization=monetization,

            earnings=earnings,

            withdrawals=withdrawals,

            total_followers=total_followers,

            total_views=total_views,

            total_videos=total_videos,

            account_age=account_age,

            minimum_followers=minimum_followers,

            minimum_views=minimum_views,

            minimum_videos=minimum_videos,

            minimum_account_age=minimum_account_age,

            minimum_withdrawal=minimum_withdrawal,

            followers_ok=followers_ok,

            views_ok=views_ok,

            videos_ok=videos_ok,

            account_age_ok=account_age_ok,

            eligible=eligible,

            progress_followers=progress_followers,

            progress_views=progress_views,

            progress_videos=progress_videos,

            progress_age=progress_age

        )

    except Exception as error:

        connection.rollback()

        print(
            "Erreur dashboard monétisation :",
            error
        )

        flash(
            "Impossible de charger la monétisation.",
            "error"
        )

        return redirect(
            url_for("feed")
        )

    finally:

        cursor.close()
        connection.close()

# ==========================================================
# FORMULAIRE DE RETRAIT
# ==========================================================

@app.route("/withdraw", methods=["GET", "POST"])
@login_required
def withdraw():
    # Formulaire de demande de retrait Mobile Money. GET = afficher le
    # formulaire ; POST = traiter la demande envoyée.

    connection = get_db_connection()

    if connection is None:
        flash("Erreur de connexion à la base de données.", "error")
        return redirect(url_for("monetization_dashboard"))

    cursor = connection.cursor(dictionary=True)

    user_id = session["user_id"]

    try:

        # --------------------------------------------------
        # Montant minimum de retrait (configuré par l'admin)
        # --------------------------------------------------
        # Lu depuis admin_settings (modifiable dans /admin/settings) :
        # c'est la MÊME source que celle utilisée par le dashboard
        # monétisation, pour que les deux pages affichent toujours le
        # même montant minimum (évite toute incohérence entre les pages).

        cursor.execute(
            """
            SELECT setting_value
            FROM admin_settings
            WHERE setting_key = 'minimum_withdrawal'
            LIMIT 1
            """
        )

        setting_row = cursor.fetchone()

        try:
            minimum_withdrawal = int(
                setting_row["setting_value"]
            ) if setting_row else 5000  # valeur de secours si le réglage est introuvable en base
        except (TypeError, ValueError):
            minimum_withdrawal = 5000

        # --------------------------------------------------
        # Récupérer le portefeuille
        # --------------------------------------------------

        cursor.execute(
            """
            SELECT
                available_balance,
                pending_balance,
                total_earned,
                total_withdrawn,
                currency
            FROM creator_wallets
            WHERE user_id = %s
            """,
            (user_id,)
        )

        wallet = cursor.fetchone()

        # --------------------------------------------------
        # Si aucun portefeuille
        # --------------------------------------------------
        # Cas rare : un utilisateur qui n'est jamais passé par
        # /monetization (qui crée automatiquement le portefeuille)
        # ne peut pas encore demander de retrait.

        if wallet is None:

            flash(
                "Ton portefeuille n'existe pas encore.",
                "error"
            )

            return redirect(
                url_for("monetization_dashboard")
            )

        # --------------------------------------------------
        # TRAITEMENT DU FORMULAIRE
        # --------------------------------------------------

        if request.method == "POST":

            amount_text = request.form.get("amount", "").strip()
            operator = request.form.get("operator", "").strip()  # "MOMO" (MTN) ou "OM" (Orange Money)
            phone = request.form.get("phone", "").strip()

            # ----------------------------------------------
            # Vérification du montant
            # ----------------------------------------------

            try:

                amount = float(amount_text)  # convertit le texte du formulaire en nombre décimal

            except ValueError:  # texte non numérique tapé dans le champ

                flash(
                    "Le montant doit être un nombre.",
                    "error"
                )

                return render_template(
                    "withdraw.html",
                    wallet=wallet,
                    minimum_withdrawal=minimum_withdrawal
                )

            # ----------------------------------------------
            # Montant minimum
            # ----------------------------------------------

            if amount < minimum_withdrawal:

                flash(
                    f"Le montant minimum de retrait est de "
                    f"{minimum_withdrawal:.0f} FCFA.",
                    "error"
                )

                return render_template(
                    "withdraw.html",
                    wallet=wallet,
                    minimum_withdrawal=minimum_withdrawal
                )

            # ----------------------------------------------
            # Vérifier le solde
            # ----------------------------------------------

            if amount > float(wallet["available_balance"]):  # on ne peut pas retirer plus que ce qu'on a

                flash(
                    "Solde insuffisant.",
                    "error"
                )

                return render_template(
                    "withdraw.html",
                    wallet=wallet,
                    minimum_withdrawal=minimum_withdrawal
                )

            # ----------------------------------------------
            # Vérifier opérateur
            # ----------------------------------------------

            if operator not in ["MOMO", "OM"]:  # seules ces deux valeurs sont acceptées (voir withdraw.html)

                flash(
                    "Opérateur de paiement invalide.",
                    "error"
                )

                return render_template(
                    "withdraw.html",
                    wallet=wallet,
                    minimum_withdrawal=minimum_withdrawal
                )

            # ----------------------------------------------
            # Vérifier numéro camerounais
            # ----------------------------------------------

            import re  # module Python pour les expressions régulières (motifs de texte)

            if not re.match(
                r"^2376[0-9]{8}$",  # doit commencer par "2376" puis exactement 8 chiffres (format camerounais)
                phone
            ):

                flash(
                    "Numéro invalide. Exemple : 237677123456",
                    "error"
                )

                return render_template(
                    "withdraw.html",
                    wallet=wallet,
                    minimum_withdrawal=minimum_withdrawal
                )

            # ----------------------------------------------
            # Solde avant retrait
            # ----------------------------------------------
            # Ces deux valeurs (avant/après) sont conservées pour être
            # inscrites telles quelles dans l'historique wallet_transactions
            # un peu plus bas — utile pour retracer l'évolution du solde.

            balance_before = float(
                wallet["available_balance"]
            )

            balance_after = (
                balance_before - amount
            )

            # ----------------------------------------------
            # Créer la demande de retrait
            # ----------------------------------------------
            # status = 'processing' au départ : la demande est "en cours",
            # avant d'être basculée sur 'completed' juste plus bas
            # (puisqu'ici, le paiement est SIMULÉ, pas un vrai virement).

            cursor.execute(
                """
                INSERT INTO withdrawal_requests
                (
                    user_id,
                    amount,
                    currency,
                    operator,
                    phone,
                    status
                )
                VALUES
                (
                    %s,
                    %s,
                    'XAF',
                    %s,
                    %s,
                    'processing'
                )
                """,
                (
                    user_id,
                    amount,
                    operator,
                    phone
                )
            )

            withdrawal_id = cursor.lastrowid  # id de la demande qu'on vient de créer, réutilisé plus bas

            # ----------------------------------------------
            # Déduire l'argent du portefeuille
            # ----------------------------------------------
            # On soustrait le montant retiré du solde disponible, et on
            # l'ajoute au cumul "total_withdrawn" (statistique affichée
            # sur le dashboard de monétisation).

            cursor.execute(
                """
                UPDATE creator_wallets
                SET
                    available_balance =
                        available_balance - %s,

                    total_withdrawn =
                        total_withdrawn + %s,

                    updated_at = CURRENT_TIMESTAMP

                WHERE user_id = %s
                """,
                (
                    amount,
                    amount,
                    user_id
                )
            )

            # ----------------------------------------------
            # Ajouter la transaction dans le portefeuille
            # ----------------------------------------------
            # Ligne d'historique à but purement informatif/traçabilité :
            # garde une trace permanente de ce mouvement d'argent, même
            # si withdrawal_requests était modifié ou supprimé plus tard.

            cursor.execute(
                """
                INSERT INTO wallet_transactions
                (
                    user_id,
                    type,
                    amount,
                    balance_before,
                    balance_after,
                    reference_type,
                    reference_id,
                    description
                )
                VALUES
                (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
                """,
                (
                    user_id,
                    "withdrawal",
                    amount,
                    balance_before,
                    balance_after,
                    "withdrawal",
                    withdrawal_id,
                    "Retrait de " + operator
                )
            )

            # ----------------------------------------------
            # Simulation du paiement
            # ----------------------------------------------
            # ⚠️ Aucun vrai argent n'est envoyé : ce projet simule le
            # paiement Mobile Money en marquant directement la demande
            # comme "réussie", avec une référence de paiement inventée
            # ("SIMULATED-..."). Une vraie intégration Mobile Money
            # (API MTN/Orange) remplacerait ce bloc par un vrai appel
            # réseau, avec un statut "processing" tant que la banque
            # n'a pas confirmé.

            cursor.execute(
                """
                UPDATE withdrawal_requests
                SET
                    status = 'completed',
                    payment_reference = %s,
                    processed_at = CURRENT_TIMESTAMP

                WHERE id = %s
                """,
                (
                    "SIMULATED-"
                    + str(withdrawal_id),

                    withdrawal_id
                )
            )

            connection.commit()  # valide TOUTES les requêtes ci-dessus (INSERT + 2 UPDATE) en une seule fois

            flash(
                f"Retrait simulé de {amount:.0f} FCFA réussi !",
                "success"
            )

            return redirect(
                url_for("monetization_dashboard")
            )

        # --------------------------------------------------
        # AFFICHAGE DU FORMULAIRE
        # --------------------------------------------------
        # Requête GET (première visite de la page) : on affiche
        # juste le formulaire vide, avec le solde actuel.

        return render_template(
            "withdraw.html",
            wallet=wallet,
            minimum_withdrawal=minimum_withdrawal
        )


    except Exception as error:

        connection.rollback()  # annule tout INSERT/UPDATE partiel fait avant l'erreur (évite un état incohérent)

        print("====================================")

        print("ERREUR RETRAIT :")

        print(error)

        print("====================================")

        flash(

            f"Erreur retrait : {error}",  # message détaillé affiché à l'utilisateur (pratique en développement)

            "error"

        )

        return redirect(

            url_for("monetization_dashboard")

        )

    finally:

        cursor.close()
        connection.close()


@app.route("/withdrawals")
@login_required
def withdrawals():
    # Page qui liste TOUS les retraits déjà effectués par l'utilisateur
    # connecté (historique complet, sans limite de nombre).

    connection = get_db_connection()

    if connection is None:
        flash("Erreur de connexion à la base de données.", "error")
        return redirect(url_for("monetization_dashboard"))

    cursor = connection.cursor(dictionary=True)

    user_id = session["user_id"]

    try:
        cursor.execute(
            """
            SELECT
                id,
                amount,
                currency,
                operator,
                phone,
                status,
                payment_reference,
                created_at,
                processed_at
            FROM withdrawal_requests
            WHERE user_id = %s
            ORDER BY created_at DESC   -- le retrait le plus récent en premier
            """,
            (user_id,)
        )

        withdrawals = cursor.fetchall()  # attention : ce nom réutilise (localement) celui de la fonction elle-même

        return render_template(
            "withdrawals.html",
            withdrawals=withdrawals
        )

    except Exception as error:

        print("Erreur historique retraits :", error)

        flash(
            "Impossible de récupérer l'historique.",
            "error"
        )

        return redirect(
            url_for("monetization_dashboard")
        )

    finally:
        cursor.close()
        connection.close()


# ==========================================================
# FONCTIONS UTILITAIRES DE LA MONÉTISATION
# ==========================================================
# À partir d'ici : des fonctions PYTHON (pas des routes @app.route),
# appelées depuis plusieurs endroits du code (video_view,
# update_watch_duration...) pour gérer le cœur du système de paiement
# des créateurs.

def get_revenue_rate():
    """
    Renvoie le montant (en XAF) payé pour 1000 vues qualifiées.
    Valeur configurable par l'administrateur (table
    monetization_settings, modifiable depuis /admin/settings).
    """

    connection = get_db_connection()

    if connection is None:
        return 500  # valeur de secours si MySQL est injoignable (500 XAF / 1000 vues par défaut)

    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT setting_value
            FROM monetization_settings
            WHERE setting_name = 'revenue_per_1000_views'
            LIMIT 1
            """
        )

        setting = cursor.fetchone()

        if setting:  # le réglage existe bien en base
            return float(setting["setting_value"])  # ex: "500" (texte) devient 500.0 (nombre)

        return 500  # aucune ligne trouvée : valeur de secours

    except Exception as error:

        print("Erreur tarif monétisation :", error)

        return 500  # erreur SQL quelconque : on ne bloque jamais le paiement pour autant, valeur de secours

    finally:
        cursor.close()
        connection.close()


def credit_creator_for_view(
    creator_id,       # qui recevoir l'argent (le créateur de la vidéo)
    video_id,          # la vidéo concernée (pour l'historique)
    qualified_view      # booléen : True seulement si qualify_view() a confirmé une vue de ≥60s
):
    """
    Crédite le portefeuille d'un créateur pour UNE vue qualifiée.
    Appelée uniquement par qualify_view() ci-dessous — jamais
    directement par une route.
    """

    if not qualified_view:  # sécurité : ne devrait jamais arriver vu où la fonction est appelée, mais on vérifie quand même
        return 0

    connection = get_db_connection()

    if connection is None:
        return 0

    cursor = connection.cursor(dictionary=True)

    try:

        # Tarif actuel
        rate = get_revenue_rate()  # ex: 500 (XAF pour 1000 vues), modifiable par l'admin

        # Une vue qualifiée rapporte :
        amount = rate / 1000  # ex: 500 / 1000 = 0.5 XAF pour CETTE vue précise



        # Ajouter le revenu
        # Une ligne d'historique par vue payée : permet d'afficher le
        # détail "Revenus récents" sur le dashboard de monétisation.
        cursor.execute(
            """
            INSERT INTO creator_earnings
            (
                user_id,
                video_id,
                source,
                amount,
                currency,
                description,
                status
            )
            VALUES
            (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s
            )
            """,
            (
                creator_id,
                video_id,
                "video_view",
                amount,
                "XAF",
                "Revenu généré par une vue qualifiée",
                "approved"  # pas de validation manuelle nécessaire : approuvé automatiquement
            )
        )

        # Créditer le portefeuille
        # C'est CETTE ligne qui augmente réellement l'argent disponible
        # du créateur (visible sur /monetization et /profile).
        cursor.execute(
            """
            UPDATE creator_wallets
            SET
                available_balance =
                    available_balance + %s,

                total_earned =
                    total_earned + %s,

                updated_at = CURRENT_TIMESTAMP

            WHERE user_id = %s
            """,
            (
                amount,
                amount,
                creator_id
            )
        )

        # Récupérer le nouveau solde
        # (nécessaire pour remplir balance_before/balance_after
        # ci-dessous, dans un souci de traçabilité complète)
        cursor.execute(
            """
            SELECT
                available_balance
            FROM creator_wallets
            WHERE user_id = %s
            """,
            (creator_id,)
        )

        wallet = cursor.fetchone()

        balance_after = float(
            wallet["available_balance"]
        ) if wallet else amount  # secours peu probable si le portefeuille n'existait pas encore

        balance_before = balance_after - amount  # déduit simplement : solde après moins le montant ajouté

        # Enregistrer la transaction
        # Historique détaillé (comme pour les retraits) : une ligne par
        # mouvement d'argent, pour un suivi complet du portefeuille.
        cursor.execute(
            """
            INSERT INTO wallet_transactions
            (
                user_id,
                type,
                amount,
                balance_before,
                balance_after,
                reference_type,
                reference_id,
                description
            )
            VALUES
            (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s
            )
            """,
            (
                creator_id,
                "earning",
                amount,
                balance_before,
                balance_after,
                "video",
                video_id,
                "Revenu généré par une vue qualifiée"
            )
        )

        connection.commit()  # valide les 3 écritures ci-dessus (earnings + wallet + transaction) ensemble

        return amount  # renvoie le montant crédité (utilisé par qualify_view() dans sa réponse JSON)

    except Exception as error:

        connection.rollback()

        print(
            "Erreur crédit créateur :",
            error
        )

        return 0

    finally:
        cursor.close()
        connection.close()


def qualify_view(view_id, watch_duration):
    """
    Qualifie une vue après 60 secondes et crédite le créateur
    UNE SEULE FOIS pour cette vue précise.

    Une vue = un utilisateur + une vidéo.
    Le view_id sert de référence unique du paiement.
    """

    # C'EST LA FONCTION LA PLUS IMPORTANTE DU PROJET : elle gère tout le
    # paiement d'une vue qualifiée, en garantissant qu'une même vue ne
    # peut JAMAIS être payée deux fois — même si le JavaScript envoie la
    # même demande plusieurs fois en même temps (double-clic, connexion
    # lente qui réessaie, deux onglets ouverts...). Voir l'étape 9 pour
    # le mécanisme technique qui rend ça possible (FOR UPDATE).

    connection = get_db_connection()

    if connection is None:
        return {
            "success": False,
            "credited": False,
            "message": "Connexion MySQL impossible"
        }

    cursor = connection.cursor(dictionary=True)

    try:

        # ==================================================
        # 1. DURÉE MINIMUM
        # ==================================================
        # Vérification de sécurité redondante avec celle déjà faite
        # dans update_watch_duration() : qualify_view() pouvant en
        # théorie être appelée d'ailleurs, elle ne doit JAMAIS faire
        # confiance aveuglément à la valeur reçue.

        QUALIFICATION_SECONDS = 60

        try:
            watch_duration = int(watch_duration)
        except (TypeError, ValueError):
            watch_duration = 0

        if watch_duration < QUALIFICATION_SECONDS:

            return {
                "success": False,
                "credited": False,
                "qualified": False,
                "message": "60 secondes minimum sont nécessaires.",
                "watch_duration": watch_duration
            }

        # ==================================================
        # 2. RÉCUPÉRER LA VUE
        # ==================================================

        cursor.execute(
            """
            SELECT
                id,
                user_id,
                video_id,
                watch_duration,
                completed
            FROM views
            WHERE id = %s
            LIMIT 1
            """,
            (view_id,)
        )

        view = cursor.fetchone()

        if not view:  # id de vue inexistant

            return {
                "success": False,
                "credited": False,
                "message": "Vue introuvable."
            }

        # ==================================================
        # 3. VÉRIFIER QUE LA VUE APPARTIENT À L'UTILISATEUR
        # ==================================================
        # Sécurité : empêche de qualifier/créditer la vue de
        # quelqu'un d'autre en devinant simplement son view_id.

        if view["user_id"] != session.get("user_id"):

            return {
                "success": False,
                "credited": False,
                "message": "Cette vue ne vous appartient pas."
            }

        # ==================================================
        # 4. VÉRIFIER SI CETTE VUE A DÉJÀ ÉTÉ PAYÉE
        # ==================================================
        # Première barrière anti-double-paiement (rapide, avant même
        # de verrouiller quoi que ce soit) : si un revenu existe déjà
        # pour ce view_id précis dans creator_earnings, on sait
        # immédiatement que cette vue a déjà généré de l'argent.

        cursor.execute(
            """
            SELECT
                id,
                amount
            FROM creator_earnings
            WHERE view_id = %s
            LIMIT 1
            """,
            (view_id,)
        )

        existing_earning = cursor.fetchone()

        if existing_earning:  # déjà payée : on le signale sans recréditer

            return {
                "success": True,
                "credited": False,
                "already_credited": True,
                "message": "Cette vue a déjà généré un revenu.",
                "view_id": view_id,
                "earning_id": existing_earning["id"],
                "amount": float(
                    existing_earning["amount"] or 0
                )
            }

        # ==================================================
        # 5. RÉCUPÉRER LA VIDÉO
        # ==================================================

        cursor.execute(
            """
            SELECT
                id,
                user_id
            FROM videos
            WHERE id = %s
            LIMIT 1
            """,
            (view["video_id"],)
        )

        video = cursor.fetchone()

        if not video:  # vidéo supprimée entre-temps

            return {
                "success": False,
                "credited": False,
                "message": "Vidéo introuvable."
            }

        # ==================================================
        # 6. IDENTIFIER LE CRÉATEUR
        # ==================================================

        creator_id = video["user_id"]  # celui qui va recevoir l'argent

        # ==================================================
        # 7. RÉCUPÉRER LE TARIF
        # ==================================================
        # (même logique que get_revenue_rate(), mais réécrite ici
        # directement plutôt que d'appeler la fonction, pour rester
        # dans LA MÊME transaction/connexion MySQL du début à la fin)

        cursor.execute(
            """
            SELECT
                setting_value
            FROM monetization_settings
            WHERE setting_name = 'revenue_per_1000_views'
            LIMIT 1
            """
        )

        setting = cursor.fetchone()

        if setting:

            try:
                rate = float(
                    setting["setting_value"]
                )
            except (TypeError, ValueError):
                rate = 500.0

        else:

            rate = 500.0

        # ==================================================
        # 8. CALCUL DU REVENU
        # ==================================================

        revenue = round(
            rate / 1000,
            4  # 4 décimales de précision (le montant par vue est petit, ex: 0.5000 XAF)
        )

        # ==================================================
        # 9. VERROUILLER LE PORTEFEUILLE
        # ==================================================
        # ⭐ LE MÉCANISME ANTI-DOUBLE-PAIEMENT ⭐
        #
        # "FOR UPDATE" est une instruction MySQL qui VERROUILLE la ligne
        # lue (ici, le portefeuille du créateur) jusqu'à la fin de la
        # transaction (jusqu'au connection.commit() de l'étape 16).
        #
        # Concrètement : si deux requêtes de qualification arrivent EN
        # MÊME TEMPS pour LA MÊME vue (ex: le JS envoie deux fois la
        # même requête réseau), la deuxième requête doit ATTENDRE que
        # la première ait fini tout son travail (créer le revenu,
        # créditer le portefeuille, valider) avant de pouvoir lire à
        # son tour la ligne "creator_wallets". Une fois débloquée,
        # elle relance sa propre vérification à l'étape 4
        # (creator_earnings WHERE view_id = ...) et trouve alors le
        # revenu déjà créé par la première requête → elle s'arrête
        # immédiatement sans créditer une seconde fois.
        #
        # Sans ce verrou, les deux requêtes pourraient lire le solde
        # AVANT que l'autre ne l'ait mis à jour, et calculer chacune
        # un nouveau solde à partir de l'ancien : le crédit de l'une
        # écraserait celui de l'autre au lieu de s'additionner (ou,
        # selon le cas, la vue serait payée deux fois).

        cursor.execute(
            """
            SELECT
                user_id,
                available_balance,
                total_earned
            FROM creator_wallets
            WHERE user_id = %s
            LIMIT 1
            FOR UPDATE
            """,
            (creator_id,)
        )

        wallet = cursor.fetchone()

        # ==================================================
        # 10. CRÉER LE PORTEFEUILLE SI ABSENT
        # ==================================================
        # Cas d'un créateur qui reçoit sa toute première vue qualifiée
        # avant d'avoir jamais visité /monetization (portefeuille pas
        # encore créé automatiquement par cette dernière).

        if wallet is None:

            cursor.execute(
                """
                INSERT INTO creator_wallets
                (
                    user_id,
                    available_balance,
                    pending_balance,
                    total_earned,
                    total_withdrawn,
                    currency
                )
                VALUES
                (
                    %s,
                    0,
                    0,
                    0,
                    0,
                    'XAF'
                )
                """,
                (creator_id,)
            )

            balance_before = 0.0

        else:

            balance_before = float(
                wallet["available_balance"] or 0
            )

        # ==================================================
        # 11. CRÉER LE REVENU
        # ==================================================
        # Cette ligne dans creator_earnings, avec son view_id, sert de
        # PREUVE que cette vue précise a été payée. C'est exactement
        # cette ligne que l'étape 4 (à un futur appel) va retrouver
        # pour éviter un second paiement.

        cursor.execute(
            """
            INSERT INTO creator_earnings
            (
                user_id,
                video_id,
                view_id,
                source,
                amount,
                currency,
                description,
                status,
                approved_at
            )
            VALUES
            (
                %s,
                %s,
                %s,
                'video_view',
                %s,
                'XAF',
                %s,
                'approved',
                CURRENT_TIMESTAMP
            )
            """,
            (
                creator_id,
                view["video_id"],
                view_id,
                revenue,
                "Revenu généré par une vue qualifiée de 60 secondes"
            )
        )

        earning_id = cursor.lastrowid

        # ==================================================
        # 12. CRÉDITER LE PORTEFEUILLE
        # ==================================================

        cursor.execute(
            """
            UPDATE creator_wallets
            SET
                available_balance =
                    available_balance + %s,

                total_earned =
                    total_earned + %s,

                updated_at =
                    CURRENT_TIMESTAMP

            WHERE user_id = %s
            """,
            (
                revenue,
                revenue,
                creator_id
            )
        )

        # ==================================================
        # 13. NOUVEAU SOLDE
        # ==================================================

        balance_after = (
            balance_before + revenue
        )

        # ==================================================
        # 14. HISTORIQUE DU PORTEFEUILLE
        # ==================================================

        cursor.execute(
            """
            INSERT INTO wallet_transactions
            (
                user_id,
                type,
                amount,
                balance_before,
                balance_after,
                reference_type,
                reference_id,
                description
            )
            VALUES
            (
                %s,
                'earning',
                %s,
                %s,
                %s,
                'video_view',
                %s,
                %s
            )
            """,
            (
                creator_id,
                revenue,
                balance_before,
                balance_after,
                view_id,
                "Revenu généré par une vue qualifiée"
            )
        )

        # ==================================================
        # 15. MARQUER LA VUE COMME COMPLÉTÉE
        # ==================================================
        # GREATEST(a, b) : fonction MySQL qui garde la plus grande des
        # deux valeurs (même logique de sécurité que max() en Python,
        # vue dans update_watch_duration : la durée ne doit jamais reculer).

        cursor.execute(
            """
            UPDATE views
            SET
                watch_duration = GREATEST(
                    watch_duration,
                    %s
                ),
                completed = 1
            WHERE id = %s
            """,
            (
                watch_duration,
                view_id
            )
        )

        # ==================================================
        # 16. VALIDER TOUT
        # ==================================================
        # Ce commit() valide EN UNE SEULE FOIS toutes les écritures
        # faites depuis le début de la fonction (création du revenu,
        # crédit du portefeuille, historique, mise à jour de la vue).
        # C'est SEULEMENT à cet instant que le verrou FOR UPDATE de
        # l'étape 9 est relâché, laissant repartir une éventuelle
        # requête concurrente qui attendait.

        connection.commit()

        # ==================================================
        # 17. RÉPONSE
        # ==================================================

        return {
            "success": True,
            "credited": True,
            "already_credited": False,
            "earning_id": earning_id,
            "creator_id": creator_id,
            "video_id": view["video_id"],
            "view_id": view_id,
            "watch_duration": watch_duration,
            "qualified": True,
            "revenue": revenue,
            "amount": revenue,
            "balance": balance_after,
            "message": (
                "Vue qualifiée. "
                "Le revenu a été ajouté au portefeuille."
            )
        }

    except Exception as error:  # n'importe quelle erreur SQL depuis le début de la fonction

        connection.rollback()  # annule TOUTES les écritures partielles (rien n'est enregistré à moitié)

        print(
            "===================================="
        )
        print(
            "ERREUR QUALIFICATION VUE :"
        )
        print(error)
        print(
            "===================================="
        )

        return {
            "success": False,
            "credited": False,
            "message": str(error)
        }

    finally:

        cursor.close()
        connection.close()

@app.route(
    "/api/views/<int:view_id>/qualify",
    methods=["POST"]
)
@login_required
def qualify_view_api(view_id):
    # Petite route "passerelle" : appelée directement en JS (en plus de
    # l'appel automatique déjà fait dans update_watch_duration()). Comme
    # qualify_view() vérifie toujours si la vue a déjà été payée, appeler
    # cette route en double ne pose aucun problème (idempotent).

    data = request.get_json(
        silent=True  # ne lève pas d'erreur si le JSON est absent/mal formé
    ) or {}

    watch_duration = int(
        data.get("watch_duration", 0)
    )

    result = qualify_view(  # toute la logique se trouve dans la fonction qualify_view() ci-dessus
        view_id,
        watch_duration
    )

    if result["success"]:

        return jsonify(result)

    return jsonify(result), 400  # 400 = requête invalide (ex: moins de 60 secondes)


# ==========================================================
# VÉRIFICATION DE L'ÉLIGIBILITÉ À LA MONÉTISATION
# ==========================================================

@app.route("/api/monetization/check", methods=["GET"])
@login_required
def check_monetization():
    # ⚠️ ATTENTION : cette route utilise un système D'ÉLIGIBILITÉ PARALLÈLE
    # et OBSOLÈTE (table "creator_monetization", seuils codés en dur :
    # 1000 abonnés / 10000 vues / 10 vidéos). Le VRAI système utilisé par
    # le reste de l'application est celui de monetization_dashboard()
    # (table "monetization_accounts", seuils configurables par l'admin
    # via /admin/settings). Cette route n'est appelée par AUCUNE page du
    # site actuellement — code laissé en place mais inutilisé, à
    # supprimer ou à corriger si on veut vraiment l'exploiter un jour.

    connection = get_db_connection()

    if connection is None:
        return jsonify({
            "success": False,
            "message": "Erreur de connexion MySQL"
        }), 500

    cursor = connection.cursor(dictionary=True)

    try:

        user_id = session["user_id"]

        # ==================================================
        # COMPTER LES ABONNÉS
        # ==================================================

        cursor.execute(
            """
            SELECT COUNT(*) AS total
            FROM followers
            WHERE following_id = %s
            """,
            (user_id,)
        )

        subscribers_count = cursor.fetchone()["total"]


        # ==================================================
        # COMPTER LES VIDÉOS
        # ==================================================

        cursor.execute(
            """
            SELECT COUNT(*) AS total
            FROM videos
            WHERE user_id = %s
            AND status = 'active'
            """,
            (user_id,)
        )

        videos_count = cursor.fetchone()["total"]


        # ==================================================
        # COMPTER LES VUES UNIQUES
        # ==================================================

        cursor.execute(
            """
            SELECT COUNT(DISTINCT v.user_id) AS total
            FROM views v
            INNER JOIN videos vid
                ON vid.id = v.video_id
            WHERE vid.user_id = %s
            """,
            (user_id,)
        )

        views_count = cursor.fetchone()["total"]


        # ==================================================
        # CONDITIONS
        # ==================================================
        # Seuils codés EN DUR ici (contrairement à monetization_dashboard
        # qui les lit depuis admin_settings) — encore un signe que cette
        # route appartient à l'ancien système, avant l'ajout du panel admin.

        subscribers_ok = subscribers_count >= 1000

        views_ok = views_count >= 10000

        videos_ok = videos_count >= 10


        eligible = (
            subscribers_ok
            and views_ok
            and videos_ok
        )


        # ==================================================
        # CRÉER OU METTRE À JOUR LE DOSSIER
        # ==================================================

        cursor.execute(
            """
            SELECT id
            FROM creator_monetization
            WHERE user_id = %s
            LIMIT 1
            """,
            (user_id,)
        )

        existing = cursor.fetchone()


        if existing:  # une ligne existe déjà : on la met à jour

            cursor.execute(
                """
                UPDATE creator_monetization
                SET
                    subscribers_count = %s,
                    views_count = %s,
                    videos_count = %s,
                    eligible = %s,
                    eligible_at =
                        CASE
                            WHEN %s = 1
                            AND eligible_at IS NULL
                            THEN NOW()
                            ELSE eligible_at
                        END
                WHERE user_id = %s
                """,
                (
                    subscribers_count,
                    views_count,
                    videos_count,
                    1 if eligible else 0,
                    1 if eligible else 0,
                    user_id
                )
            )

        else:  # première fois : on crée la ligne

            cursor.execute(
                """
                INSERT INTO creator_monetization
                (
                    user_id,
                    subscribers_count,
                    views_count,
                    videos_count,
                    eligible,
                    eligible_at
                )
                VALUES
                (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    CASE
                        WHEN %s = 1
                        THEN NOW()
                        ELSE NULL
                    END
                )
                """,
                (
                    user_id,
                    subscribers_count,
                    views_count,
                    videos_count,
                    1 if eligible else 0,
                    1 if eligible else 0
                )
            )


        connection.commit()


        # ==================================================
        # RÉPONSE
        # ==================================================

        return jsonify({

            "success": True,

            "eligible": eligible,

            "requirements": {  # détail condition par condition, pratique pour un affichage progressif côté front

                "subscribers": {
                    "current": subscribers_count,
                    "required": 1000,
                    "valid": subscribers_ok
                },

                "views": {
                    "current": views_count,
                    "required": 10000,
                    "valid": views_ok
                },

                "videos": {
                    "current": videos_count,
                    "required": 10,
                    "valid": videos_ok
                }

            },

            "message":
                "Vous êtes éligible à la monétisation."
                if eligible
                else
                "Vous ne remplissez pas encore toutes les conditions."

        })


    except Exception as error:

        connection.rollback()

        print(
            "ERREUR MONÉTISATION :",
            error
        )

        return jsonify({

            "success": False,

            "message": str(error)

        }), 500


    finally:

        cursor.close()
        connection.close()


# ==========================================================
# NOTIFICATIONS
# ==========================================================

@app.route("/notifications")
@login_required
def notifications():
    # Page listant toutes les notifications de l'utilisateur connecté
    # (like, commentaire, abonnement, monétisation...), les plus
    # récentes en premier, limitées aux 100 dernières.

    connection = get_db_connection()

    if connection is None:

        flash(
            "Impossible de se connecter à MySQL.",
            "error"
        )

        return redirect(
            url_for("feed")
        )

    cursor = connection.cursor(dictionary=True)

    user_id = session["user_id"]

    try:

        # ==================================================
        # RÉCUPÉRER LES NOTIFICATIONS
        # ==================================================

        cursor.execute(
            """
            SELECT
                id,
                user_id,
                type,
                message,
                reference_id,
                is_read,
                created_at
            FROM notifications
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT 100
            """,
            (user_id,)
        )

        notification_list = cursor.fetchall()

        # ==================================================
        # NOMBRE DE NON LUES
        # ==================================================
        # Ce chiffre alimente le badge rouge affiché sur la page (voir
        # aussi inject_notifications_count() plus bas, qui fait le même
        # calcul mais pour l'afficher DANS LA NAVBAR sur toutes les pages).

        cursor.execute(
            """
            SELECT COUNT(*) AS total
            FROM notifications
            WHERE user_id = %s
            AND is_read = 0
            """,
            (user_id,)
        )

        unread_count = cursor.fetchone()["total"]

        return render_template(
            "notifications.html",
            notifications=notification_list,
            unread_count=unread_count
        )

    except Exception as error:

        print(
            "Erreur notifications :",
            error
        )

        flash(
            "Impossible de charger les notifications.",
            "error"
        )

        return redirect(
            url_for("feed")
        )

    finally:

        cursor.close()
        connection.close()



# ==========================================================
# MARQUER UNE NOTIFICATION COMME LUE
# ==========================================================

@app.route(
    "/api/notifications/<int:notification_id>/read",
    methods=["POST"]
)
@login_required
def mark_notification_read(notification_id):
    # Appelée en JS au clic sur le bouton ✓ d'UNE notification précise.

    connection = get_db_connection()

    if connection is None:

        return jsonify({
            "success": False,
            "message": "Erreur MySQL"
        }), 500

    cursor = connection.cursor()  # pas de dictionary=True : simple UPDATE, aucune lecture de résultat

    try:

        # AND user_id = %s : sécurité, empêche de marquer comme lue
        # une notification appartenant à quelqu'un d'autre.
        cursor.execute(
            """
            UPDATE notifications
            SET is_read = 1
            WHERE id = %s
            AND user_id = %s
            """,
            (
                notification_id,
                session["user_id"]
            )
        )

        connection.commit()

        return jsonify({
            "success": True
        })

    except Exception as error:

        connection.rollback()

        print(
            "Erreur notification lue :",
            error
        )

        return jsonify({
            "success": False,
            "message": "Impossible de modifier la notification."
        }), 500

    finally:

        cursor.close()
        connection.close()



# ==========================================================
# NOMBRE DE NOTIFICATIONS NON LUES
# ==========================================================
# @app.context_processor est un décorateur SPÉCIAL de Flask : la
# fonction qu'il décore est exécutée AUTOMATIQUEMENT avant CHAQUE
# rendu de template (n'importe laquelle des pages du site, pas
# besoin de l'appeler depuis chaque route). C'est ainsi que
# "unread_notifications" est disponible dans base.html pour afficher
# le badge rouge à côté de "🔔 Notifications" dans la navbar, sur
# absolument toutes les pages, sans avoir à le répéter dans chaque route.

@app.context_processor
def inject_notifications_count():

    unread_notifications = 0  # valeur par défaut si personne n'est connecté

    if "user_id" in session:  # inutile de faire une requête SQL pour un visiteur non connecté

        connection = get_db_connection()

        if connection is not None:

            cursor = connection.cursor(dictionary=True)

            try:

                cursor.execute(
                    """
                    SELECT COUNT(*) AS total
                    FROM notifications
                    WHERE user_id = %s
                    AND is_read = 0
                    """,
                    (session["user_id"],)
                )

                result = cursor.fetchone()

                if result:
                    unread_notifications = result["total"]

            except Exception as error:  # on avale l'erreur : un badge manquant n'est pas grave, pas de flash/redirect

                print(
                    "Erreur compteur notifications :",
                    error
                )

            finally:

                cursor.close()
                connection.close()

    # Le dictionnaire renvoyé est fusionné automatiquement par Flask avec
    # les variables passées à render_template() : "unread_notifications"
    # devient donc utilisable dans N'IMPORTE QUEL template, y compris
    # ceux qui ne le passent pas eux-mêmes explicitement.
    return {
        "unread_notifications": unread_notifications
    }



# ==========================================================
# MARQUER TOUTES LES NOTIFICATIONS COMME LUES
# ==========================================================

@app.route(
    "/api/notifications/read-all",
    methods=["POST"]
)
@login_required
def mark_all_notifications_read():
    # Appelée en JS au clic sur "Tout marquer comme lu" (visible
    # uniquement s'il y a au moins une notification non lue).

    connection = get_db_connection()

    if connection is None:

        return jsonify({
            "success": False,
            "message": "Erreur MySQL"
        }), 500

    cursor = connection.cursor()

    try:

        # Pas de LIMIT ici : UPDATE modifie TOUTES les lignes qui
        # correspondent à la condition (mes notifications, non lues).
        cursor.execute(
            """
            UPDATE notifications
            SET is_read = 1
            WHERE user_id = %s
            AND is_read = 0
            """,
            (session["user_id"],)
        )

        connection.commit()

        return jsonify({
            "success": True
        })

    except Exception as error:

        connection.rollback()

        print(
            "Erreur lecture notifications :",
            error
        )

        return jsonify({
            "success": False,
            "message": str(error)
        }), 500

    finally:

        cursor.close()
        connection.close()


# ==========================================================
# ADMINISTRATION - CONNEXION SÉPARÉE
# ==========================================================

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    # Page de connexion RÉSERVÉE aux comptes administrateur, totalement
    # séparée de /login (la connexion classique des utilisateurs). Pas
    # de @login_required ici (par définition, personne n'est encore
    # connecté quand on arrive sur cette page).

    # Si déjà connecté en tant qu'admin, direct au tableau de bord

    if session.get("user_id") and session.get("is_admin"):
        return redirect(url_for("admin_dashboard"))

    if request.method == "POST":

        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email or not password:

            flash(
                "Veuillez remplir tous les champs.",
                "error"
            )

            return redirect(url_for("admin_login"))

        connection = get_db_connection()

        if connection is None:

            flash(
                "Impossible de se connecter à la base de données.",
                "error"
            )

            return redirect(url_for("admin_login"))

        cursor = connection.cursor(dictionary=True)

        try:

            cursor.execute(
                """
                SELECT
                    id,
                    username,
                    email,
                    password_hash,
                    is_active,
                    is_admin
                FROM users
                WHERE email = %s
                LIMIT 1
                """,
                (email,)
            )

            user = cursor.fetchone()

            if not user or not check_password_hash(
                user["password_hash"], password
            ):  # email inconnu OU mot de passe incorrect : même message pour les deux cas (sécurité)

                flash(
                    "Email ou mot de passe incorrect.",
                    "error"
                )

                return redirect(url_for("admin_login"))

            if not user["is_admin"]:  # bon mot de passe, mais ce n'est PAS un compte admin

                flash(
                    "Ce compte n'a pas les droits "
                    "administrateur.",
                    "error"
                )

                return redirect(url_for("admin_login"))  # renvoyé ici, PAS vers /login (séparation stricte des rôles)

            if not user["is_active"]:  # compte admin lui-même désactivé

                flash(
                    "Ce compte administrateur est désactivé.",
                    "error"
                )

                return redirect(url_for("admin_login"))

            session.clear()  # sécurité : repart d'une session totalement vide

            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["email"] = user["email"]
            session["is_admin"] = True  # ⭐ c'est CETTE ligne qui active tout l'accès admin (voir admin_required)

            flash(
                f"Bienvenue, {user['username']}.",
                "success"
            )

            return redirect(url_for("admin_dashboard"))

        except Exception as error:

            print("Erreur connexion admin :", error)

            flash("Une erreur est survenue.", "error")

            return redirect(url_for("admin_login"))

        finally:
            cursor.close()
            connection.close()

    # Requête GET : simple affichage du formulaire
    return render_template("admin_login.html")


# ==========================================================
# ADMINISTRATION - TABLEAU DE BORD
# ==========================================================

@app.route("/admin")
@admin_required  # protégé par le décorateur vu tout en haut du fichier : réservé aux comptes is_admin=1
def admin_dashboard():
    # Vue d'ensemble de la plateforme pour l'administrateur : quelques
    # statistiques globales calculées à la volée à chaque visite (pas
    # de mise en cache, simple mais suffisant pour ce projet).

    connection = get_db_connection()

    if connection is None:
        flash("Erreur de connexion à MySQL.", "error")
        return redirect(url_for("feed"))

    cursor = connection.cursor(dictionary=True)

    try:

        cursor.execute(
            "SELECT COUNT(*) AS total FROM users"
        )
        total_users = cursor.fetchone()["total"]

        cursor.execute(
            """
            SELECT COUNT(*) AS total
            FROM videos
            WHERE status = 'active'
            """
        )
        total_videos = cursor.fetchone()["total"]

        cursor.execute(
            """
            SELECT COUNT(*) AS total
            FROM monetization_accounts
            WHERE status = 'active'
            """
        )
        total_active = cursor.fetchone()["total"]  # nombre de créateurs dont la monétisation est activée

        cursor.execute(
            """
            SELECT COUNT(*) AS total
            FROM monetization_accounts
            WHERE status = 'eligible'
            """
        )
        total_eligible = cursor.fetchone()["total"]  # remplissent les conditions, en attente d'activation

        cursor.execute(
            """
            SELECT COUNT(*) AS total
            FROM monetization_accounts
            WHERE status = 'suspended'
            """
        )
        total_suspended = cursor.fetchone()["total"]  # comptes suspendus manuellement par un admin

        cursor.execute(
            """
            SELECT COALESCE(SUM(total_earned), 0) AS total
            FROM creator_wallets
            """
        )
        total_paid = cursor.fetchone()["total"]  # somme de TOUT l'argent gagné par TOUS les créateurs cumulés

        cursor.execute(
            """
            SELECT setting_value
            FROM monetization_settings
            WHERE setting_name = 'revenue_per_1000_views'
            LIMIT 1
            """
        )
        rate_row = cursor.fetchone()
        current_rate = rate_row["setting_value"] if rate_row else "500"  # affiché tel quel sur le dashboard

        return render_template(
            "admin_dashboard.html",
            total_users=total_users,
            total_videos=total_videos,
            total_active=total_active,
            total_eligible=total_eligible,
            total_suspended=total_suspended,
            total_paid=total_paid,
            current_rate=current_rate
        )

    except Exception as error:

        print("Erreur admin dashboard :", error)

        flash(
            "Impossible de charger le tableau de bord.",
            "error"
        )

        return redirect(url_for("feed"))

    finally:
        cursor.close()
        connection.close()


# ==========================================================
# ADMINISTRATION - PARAMÈTRES DE MONÉTISATION
# ==========================================================

@app.route("/admin/settings", methods=["GET", "POST"])
@admin_required
def admin_settings():
    # C'est ICI que l'administrateur modifie en direct les règles
    # économiques de toute la plateforme : les seuils d'éligibilité à
    # la monétisation ET le tarif payé par vue qualifiée. Toute
    # modification ici a un effet IMMÉDIAT sur monetization_dashboard(),
    # withdraw() et qualify_view() (via get_revenue_rate()), puisque
    # ces fonctions relisent ces tables à chaque appel plutôt que
    # d'utiliser une valeur figée dans le code.

    connection = get_db_connection()

    if connection is None:
        flash("Erreur de connexion à MySQL.", "error")
        return redirect(url_for("admin_dashboard"))

    cursor = connection.cursor(dictionary=True)

    # Seuils d'éligibilité + retrait minimum (table admin_settings)
    eligibility_keys = [
        "minimum_followers",
        "minimum_views",
        "minimum_videos",
        "minimum_account_age",
        "minimum_withdrawal"
    ]

    try:

        if request.method == "POST":

            # ----------------------------------------------
            # 1. Conditions d'éligibilité + retrait minimum
            # ----------------------------------------------
            # On boucle sur les 5 réglages et on met à jour chacun
            # séparément (5 UPDATE), après avoir vérifié que la valeur
            # envoyée est bien un nombre entier positif (.isdigit()).

            for key in eligibility_keys:

                value = request.form.get(key, "").strip()

                if not value.isdigit():  # texte vide, négatif, ou non numérique

                    flash(
                        f"Valeur invalide pour {key}.",
                        "error"
                    )

                    return redirect(url_for("admin_settings"))

                cursor.execute(
                    """
                    UPDATE admin_settings
                    SET setting_value = %s
                    WHERE setting_key = %s
                    """,
                    (value, key)
                )

            # ----------------------------------------------
            # 2. Montant généré par 1000 vues qualifiées
            #    (table monetization_settings)
            # ----------------------------------------------
            # Champ séparé, car il autorise les décimales (ex: 500.50),
            # contrairement aux seuils ci-dessus qui sont des entiers.

            revenue_rate = request.form.get(
                "revenue_per_1000_views", ""
            ).strip()

            try:
                revenue_rate_value = float(
                    revenue_rate.replace(",", ".")  # accepte la virgule française ET le point décimal
                )
            except ValueError:
                revenue_rate_value = None

            if revenue_rate_value is None or revenue_rate_value < 0:

                flash(
                    "Montant par 1000 vues invalide.",
                    "error"
                )

                return redirect(url_for("admin_settings"))

            cursor.execute(
                """
                UPDATE monetization_settings
                SET setting_value = %s
                WHERE setting_name = 'revenue_per_1000_views'
                """,
                (str(revenue_rate_value),)  # reconverti en texte : la colonne setting_value est un varchar
            )

            connection.commit()  # valide les 5 + 1 UPDATE d'un coup, une fois toutes les valeurs vérifiées

            flash(
                "Paramètres de monétisation mis à jour.",
                "success"
            )

            return redirect(url_for("admin_settings"))

        # ----------------------------------------------
        # Affichage (GET)
        # ----------------------------------------------
        # (Exécuté uniquement si la requête n'est PAS un POST, donc à
        # l'affichage initial de la page.)

        cursor.execute(
            """
            SELECT setting_key, setting_value, description
            FROM admin_settings
            WHERE setting_key IN (
                'minimum_followers',
                'minimum_views',
                'minimum_videos',
                'minimum_account_age',
                'minimum_withdrawal'
            )
            """
        )

        rows = cursor.fetchall()

        # Transforme la liste de lignes en dictionnaire {clé: ligne
        # complète}, pour un accès facile côté template Jinja
        # (ex: settings.minimum_followers.setting_value).
        settings = {row["setting_key"]: row for row in rows}

        cursor.execute(
            """
            SELECT setting_value
            FROM monetization_settings
            WHERE setting_name = 'revenue_per_1000_views'
            LIMIT 1
            """
        )

        rate_row = cursor.fetchone()

        revenue_per_1000_views = (
            rate_row["setting_value"] if rate_row else "500"
        )

        return render_template(
            "admin_settings.html",
            settings=settings,
            revenue_per_1000_views=revenue_per_1000_views
        )

    except Exception as error:

        connection.rollback()

        # traceback.print_exc() affiche la pile d'appel complète dans
        # la console PyCharm — beaucoup plus utile que print(error)
        # seul pour localiser PRÉCISÉMENT la ligne fautive pendant le
        # développement.
        import traceback
        traceback.print_exc()

        print("Erreur admin settings :", error)

        flash(
            f"Impossible de mettre à jour les paramètres. "
            f"Détail technique : {error}",  # message détaillé (pratique en dev, à simplifier en production)
            "error"
        )

        return redirect(url_for("admin_dashboard"))

    finally:
        cursor.close()
        connection.close()


# ==========================================================
# ADMINISTRATION - LISTE DES COMPTES
# ==========================================================

@app.route("/admin/accounts")
@admin_required
def admin_accounts():
    # Liste de TOUS les utilisateurs de la plateforme, avec leurs
    # statistiques essentielles, et une recherche facultative par
    # nom d'utilisateur ou email (paramètre ?q=... dans l'URL).

    connection = get_db_connection()

    if connection is None:
        flash("Erreur de connexion à MySQL.", "error")
        return redirect(url_for("admin_dashboard"))

    cursor = connection.cursor(dictionary=True)

    search_query = request.args.get("q", "").strip()

    try:

        # La requête est construite en Python sous forme de texte (pas
        # exécutée directement), pour pouvoir y ajouter dynamiquement
        # la clause WHERE ... SEULEMENT si une recherche a été tapée.
        sql = """
            SELECT
                users.id,
                users.username,
                users.email,
                users.is_active,
                users.created_at,

                COALESCE(
                    monetization_accounts.status,
                    'not_eligible'
                ) AS monetization_status,    -- 'not_eligible' si l'utilisateur n'a pas encore de ligne monetization_accounts

                (
                    SELECT COUNT(*)
                    FROM followers
                    WHERE followers.following_id = users.id
                ) AS followers_count,

                (
                    SELECT COUNT(*)
                    FROM videos
                    WHERE videos.user_id = users.id
                    AND videos.status = 'active'
                ) AS videos_count,

                COALESCE(
                    creator_wallets.available_balance,
                    0
                ) AS wallet_balance          -- 0 si le portefeuille n'a pas encore été créé

            FROM users

            LEFT JOIN monetization_accounts          -- LEFT (pas INNER) : on veut TOUS les utilisateurs,
                ON monetization_accounts.user_id = users.id   -- même ceux sans ligne monetization_accounts

            LEFT JOIN creator_wallets
                ON creator_wallets.user_id = users.id
        """

        params = []  # les paramètres seront ajoutés dynamiquement ci-dessous, si une recherche est en cours

        if search_query:  # une recherche a été tapée dans le champ

            sql += """
                WHERE users.username LIKE %s
                OR users.email LIKE %s
            """

            pattern = f"%{search_query}%"

            params.extend([pattern, pattern])  # 2 fois le même motif : une fois pour username, une fois pour email

        sql += " ORDER BY users.created_at DESC"  # les inscriptions les plus récentes en premier

        cursor.execute(sql, tuple(params))  # tuple(params) : liste vide si pas de recherche, sinon les 2 motifs

        accounts = cursor.fetchall()

        return render_template(
            "admin_accounts.html",
            accounts=accounts,
            search_query=search_query  # renvoyé pour préremplir le champ de recherche après une recherche
        )

    except Exception as error:

        print("Erreur admin accounts :", error)

        flash(
            "Impossible de charger les comptes.",
            "error"
        )

        return redirect(url_for("admin_dashboard"))

    finally:
        cursor.close()
        connection.close()


# ==========================================================
# ADMINISTRATION - DÉTAIL D'UN COMPTE
# ==========================================================

@app.route("/admin/accounts/<int:user_id>")
@admin_required
def admin_account_detail(user_id):
    # Fiche complète d'UN utilisateur précis, avec toutes les
    # informations nécessaires à l'admin pour décider s'il faut
    # activer/suspendre sa monétisation ou désactiver son compte.
    # <int:user_id> dans la route : Flask convertit automatiquement le
    # morceau d'URL en entier (ex: /admin/accounts/7 → user_id = 7).

    connection = get_db_connection()

    if connection is None:
        flash("Erreur de connexion à MySQL.", "error")
        return redirect(url_for("admin_accounts"))

    cursor = connection.cursor(dictionary=True)

    try:

        cursor.execute(
            """
            SELECT
                id,
                username,
                email,
                phone,
                bio,
                is_active,
                is_admin,
                created_at
            FROM users
            WHERE id = %s
            """,
            (user_id,)
        )

        user = cursor.fetchone()

        if not user:  # id inexistant (ex: URL modifiée à la main par l'admin)

            flash("Utilisateur introuvable.", "error")

            return redirect(url_for("admin_accounts"))

        # SELECT * : on récupère TOUTES les colonnes de monetization_accounts
        # (status, suspension_reason, dates...) plutôt que de toutes les
        # lister une par une, pratique pour une page de détail complète.
        cursor.execute(
            """
            SELECT *
            FROM monetization_accounts
            WHERE user_id = %s
            """,
            (user_id,)
        )

        monetization = cursor.fetchone()  # peut être None si l'utilisateur n'a encore jamais visité /monetization

        cursor.execute(
            """
            SELECT *
            FROM creator_wallets
            WHERE user_id = %s
            """,
            (user_id,)
        )

        wallet = cursor.fetchone()  # peut aussi être None, même raison

        cursor.execute(
            """
            SELECT COUNT(*) AS total
            FROM followers
            WHERE following_id = %s
            """,
            (user_id,)
        )

        followers_count = cursor.fetchone()["total"]

        cursor.execute(
            """
            SELECT COUNT(*) AS total
            FROM videos
            WHERE user_id = %s
            AND status = 'active'
            """,
            (user_id,)
        )

        videos_count = cursor.fetchone()["total"]

        cursor.execute(
            """
            SELECT COUNT(*) AS total
            FROM views
            INNER JOIN videos
                ON videos.id = views.video_id
            WHERE videos.user_id = %s
            """,
            (user_id,)
        )

        views_count = cursor.fetchone()["total"]

        # Les seuils configurés par l'admin (mêmes valeurs que celles
        # lues dans monetization_dashboard()), pour recalculer ici
        # l'éligibilité de CE créateur précis.
        cursor.execute(
            """
            SELECT setting_key, setting_value
            FROM admin_settings
            WHERE setting_key IN (
                'minimum_followers',
                'minimum_views',
                'minimum_videos',
                'minimum_account_age'
            )
            """
        )

        settings_rows = cursor.fetchall()

        settings = {
            row["setting_key"]: int(row["setting_value"])
            for row in settings_rows  # transforme la liste de lignes en dictionnaire {clé: valeur numérique}
        }

        cursor.execute(
            """
            SELECT DATEDIFF(
                CURDATE(),
                DATE(created_at)
            ) AS age
            FROM users
            WHERE id = %s
            """,
            (user_id,)
        )

        account_age = cursor.fetchone()["age"] or 0

        # Même calcul d'éligibilité que dans monetization_dashboard(),
        # mais ici uniquement pour AFFICHAGE (bandeau "remplit/ne
        # remplit pas les conditions") — cette page ne modifie JAMAIS
        # le statut automatiquement, seul admin_update_monetization()
        # (juste après) peut changer le statut, sur action explicite de l'admin.
        eligible = (
            followers_count >= settings.get(
                "minimum_followers", 5000
            )
            and views_count >= settings.get(
                "minimum_views", 100000
            )
            and videos_count >= settings.get(
                "minimum_videos", 10
            )
            and account_age >= settings.get(
                "minimum_account_age", 30
            )
        )

        cursor.execute(
            """
            SELECT *
            FROM creator_earnings
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT 10
            """,
            (user_id,)
        )

        recent_earnings = cursor.fetchall()

        return render_template(
            "admin_account_detail.html",
            account_user=user,  # nommé "account_user" (pas "user") pour ne pas entrer en conflit avec la session admin
            monetization=monetization,
            wallet=wallet,
            followers_count=followers_count,
            videos_count=videos_count,
            views_count=views_count,
            account_age=account_age,
            eligible=eligible,
            settings=settings,
            recent_earnings=recent_earnings
        )

    except Exception as error:

        print("Erreur détail compte admin :", error)

        flash(
            "Impossible de charger ce compte.",
            "error"
        )

        return redirect(url_for("admin_accounts"))

    finally:
        cursor.close()
        connection.close()


# ==========================================================
# ADMINISTRATION - MODIFIER LE STATUT DE MONÉTISATION
# ==========================================================

@app.route(
    "/admin/accounts/<int:user_id>/monetization",
    methods=["POST"]
)
@admin_required
def admin_update_monetization(user_id):
    # ⭐ Fonction clé du panel admin : permet de forcer MANUELLEMENT le
    # statut de monétisation d'un créateur, INDÉPENDAMMENT de ce que
    # calculerait automatiquement monetization_dashboard(). Rappel du
    # mécanisme (voir plus haut) : ce statut manuel n'est JAMAIS écrasé
    # par le recalcul automatique tant qu'il vaut "active" ou "suspended".

    new_status = request.form.get("status", "").strip()
    reason = request.form.get("suspension_reason", "").strip()  # motif, utilisé seulement si new_status="suspended"

    allowed_statuses = [
        "not_eligible",
        "eligible",
        "active",
        "suspended"
    ]

    if new_status not in allowed_statuses:  # sécurité : rejette toute valeur inattendue envoyée dans le formulaire

        flash("Statut invalide.", "error")

        return redirect(
            url_for("admin_account_detail", user_id=user_id)
        )

    connection = get_db_connection()

    if connection is None:
        flash("Erreur de connexion à MySQL.", "error")
        return redirect(
            url_for("admin_account_detail", user_id=user_id)
        )

    cursor = connection.cursor(dictionary=True)

    try:

        cursor.execute(
            """
            SELECT id
            FROM monetization_accounts
            WHERE user_id = %s
            """,
            (user_id,)
        )

        existing = cursor.fetchone()

        suspension_reason = (
            reason if new_status == "suspended" else None  # motif enregistré SEULEMENT en cas de suspension
        )

        if existing:  # le créateur a déjà une ligne monetization_accounts : on la met à jour

            cursor.execute(
                """
                UPDATE monetization_accounts
                SET
                    status = %s,
                    suspension_reason = %s,
                    suspended_at = CASE
                        WHEN %s = 'suspended'
                        THEN NOW()
                        ELSE suspended_at
                    END,
                    activated_at = CASE
                        WHEN %s = 'active'
                        AND activated_at IS NULL
                        THEN NOW()
                        ELSE activated_at
                    END
                WHERE user_id = %s
                """,
                (
                    new_status,
                    suspension_reason,
                    new_status,   # 1er CASE : date de suspension, seulement si on suspend maintenant
                    new_status,   # 2e CASE : date de PREMIÈRE activation, seulement si jamais activé avant
                    user_id
                )
            )

        else:  # aucune ligne encore : on la crée directement avec le statut choisi par l'admin

            cursor.execute(
                """
                INSERT INTO monetization_accounts
                (
                    user_id,
                    status,
                    suspension_reason,
                    activated_at
                )
                VALUES
                (
                    %s,
                    %s,
                    %s,
                    CASE WHEN %s = 'active'
                        THEN NOW()
                        ELSE NULL
                    END
                )
                """,
                (
                    user_id,
                    new_status,
                    suspension_reason,
                    new_status
                )
            )

            # Créer aussi le portefeuille s'il n'existe pas
            # (sinon un créateur activé manuellement par l'admin, sans
            # jamais être passé par /monetization, n'aurait aucun
            # endroit où recevoir ses futurs revenus)

            cursor.execute(
                """
                SELECT id
                FROM creator_wallets
                WHERE user_id = %s
                """,
                (user_id,)
            )

            if not cursor.fetchone():

                cursor.execute(
                    """
                    INSERT INTO creator_wallets (user_id)
                    VALUES (%s)
                    """,
                    (user_id,)  # les autres colonnes (balance, etc.) prennent leurs valeurs par défaut (0)
                )

        connection.commit()

        # Message de notification différent selon le nouveau statut,
        # pour que le créateur comprenne clairement ce qui a changé
        # pour lui (visible dans sa page /notifications).
        messages_by_status = {
            "active": (
                "🎉 Ta monétisation a été activée "
                "par l'administrateur !"
            ),
            "suspended": (
                "⚠️ Ta monétisation a été suspendue "
                "par l'administrateur."
            ),
            "eligible": (
                "✅ Tu es maintenant éligible "
                "à la monétisation."
            ),
            "not_eligible": (
                "Ton statut de monétisation "
                "a été mis à jour."
            )
        }

        create_notification(
            user_id,
            "monetization",
            messages_by_status.get(
                new_status,
                "Ton statut de monétisation a été mis à jour."  # filet de sécurité si new_status n'est pas dans le dict (ne devrait jamais arriver, déjà validé plus haut)
            ),
            None
        )

        flash(
            "Statut de monétisation mis à jour avec succès.",
            "success"
        )

    except Exception as error:

        connection.rollback()

        print("Erreur mise à jour monétisation admin :", error)

        flash(
            "Impossible de mettre à jour le statut.",
            "error"
        )

    finally:
        cursor.close()
        connection.close()

    return redirect(  # toujours renvoyé vers la fiche du compte, succès ou échec, pour voir le résultat
        url_for("admin_account_detail", user_id=user_id)
    )


# ==========================================================
# ADMINISTRATION - ACTIVER / DÉSACTIVER UN COMPTE
# ==========================================================

@app.route(
    "/admin/accounts/<int:user_id>/toggle-active",
    methods=["POST"]
)
@admin_required
def admin_toggle_active(user_id):
    # "Toggle" = bascule : si le compte est actif, on le désactive, et
    # inversement. Une seule route pour les deux actions (activer ET
    # désactiver), plutôt que deux routes séparées.

    if user_id == session["user_id"]:  # l'admin regarde SA PROPRE fiche (via admin_account_detail)

        flash(
            "Tu ne peux pas désactiver ton propre compte.",
            "error"
        )

        return redirect(
            url_for("admin_account_detail", user_id=user_id)
        )

    connection = get_db_connection()

    if connection is None:
        flash("Erreur de connexion à MySQL.", "error")
        return redirect(
            url_for("admin_account_detail", user_id=user_id)
        )

    cursor = connection.cursor(dictionary=True)

    try:

        cursor.execute(
            """
            SELECT is_active
            FROM users
            WHERE id = %s
            """,
            (user_id,)
        )

        row = cursor.fetchone()

        if not row:  # id inexistant

            flash("Utilisateur introuvable.", "error")

            return redirect(url_for("admin_accounts"))

        # Bascule simple : is_active vaut 1 (actif) ou 0 (désactivé) en
        # base de données. Si c'était 1 (actif → truthy en Python), on
        # passe à 0 ; sinon (0, désactivé) on passe à 1.
        new_value = 0 if row["is_active"] else 1

        cursor.execute(
            """
            UPDATE users
            SET is_active = %s
            WHERE id = %s
            """,
            (new_value, user_id)
        )

        connection.commit()

        # Rappel : un compte désactivé (is_active = 0) ne peut plus se
        # connecter du tout — voir la vérification dans login() tout
        # en haut du fichier ("if not user['is_active']").
        flash(
            "Compte réactivé."
            if new_value
            else "Compte désactivé.",
            "success"
        )

    except Exception as error:

        connection.rollback()

        print("Erreur toggle actif admin :", error)

        flash(
            "Impossible de modifier ce compte.",
            "error"
        )

    finally:
        cursor.close()
        connection.close()

    return redirect(
        url_for("admin_account_detail", user_id=user_id)
    )


# ==========================================================
# LANCEMENT
# ==========================================================
# Ce bloc ne s'exécute QUE si le fichier est lancé directement
# (ex: "python app.py" dans PyCharm), pas s'il est importé depuis un
# autre fichier Python — pratique standard de tous les projets Flask.

if __name__ == "__main__":

    app.run(
        debug=True,      # affiche les erreurs détaillées dans le navigateur + recharge auto à chaque modif de fichier
        host="127.0.0.1", # accessible uniquement depuis cet ordinateur (pas depuis le réseau local/internet)
        port=5000          # l'application sera servie sur http://127.0.0.1:5000
    )