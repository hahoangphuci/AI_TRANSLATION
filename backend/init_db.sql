-- init_db.sql
-- SQL script to create database and tables for AI Translation app
-- Usage:
-- 1) In phpMyAdmin: open SQL tab, paste and run
-- 2) In MySQL CLI:
--      mysql -u root
--      source /path/to/init_db.sql

CREATE DATABASE IF NOT EXISTS `ai_translation`
  DEFAULT CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;
USE `ai_translation`;

-- users table
CREATE TABLE IF NOT EXISTS `user` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `google_id` VARCHAR(255) UNIQUE,
  `email` VARCHAR(255) NOT NULL,
  `name` VARCHAR(255),
  `avatar_url` VARCHAR(500),
  `plan` VARCHAR(50) DEFAULT 'free',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- translations table
CREATE TABLE IF NOT EXISTS `translation` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `user_id` INT NULL,
  `original_text` LONGTEXT,
  `translated_text` LONGTEXT,
  `source_lang` VARCHAR(10),
  `target_lang` VARCHAR(10),
  `file_path` VARCHAR(500),
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  INDEX (`user_id`),
  CONSTRAINT `fk_translation_user` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`)
    ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- payments table
CREATE TABLE IF NOT EXISTS `payment` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `user_id` INT NOT NULL,
  `amount` DOUBLE NOT NULL,
  `currency` VARCHAR(10) DEFAULT 'VND',
  `status` VARCHAR(50) DEFAULT 'pending',
  `sepay_transaction_id` VARCHAR(255),
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  INDEX (`user_id`),
  CONSTRAINT `fk_payment_user` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
