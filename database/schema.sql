-- Create database if it does not exist
CREATE DATABASE IF NOT EXISTS emotion_db;
USE emotion_db;

-- Create Users table
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    role ENUM('Employee', 'Manager') NOT NULL
);

-- Create Emotion Logs table
CREATE TABLE IF NOT EXISTS emotion_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    employee_id INT NOT NULL,
    emotion VARCHAR(50),
    pulse_rate INT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    work_duration INT DEFAULT 0, -- Duration in seconds
    status ENUM('Active', 'Inactive') DEFAULT 'Active',
    FOREIGN KEY (employee_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Insert dummy manager for testing (password is 'password123' hashed with bcrypt)
-- You can use the register endpoint to add more later.
INSERT IGNORE INTO users (name, email, password, role) VALUES 
('Manager Admin', 'manager@example.com', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGGa.Wze', 'Manager');
