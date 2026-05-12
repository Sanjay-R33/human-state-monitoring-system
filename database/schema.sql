-- ==============================================================
-- Human State Monitoring System — Reference MySQL Schema
-- ==============================================================
-- This schema is provided as a reference for manual database setup.
-- SQLAlchemy (via models.py) auto-creates these tables at runtime.
-- Run this file only if you need to initialize the database manually:
--   mysql -u root -p < database/schema.sql
-- ==============================================================

-- Create database
CREATE DATABASE IF NOT EXISTS emotion_db;
USE emotion_db;

-- ----------------------------
-- Users table
-- ----------------------------
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    role ENUM('Employee', 'Manager') NOT NULL,
    INDEX idx_email (email)
);

-- ----------------------------
-- Emotion Logs table
-- ----------------------------
-- Stores real-time monitoring snapshots per employee.
CREATE TABLE IF NOT EXISTS emotion_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    employee_id INT NOT NULL,
    emotion VARCHAR(50) DEFAULT NULL,
    fatigue VARCHAR(50) DEFAULT 'Neutral',
    pulse_rate INT DEFAULT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    work_duration INT DEFAULT 0 COMMENT 'Duration in seconds',
    status ENUM('Active', 'Inactive') DEFAULT 'Active',
    FOREIGN KEY (employee_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_employee_status (employee_id, status)
);

-- ----------------------------
-- User Sessions table
-- ----------------------------
-- Tracks login/logout sessions for usage statistics.
CREATE TABLE IF NOT EXISTS user_sessions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    login_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    logout_time DATETIME DEFAULT NULL,
    session_duration INT DEFAULT 0 COMMENT 'Duration in seconds',
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_login (user_id, login_time)
);
