-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Hôte : 127.0.0.1
-- Généré le : ven. 21 août 2026 à 23:27
-- Version du serveur : 10.4.32-MariaDB
-- Version de PHP : 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Base de données : `streamlocal_db`
--

-- --------------------------------------------------------

--
-- Structure de la table `admin_settings`
--

CREATE TABLE `admin_settings` (
  `id` int(11) NOT NULL,
  `setting_key` varchar(100) NOT NULL,
  `setting_value` varchar(255) NOT NULL,
  `description` varchar(255) DEFAULT NULL,
  `updated_at` datetime NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Déchargement des données de la table `admin_settings`
--

INSERT INTO `admin_settings` (`id`, `setting_key`, `setting_value`, `description`, `updated_at`) VALUES
(1, 'minimum_followers', '5000', 'Nombre minimum d abonnes pour la monetisation', '2026-08-16 16:04:55'),
(2, 'minimum_views', '10', 'Nombre minimum de vues pour la monetisation', '2026-08-19 12:20:55'),
(3, 'minimum_videos', '5', 'Nombre minimum de videos publiees', '2026-08-21 20:02:03'),
(4, 'minimum_account_age', '15', 'Age minimum du compte en jours', '2026-08-19 11:54:03'),
(5, 'minimum_withdrawal', '1000', 'Montant minimum de retrait en XAF', '2026-08-19 12:20:13'),
(6, 'currency', 'XAF', 'Devise principale de StreamLocal', '2026-08-16 16:04:55'),
(7, 'payment_provider', 'codinghq', 'Passerelle de paiement utilisee', '2026-08-16 16:04:55'),
(8, 'payment_environment', 'sandbox', 'Environnement de paiement', '2026-08-16 16:04:55');

-- --------------------------------------------------------

--
-- Structure de la table `categories`
--

CREATE TABLE `categories` (
  `id` int(11) NOT NULL,
  `name` varchar(100) NOT NULL,
  `description` varchar(255) DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Structure de la table `comments`
--

CREATE TABLE `comments` (
  `id` bigint(20) NOT NULL,
  `user_id` int(11) NOT NULL,
  `video_id` bigint(20) NOT NULL,
  `parent_id` bigint(20) DEFAULT NULL,
  `content` text NOT NULL,
  `created_at` datetime NOT NULL DEFAULT current_timestamp(),
  `updated_at` datetime NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Déchargement des données de la table `comments`
--

INSERT INTO `comments` (`id`, `user_id`, `video_id`, `parent_id`, `content`, `created_at`, `updated_at`) VALUES
(17, 17, 8, NULL, 'hyper cool💥🤯', '2026-08-21 20:36:59', '2026-08-21 20:36:59'),
(18, 18, 8, NULL, 'Super jeux. j\'aime', '2026-08-21 20:48:43', '2026-08-21 20:48:43');

-- --------------------------------------------------------

--
-- Structure de la table `creator_earnings`
--

CREATE TABLE `creator_earnings` (
  `id` bigint(20) NOT NULL,
  `user_id` int(11) NOT NULL,
  `video_id` int(11) DEFAULT NULL,
  `source` varchar(50) NOT NULL,
  `amount` decimal(15,2) NOT NULL,
  `currency` varchar(10) NOT NULL DEFAULT 'XAF',
  `description` varchar(255) DEFAULT NULL,
  `status` varchar(30) NOT NULL DEFAULT 'pending',
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `approved_at` timestamp NULL DEFAULT NULL,
  `view_id` bigint(20) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Déchargement des données de la table `creator_earnings`
--

INSERT INTO `creator_earnings` (`id`, `user_id`, `video_id`, `source`, `amount`, `currency`, `description`, `status`, `created_at`, `approved_at`, `view_id`) VALUES
(1, 17, 8, 'video_view', 500.00, 'XAF', 'Revenu généré par une vue qualifiée de 60 secondes', 'approved', '2026-08-21 19:37:22', '2026-08-21 19:37:22', 57),
(2, 17, 8, 'video_view', 500.00, 'XAF', 'Revenu généré par une vue qualifiée de 60 secondes', 'approved', '2026-08-21 19:49:17', '2026-08-21 19:49:17', 58);

-- --------------------------------------------------------

--
-- Structure de la table `creator_wallets`
--

CREATE TABLE `creator_wallets` (
  `id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `available_balance` decimal(15,2) NOT NULL DEFAULT 0.00,
  `pending_balance` decimal(15,2) NOT NULL DEFAULT 0.00,
  `total_earned` decimal(15,2) NOT NULL DEFAULT 0.00,
  `total_withdrawn` decimal(15,2) NOT NULL DEFAULT 0.00,
  `currency` varchar(10) NOT NULL DEFAULT 'XAF',
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Déchargement des données de la table `creator_wallets`
--

INSERT INTO `creator_wallets` (`id`, `user_id`, `available_balance`, `pending_balance`, `total_earned`, `total_withdrawn`, `currency`, `created_at`, `updated_at`) VALUES
(2, 17, 1000.00, 0.00, 1000.00, 0.00, 'XAF', '2026-08-21 19:34:23', '2026-08-21 19:49:17'),
(3, 18, 0.00, 0.00, 0.00, 0.00, 'XAF', '2026-08-21 19:47:53', '2026-08-21 19:47:53');

-- --------------------------------------------------------

--
-- Structure de la table `followers`
--

CREATE TABLE `followers` (
  `id` bigint(20) NOT NULL,
  `follower_id` int(11) NOT NULL,
  `following_id` int(11) NOT NULL,
  `created_at` datetime NOT NULL DEFAULT current_timestamp()
) ;

--
-- Déchargement des données de la table `followers`
--

INSERT INTO `followers` (`id`, `follower_id`, `following_id`, `created_at`) VALUES
(38, 18, 17, '2026-08-21 20:48:14');

-- --------------------------------------------------------

--
-- Structure de la table `likes`
--

CREATE TABLE `likes` (
  `id` bigint(20) NOT NULL,
  `user_id` int(11) NOT NULL,
  `video_id` bigint(20) NOT NULL,
  `created_at` datetime NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Déchargement des données de la table `likes`
--

INSERT INTO `likes` (`id`, `user_id`, `video_id`, `created_at`) VALUES
(65, 17, 8, '2026-08-21 20:36:28'),
(66, 18, 8, '2026-08-21 20:48:08');

-- --------------------------------------------------------

--
-- Structure de la table `monetization`
--

CREATE TABLE `monetization` (
  `id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `status` enum('not_eligible','eligible','pending_review','active','suspended') NOT NULL DEFAULT 'not_eligible',
  `eligible` tinyint(1) NOT NULL DEFAULT 0,
  `eligible_at` datetime DEFAULT NULL,
  `activated_at` datetime DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Déchargement des données de la table `monetization`
--

INSERT INTO `monetization` (`id`, `user_id`, `status`, `eligible`, `eligible_at`, `activated_at`, `created_at`) VALUES
(8, 17, 'not_eligible', 0, NULL, NULL, '2026-08-21 20:33:57'),
(9, 18, 'not_eligible', 0, NULL, NULL, '2026-08-21 20:47:08');

-- --------------------------------------------------------

--
-- Structure de la table `monetization_accounts`
--

CREATE TABLE `monetization_accounts` (
  `id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `status` varchar(30) NOT NULL DEFAULT 'not_eligible',
  `total_views` bigint(20) NOT NULL DEFAULT 0,
  `total_followers` int(11) NOT NULL DEFAULT 0,
  `eligible_at` timestamp NULL DEFAULT NULL,
  `activated_at` timestamp NULL DEFAULT NULL,
  `suspended_at` timestamp NULL DEFAULT NULL,
  `suspension_reason` varchar(500) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Déchargement des données de la table `monetization_accounts`
--

INSERT INTO `monetization_accounts` (`id`, `user_id`, `status`, `total_views`, `total_followers`, `eligible_at`, `activated_at`, `suspended_at`, `suspension_reason`, `created_at`, `updated_at`) VALUES
(1, 14, 'not_eligible', 0, 0, NULL, NULL, NULL, NULL, '2026-08-21 19:07:14', '2026-08-21 19:07:14'),
(2, 17, 'not_eligible', 2, 1, NULL, NULL, NULL, NULL, '2026-08-21 19:34:23', '2026-08-21 19:51:03'),
(3, 18, 'not_eligible', 0, 0, NULL, NULL, NULL, NULL, '2026-08-21 19:47:53', '2026-08-21 19:47:53');

-- --------------------------------------------------------

--
-- Structure de la table `monetization_settings`
--

CREATE TABLE `monetization_settings` (
  `id` int(11) NOT NULL,
  `setting_name` varchar(100) NOT NULL,
  `setting_value` varchar(255) NOT NULL,
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Déchargement des données de la table `monetization_settings`
--

INSERT INTO `monetization_settings` (`id`, `setting_name`, `setting_value`, `updated_at`) VALUES
(1, 'revenue_per_1000_views', '500000.0', '2026-08-19 11:21:08');

-- --------------------------------------------------------

--
-- Structure de la table `notifications`
--

CREATE TABLE `notifications` (
  `id` bigint(20) NOT NULL,
  `user_id` int(11) NOT NULL,
  `type` varchar(50) NOT NULL,
  `message` varchar(255) NOT NULL,
  `reference_id` bigint(20) DEFAULT NULL,
  `is_read` tinyint(1) NOT NULL DEFAULT 0,
  `created_at` datetime NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Déchargement des données de la table `notifications`
--

INSERT INTO `notifications` (`id`, `user_id`, `type`, `message`, `reference_id`, `is_read`, `created_at`) VALUES
(103, 17, 'like', '@Annick M. a aimé ta vidéo « yuzu 1734 _ The Legend of Zelda_ Tears of the Kingdom ».', 8, 0, '2026-08-21 20:48:08'),
(104, 17, 'follow', '@Annick M. a commencé à te suivre.', 18, 0, '2026-08-21 20:48:14'),
(105, 17, 'comment', '@Annick M. a commenté ta vidéo « yuzu 1734 _ The Legend of Zelda_ Tears of the Kingdom ».', 8, 0, '2026-08-21 20:48:43');

-- --------------------------------------------------------

--
-- Structure de la table `shares`
--

CREATE TABLE `shares` (
  `id` bigint(20) NOT NULL,
  `user_id` int(11) DEFAULT NULL,
  `video_id` bigint(20) NOT NULL,
  `platform` varchar(50) DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Déchargement des données de la table `shares`
--

INSERT INTO `shares` (`id`, `user_id`, `video_id`, `platform`, `created_at`) VALUES
(13, 17, 8, NULL, '2026-08-21 20:36:35');

-- --------------------------------------------------------

--
-- Structure de la table `users`
--

CREATE TABLE `users` (
  `id` int(11) NOT NULL,
  `username` varchar(50) NOT NULL,
  `email` varchar(100) NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `phone` varchar(20) DEFAULT NULL,
  `profile_photo` varchar(500) DEFAULT NULL,
  `bio` varchar(500) DEFAULT NULL,
  `date_naissance` date DEFAULT NULL,
  `is_active` tinyint(1) NOT NULL DEFAULT 1,
  `is_admin` tinyint(1) NOT NULL DEFAULT 0,
  `created_at` datetime NOT NULL DEFAULT current_timestamp(),
  `updated_at` datetime NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Déchargement des données de la table `users`
--

INSERT INTO `users` (`id`, `username`, `email`, `password_hash`, `phone`, `profile_photo`, `bio`, `date_naissance`, `is_active`, `is_admin`, `created_at`, `updated_at`) VALUES
(12, 'admin', 'admin@gmail.com', 'scrypt:32768:8:1$AqKKeY1F8r3WrQDo$87c2ec33faf73223f289016465bdac4dd63113d129cf0d978aabade73f12899a64a8bb4b158fc83a90d3c1ad3a80383e42b769f77acc1c4a3e6ee9cdf517b1b2', NULL, NULL, NULL, NULL, 1, 1, '2026-08-19 11:39:05', '2026-08-19 11:39:05'),
(17, 'Ravi Jr', 'ravijunior321@gmail.com', 'scrypt:32768:8:1$wI2hX5ZMTMu12d1q$64c4e9969da990221ba9fd6ee34d218a38939ad7524e7c168817ef9a5d13dfc4291170aa79b612307b406bdb01a741f5f5f4bb55ad13f2b6850628fac0895a4f', '237696670085', NULL, NULL, NULL, 1, 0, '2026-08-21 20:33:57', '2026-08-21 20:33:57'),
(18, 'Annick M.', 'annick@gmail.com', 'scrypt:32768:8:1$Gtl0NR7F763tCo97$ff1e3a0e141c862590af434e5f34327ed56755bc12afe704a4c39ea7477f3d334123b0d6990b57f872f711c5d0f0dc4fe1cfc587e96392f62c6f704b00c7eeb9', '237699021435', NULL, NULL, NULL, 1, 0, '2026-08-21 20:47:08', '2026-08-21 20:47:08');

-- --------------------------------------------------------

--
-- Structure de la table `videos`
--

CREATE TABLE `videos` (
  `id` bigint(20) NOT NULL,
  `user_id` int(11) NOT NULL,
  `category_id` int(11) DEFAULT NULL,
  `title` varchar(150) DEFAULT NULL,
  `description` text DEFAULT NULL,
  `video_url` varchar(500) NOT NULL,
  `thumbnail_url` varchar(500) DEFAULT NULL,
  `duration` int(11) NOT NULL DEFAULT 0,
  `visibility` enum('public','private') NOT NULL DEFAULT 'public',
  `status` enum('active','pending','blocked','deleted') NOT NULL DEFAULT 'active',
  `created_at` datetime NOT NULL DEFAULT current_timestamp(),
  `updated_at` datetime NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Déchargement des données de la table `videos`
--

INSERT INTO `videos` (`id`, `user_id`, `category_id`, `title`, `description`, `video_url`, `thumbnail_url`, `duration`, `visibility`, `status`, `created_at`, `updated_at`) VALUES
(8, 17, NULL, 'yuzu 1734 _ The Legend of Zelda_ Tears of the Kingdom', '(64-bit) _ 1.0.0 _ NVIDIA 2026-04-26 13-26-57', '/uploads/videos/17_a38ae911637f41878f8a3c7d0a0806ff.mp4', NULL, 0, 'public', 'active', '2026-08-21 20:35:50', '2026-08-21 20:35:50');

-- --------------------------------------------------------

--
-- Structure de la table `views`
--

CREATE TABLE `views` (
  `id` bigint(20) NOT NULL,
  `user_id` int(11) DEFAULT NULL,
  `video_id` bigint(20) NOT NULL,
  `watch_duration` int(11) NOT NULL DEFAULT 0,
  `completed` tinyint(1) NOT NULL DEFAULT 0,
  `ip_address` varchar(45) DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Déchargement des données de la table `views`
--

INSERT INTO `views` (`id`, `user_id`, `video_id`, `watch_duration`, `completed`, `ip_address`, `created_at`) VALUES
(57, 17, 8, 60, 1, '127.0.0.1', '2026-08-21 20:35:50'),
(58, 18, 8, 60, 1, '127.0.0.1', '2026-08-21 20:48:00');

-- --------------------------------------------------------

--
-- Structure de la table `wallet_transactions`
--

CREATE TABLE `wallet_transactions` (
  `id` bigint(20) NOT NULL,
  `user_id` int(11) NOT NULL,
  `type` varchar(30) NOT NULL,
  `amount` decimal(15,2) NOT NULL,
  `balance_before` decimal(15,2) NOT NULL,
  `balance_after` decimal(15,2) NOT NULL,
  `reference_type` varchar(50) DEFAULT NULL,
  `reference_id` bigint(20) DEFAULT NULL,
  `description` varchar(255) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Déchargement des données de la table `wallet_transactions`
--

INSERT INTO `wallet_transactions` (`id`, `user_id`, `type`, `amount`, `balance_before`, `balance_after`, `reference_type`, `reference_id`, `description`, `created_at`) VALUES
(1, 17, 'earning', 500.00, 0.00, 500.00, 'video_view', 57, 'Revenu généré par une vue qualifiée', '2026-08-21 19:37:22'),
(2, 17, 'earning', 500.00, 500.00, 1000.00, 'video_view', 58, 'Revenu généré par une vue qualifiée', '2026-08-21 19:49:17');

-- --------------------------------------------------------

--
-- Structure de la table `withdrawal_requests`
--

CREATE TABLE `withdrawal_requests` (
  `id` bigint(20) NOT NULL,
  `user_id` int(11) NOT NULL,
  `amount` decimal(15,2) NOT NULL,
  `currency` varchar(10) NOT NULL DEFAULT 'XAF',
  `operator` varchar(10) NOT NULL,
  `phone` varchar(20) NOT NULL,
  `status` varchar(30) NOT NULL DEFAULT 'pending',
  `payment_reference` varchar(255) DEFAULT NULL,
  `deposit_id` varchar(255) DEFAULT NULL,
  `failure_reason` varchar(500) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `processed_at` timestamp NULL DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Index pour les tables déchargées
--

--
-- Index pour la table `admin_settings`
--
ALTER TABLE `admin_settings`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `setting_key` (`setting_key`);

--
-- Index pour la table `categories`
--
ALTER TABLE `categories`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `name` (`name`);

--
-- Index pour la table `comments`
--
ALTER TABLE `comments`
  ADD PRIMARY KEY (`id`),
  ADD KEY `fk_comment_user` (`user_id`),
  ADD KEY `idx_comment_video` (`video_id`),
  ADD KEY `idx_comment_parent` (`parent_id`);

--
-- Index pour la table `creator_earnings`
--
ALTER TABLE `creator_earnings`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `unique_view_earning` (`view_id`);

--
-- Index pour la table `creator_wallets`
--
ALTER TABLE `creator_wallets`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `user_id` (`user_id`);

--
-- Index pour la table `followers`
--
ALTER TABLE `followers`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `unique_follow` (`follower_id`,`following_id`),
  ADD KEY `fk_following_user` (`following_id`);

--
-- Index pour la table `likes`
--
ALTER TABLE `likes`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `unique_user_video_like` (`user_id`,`video_id`),
  ADD KEY `fk_like_video` (`video_id`);

--
-- Index pour la table `monetization`
--
ALTER TABLE `monetization`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `user_id` (`user_id`);

--
-- Index pour la table `monetization_accounts`
--
ALTER TABLE `monetization_accounts`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `user_id` (`user_id`);

--
-- Index pour la table `monetization_settings`
--
ALTER TABLE `monetization_settings`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `setting_name` (`setting_name`);

--
-- Index pour la table `notifications`
--
ALTER TABLE `notifications`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_notification_user_read` (`user_id`,`is_read`,`created_at`);

--
-- Index pour la table `shares`
--
ALTER TABLE `shares`
  ADD PRIMARY KEY (`id`),
  ADD KEY `fk_share_user` (`user_id`),
  ADD KEY `idx_share_video` (`video_id`);

--
-- Index pour la table `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `username` (`username`),
  ADD UNIQUE KEY `email` (`email`),
  ADD UNIQUE KEY `phone` (`phone`);

--
-- Index pour la table `videos`
--
ALTER TABLE `videos`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_video_user` (`user_id`),
  ADD KEY `idx_video_category` (`category_id`),
  ADD KEY `idx_video_feed` (`status`,`visibility`,`created_at`);

--
-- Index pour la table `views`
--
ALTER TABLE `views`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `unique_user_video` (`user_id`,`video_id`),
  ADD KEY `idx_view_video` (`video_id`),
  ADD KEY `idx_view_user` (`user_id`),
  ADD KEY `idx_view_created` (`created_at`);

--
-- Index pour la table `wallet_transactions`
--
ALTER TABLE `wallet_transactions`
  ADD PRIMARY KEY (`id`);

--
-- Index pour la table `withdrawal_requests`
--
ALTER TABLE `withdrawal_requests`
  ADD PRIMARY KEY (`id`);

--
-- AUTO_INCREMENT pour les tables déchargées
--

--
-- AUTO_INCREMENT pour la table `admin_settings`
--
ALTER TABLE `admin_settings`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=9;

--
-- AUTO_INCREMENT pour la table `categories`
--
ALTER TABLE `categories`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT pour la table `comments`
--
ALTER TABLE `comments`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=19;

--
-- AUTO_INCREMENT pour la table `creator_earnings`
--
ALTER TABLE `creator_earnings`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT pour la table `creator_wallets`
--
ALTER TABLE `creator_wallets`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT pour la table `followers`
--
ALTER TABLE `followers`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT pour la table `likes`
--
ALTER TABLE `likes`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=67;

--
-- AUTO_INCREMENT pour la table `monetization`
--
ALTER TABLE `monetization`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=10;

--
-- AUTO_INCREMENT pour la table `monetization_accounts`
--
ALTER TABLE `monetization_accounts`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT pour la table `monetization_settings`
--
ALTER TABLE `monetization_settings`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT pour la table `notifications`
--
ALTER TABLE `notifications`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=106;

--
-- AUTO_INCREMENT pour la table `shares`
--
ALTER TABLE `shares`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=14;

--
-- AUTO_INCREMENT pour la table `users`
--
ALTER TABLE `users`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=19;

--
-- AUTO_INCREMENT pour la table `videos`
--
ALTER TABLE `videos`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=9;

--
-- AUTO_INCREMENT pour la table `views`
--
ALTER TABLE `views`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=59;

--
-- AUTO_INCREMENT pour la table `wallet_transactions`
--
ALTER TABLE `wallet_transactions`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT pour la table `withdrawal_requests`
--
ALTER TABLE `withdrawal_requests`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=7;

--
-- Contraintes pour les tables déchargées
--

--
-- Contraintes pour la table `comments`
--
ALTER TABLE `comments`
  ADD CONSTRAINT `fk_comment_parent` FOREIGN KEY (`parent_id`) REFERENCES `comments` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `fk_comment_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `fk_comment_video` FOREIGN KEY (`video_id`) REFERENCES `videos` (`id`) ON DELETE CASCADE;

--
-- Contraintes pour la table `creator_wallets`
--
ALTER TABLE `creator_wallets`
  ADD CONSTRAINT `fk_creator_wallets_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE;

--
-- Contraintes pour la table `followers`
--
ALTER TABLE `followers`
  ADD CONSTRAINT `fk_follower_user` FOREIGN KEY (`follower_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `fk_following_user` FOREIGN KEY (`following_id`) REFERENCES `users` (`id`) ON DELETE CASCADE;

--
-- Contraintes pour la table `likes`
--
ALTER TABLE `likes`
  ADD CONSTRAINT `fk_like_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `fk_like_video` FOREIGN KEY (`video_id`) REFERENCES `videos` (`id`) ON DELETE CASCADE;

--
-- Contraintes pour la table `monetization`
--
ALTER TABLE `monetization`
  ADD CONSTRAINT `fk_monetization_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE;

--
-- Contraintes pour la table `notifications`
--
ALTER TABLE `notifications`
  ADD CONSTRAINT `fk_notification_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE;

--
-- Contraintes pour la table `shares`
--
ALTER TABLE `shares`
  ADD CONSTRAINT `fk_share_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `fk_share_video` FOREIGN KEY (`video_id`) REFERENCES `videos` (`id`) ON DELETE CASCADE;

--
-- Contraintes pour la table `videos`
--
ALTER TABLE `videos`
  ADD CONSTRAINT `fk_video_category` FOREIGN KEY (`category_id`) REFERENCES `categories` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `fk_video_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE;

--
-- Contraintes pour la table `views`
--
ALTER TABLE `views`
  ADD CONSTRAINT `fk_view_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `fk_view_video` FOREIGN KEY (`video_id`) REFERENCES `videos` (`id`) ON DELETE CASCADE;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
